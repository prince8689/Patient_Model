import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, recall_score

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config

def evaluate_subgroup(df, group_name):
    n_rows = len(df)
    n_pats = df["patient_id"].nunique()
    if n_pats < 2 or len(df["spike_next_2h"].unique()) < 2:
        return {"group": group_name, "n_rows": n_rows, "n_patients": n_pats, "status": "insufficient data"}
        
    y = df["spike_next_2h"]
    p = df["prob_calib"]
    prev = y.mean()
    auc = roc_auc_score(y, p)
    rec = recall_score(y, df["pred"])
    
    return {
        "group": group_name,
        "n_rows": n_rows,
        "n_patients": n_pats,
        "prevalence": prev,
        "roc_auc": auc,
        "recall_t_med": rec,
        "status": "ok"
    }

def main():
    config = load_config()
    reports_path = Path(config["paths"]["reports"])
    fig_dir = reports_path / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    # We must join patients.csv to get static traits (age, sex, etc.)
    df_test = pd.read_parquet(reports_path / "test_predictions_day7.parquet")
    df_feat = pd.read_parquet(Path(config["paths"]["data_processed"]) / "features.parquet")
    
    # Merge required columns from features
    static_cols = ["patient_id", "ehr_hba1c", "ehr_sex_male", "ehr_age", "ehr_on_insulin", "time_hour_sin", "miss_glucose_frac_60m", "meal_min_since_last"]
    # only keep static cols that exist, plus the index
    df_test = df_test.merge(df_feat[static_cols].drop_duplicates("patient_id"), on="patient_id", how="left", suffixes=("", "_dup"))
    
    with open(Path(config["paths"]["models"]) / "thresholds_v1.json", "r") as f:
        t_med = json.load(f)["thresholds"]["t_medium"]
        
    df_test["pred"] = (df_test["prob_calib"] >= t_med).astype(int)
    
    results = []
    
    # Subgroup: Sex
    if "ehr_sex_male" in df_test.columns:
        results.append(evaluate_subgroup(df_test[df_test["ehr_sex_male"] == 1], "Sex: Male"))
        results.append(evaluate_subgroup(df_test[df_test["ehr_sex_male"] == 0], "Sex: Female"))
        
    # Subgroup: Age
    if "ehr_age" in df_test.columns:
        results.append(evaluate_subgroup(df_test[df_test["ehr_age"] >= 55], "Age: >= 55"))
        results.append(evaluate_subgroup(df_test[df_test["ehr_age"] < 55], "Age: < 55"))
        
    # Print Subgroup results
    for r in results:
        if r["status"] == "ok":
            print(f"{r['group']}: AUC={r['roc_auc']:.3f}, Recall={r['recall_t_med']:.3f} (n={r['n_patients']})")
        else:
            print(f"{r['group']}: {r['status']}")
            
    # Error patterns
    fn_df = df_test[(df_test["spike_next_2h"] == 1) & (df_test["pred"] == 0)]
    fp_df = df_test[(df_test["spike_next_2h"] == 0) & (df_test["pred"] == 1)]
    
    print(f"\nTotal FN: {len(fn_df)}, Total FP: {len(fp_df)}")
    
    # Plot missing data effect
    if "miss_glucose_frac_60m" in df_test.columns:
        plt.figure(figsize=(6,4))
        miss_perf = [
            evaluate_subgroup(df_test[df_test["miss_glucose_frac_60m"] == 0], "No Missing Data"),
            evaluate_subgroup(df_test[df_test["miss_glucose_frac_60m"] > 0], "Some Missing Data")
        ]
        
        x = [m["group"] for m in miss_perf if m["status"] == "ok"]
        y = [m["roc_auc"] for m in miss_perf if m["status"] == "ok"]
        plt.bar(x, y, color="orange")
        plt.title("Effect of Sensor Missingness on ROC-AUC")
        plt.ylim(0.5, 1.0)
        plt.savefig(fig_dir / "day7_missing_data_effect.png", dpi=150)
        plt.close()

if __name__ == "__main__":
    main()
