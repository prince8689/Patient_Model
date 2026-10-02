import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from src.evaluation.oracle import reproduce_true_counterfactual
from src.simulator.scenarios import PlannedMeal
from src.simulator.whatif import WhatIfRequest, run_whatif
from src.utils.config import load_config


def main():
    config = load_config()
    data_dir = Path(config["paths"]["data_processed"])
    
    splits = pd.read_csv(data_dir / "splits.csv")
    val_patients = splits[splits["split"] == "val"]["patient_id"].values
    
    ehr_df = pd.read_csv(Path(config["paths"]["data_raw"]) / "patients.csv")
    sim_params_df = pd.read_csv(Path(config["paths"]["data_raw"]) / "patient_sim_params.csv")
    
    with open(config["whatif"]["prior_path"], "r") as f:
        prior_data = json.load(f)
        
    metrics = []
    
    for pid in val_patients:
        history_file = data_dir / "wearable" / f"{pid}.parquet"
        if not history_file.exists():
            history_file = Path(config["paths"]["data_raw"]) / "wearable.csv"
            history_df = pd.read_csv(history_file)
            history_df = history_df[history_df["patient_id"] == pid].copy()
        else:
            history_df = pd.read_parquet(history_file)
            
        prof = ehr_df[ehr_df["patient_id"] == pid].iloc[0].to_dict()
        
        features = prior_data["features"]
        X = np.array([prof.get(f, 0.0) for f in features])
        coef = np.array(prior_data["coef"])
        intercept = np.array(prior_data["intercept"])
        mean_est = X @ coef.T + intercept
        
        prior = {
            "mean": dict(zip(prior_data["param_names"], mean_est)),
            "cov": np.array(prior_data["cov"])
        }
        
        meal_idx = np.where(history_df["meal_carbs_g"].fillna(0) > 0)[0]
        valid_idx = [i for i in meal_idx if i > 7 * 288 and i < len(history_df) - 36]
        if not valid_idx:
            continue
            
        decision_idx = valid_idx[0] - 3
        decision_time_min = decision_idx * config["sampling_interval_minutes"]
        
        meal_carbs = history_df["meal_carbs_g"].iloc[valid_idx[0]]
        
        request = WhatIfRequest(
            planned_meals=[PlannedMeal(time_offset_min=15, carbs_g=meal_carbs)],
            baseline_activities=[],
            scenario_names=["walk_30min_moderate", "meal_earlier_30min", "reduce_carbs_30pct"]
        )
        
        history_cut = history_df.iloc[:decision_idx].copy()
        report = run_whatif(history_cut, prof, request, prior, config)
        
        oracle_effects = reproduce_true_counterfactual(
            pid, decision_time_min, request, sim_params_df, history_df, config
        )
        
        for scenario in report.scenarios:
            true_d_peak = oracle_effects[scenario.name]["delta_peak"]
            true_d_ta = oracle_effects[scenario.name]["delta_time_above_180"]
            
            peak_covered = (scenario.delta_peak_p10 <= true_d_peak <= scenario.delta_peak_p90)
            
            metrics.append({
                "patient_id": pid,
                "scenario": scenario.name,
                "true_d_peak": true_d_peak,
                "est_d_peak_median": scenario.delta_peak_median,
                "peak_err": abs(true_d_peak - scenario.delta_peak_median),
                "peak_covered": peak_covered
            })
            
    metrics_df = pd.DataFrame(metrics)
    summary = metrics_df.groupby("scenario")[["peak_err", "peak_covered"]].mean()
    print("VAL RESULTS:")
    print(summary)
    
    out_dict = summary.to_dict(orient="index")
    with open(config["paths"]["reports"] + "/metrics_whatif_val.json", "w") as f:
        json.dump(out_dict, f, indent=2)
    
if __name__ == "__main__":
    main()
