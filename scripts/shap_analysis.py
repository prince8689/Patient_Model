import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

sys.path.append(str(Path(__file__).parent.parent))
from src.models.explain import explain_row, group_shap
from src.utils.config import load_config


def main():
    config = load_config()
    feat_path = Path(config["paths"]["data_processed"]) / "features.parquet"
    models_path = Path(config["paths"]["models"])
    reports_path = Path(config["paths"]["reports"])
    fig_dir = reports_path / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading test data...")
    df = pd.read_parquet(feat_path)
    test_mask = (df["split"].eq("test")) & (df["valid"] == 1)
    df_test = df[test_mask].copy()
    
    with open(models_path / "xgb_v1_meta.json", "r") as f:
        meta = json.load(f)
    features = meta["features"]
    
    model = joblib.load(models_path / "xgb_v1.joblib")
    
    X_test = df_test[features]
    
    print("Initializing SHAP Explainer...")
    # Stratified sample
    np.random.seed(42)
    sample_size = min(config["evaluation"]["shap_sample_size"], len(X_test))
    # simple random sample for now
    X_sample = X_test.sample(n=sample_size, random_state=42)
    
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    
    # Check additivity
    margin = model.predict(X_sample, output_margin=True)
    reconstructed = shap_values.sum(axis=1) + explainer.expected_value
    max_err = np.max(np.abs(margin - reconstructed))
    print(f"SHAP max reconstruction error: {max_err:.2e}")
    if max_err > 1e-4:
        print("WARNING: SHAP additivity violated!")
        
    # Global Importance
    abs_shap = np.abs(shap_values).mean(axis=0)
    imp_df = pd.DataFrame({"feature": features, "importance": abs_shap})
    imp_df = imp_df.sort_values("importance", ascending=False)
    imp_df.to_csv(reports_path / "shap_importance_day7.csv", index=False)
    
    # 1. Beeswarm
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_sample, max_display=20, show=False)
    plt.savefig(fig_dir / "day7_shap_beeswarm_top20.png", dpi=150, bbox_inches="tight")
    plt.close()
    
    # 2. Bar plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_sample, plot_type="bar", max_display=20, show=False)
    plt.savefig(fig_dir / "day7_shap_bar_top20.png", dpi=150, bbox_inches="tight")
    plt.close()
    
    # 3. Group importance
    grp_shap = group_shap(shap_values, features)
    plt.figure(figsize=(8, 6))
    pd.Series(grp_shap).sort_values().plot(kind="barh", color="teal")
    plt.title("SHAP Importance by Feature Group")
    plt.xlabel("Mean |SHAP|")
    plt.savefig(fig_dir / "day7_shap_group_importance.png", dpi=150, bbox_inches="tight")
    plt.close()
    
    # 4. Dependence plots (Top 4)
    top_4 = imp_df["feature"].head(4).tolist()
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    for i, f in enumerate(top_4):
        plt.sca(axes[i])
        shap.dependence_plot(f, shap_values, X_sample, ax=axes[i], show=False)
    plt.tight_layout()
    plt.savefig(fig_dir / "day7_shap_dependence_top4.png", dpi=150, bbox_inches="tight")
    plt.close()
    
    # 5. Local examples
    df_test["prob_raw"] = model.predict_proba(X_test)[:, 1]
    y_test = df_test["spike_next_2h"]
    
    # Pick TP, FN, TN
    with open(models_path / "thresholds_v1.json", "r") as f:
        t_med = json.load(f)["thresholds"]["t_medium"]
        
    df_test["pred"] = (df_test["prob_raw"] >= t_med).astype(int)
    
    tp_idx = df_test[(y_test == 1) & (df_test["pred"] == 1)].index[0]
    fn_idx = df_test[(y_test == 1) & (df_test["pred"] == 0)].index[0]
    tn_idx = df_test[(y_test == 0) & (df_test["pred"] == 0)].index[0]
    
    fig, axes = plt.subplots(3, 1, figsize=(10, 15))
    
    for i, (idx, name) in enumerate([(tp_idx, "True Positive"), (fn_idx, "False Negative"), (tn_idx, "True Negative")]):
        row = df_test.loc[[idx]]
        exp = explain_row(explainer, row, features, top_k=5)
        
        y_pos = np.arange(len(exp))
        vals = [e["shap_value"] for e in exp]
        labels = [f"{e['feature']} ({e['feature_value']:.1f})" for e in exp]
        colors = ["red" if v > 0 else "blue" for v in vals]
        
        axes[i].barh(y_pos, vals, color=colors)
        axes[i].set_yticks(y_pos)
        axes[i].set_yticklabels(labels)
        axes[i].invert_yaxis()
        
        title = f"{name} Example (Row {idx})\n"
        for j, e in enumerate(exp[:3]):
            title += f"{j+1}. {e['human_readable']}\n"
        axes[i].set_title(title, fontsize=10)
        
    plt.tight_layout()
    plt.savefig(fig_dir / "day7_shap_local_examples.png", dpi=150, bbox_inches="tight")
    plt.close()

if __name__ == "__main__":
    main()
