import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_auc_score

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config
from src.features.registry import FEATURE_REGISTRY

def main():
    config = load_config()
    feat_path = Path(config["features"]["features_path"])
    fig_dir = Path(config["paths"]["reports"]) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading features...")
    df = pd.read_parquet(feat_path)
    train_df = df[(df["split"] == "train") & (df["valid"] == 1)].copy()
    print(f"Train rows: {len(train_df)}")
    
    features = [f["name"] for f in FEATURE_REGISTRY]
    groups = {f["name"]: f["group"] for f in FEATURE_REGISTRY}
    
    missing = train_df[features].isna().mean() * 100
    high_missing = missing[missing > 20].to_dict()
    
    stds = train_df[features].std()
    constants = stds[stds < 1e-6].index.tolist()
    
    print("Computing correlations...")
    corr = train_df[features].corr().abs()
    high_corr_pairs = []
    for i in range(len(corr.columns)):
        for j in range(i+1, len(corr.columns)):
            if corr.iloc[i, j] > 0.95:
                high_corr_pairs.append((corr.columns[i], corr.columns[j], float(corr.iloc[i, j])))
                
    print("Computing AUCs...")
    y = train_df["spike_next_2h"]
    aucs = {}
    for f in features:
        if f in constants:
            continue
        mask = train_df[f].notna()
        if mask.sum() < 100:
            continue
        
        try:
            score = roc_auc_score(y[mask], train_df.loc[mask, f])
            aucs[f] = score
        except ValueError:
            pass
            
    auc_records = []
    for f, score in aucs.items():
        if score < 0.5:
            auc_records.append({"feature": f, "group": groups[f], "auc": 1 - score, "direction": "-"})
        else:
            auc_records.append({"feature": f, "group": groups[f], "auc": score, "direction": "+"})
            
    auc_df = pd.DataFrame(auc_records).sort_values("auc", ascending=False)
    
    top_15 = auc_df.head(15).to_dict("records")
    bottom_5 = auc_df.tail(5).to_dict("records")
    
    report = {
        "n_features": len(features),
        "high_missing_features": high_missing,
        "constant_features": constants,
        "highly_correlated_pairs": high_corr_pairs,
        "top_15_aucs": top_15,
        "bottom_5_aucs": bottom_5
    }
    
    with open("docs/feature_quality.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(json.dumps(report, indent=2))
    
    missing_df = pd.DataFrame({"feature": missing.index, "missing_pct": missing.values})
    missing_df["group"] = missing_df["feature"].map(groups)
    grp_miss = missing_df.groupby("group")["missing_pct"].mean()
    plt.figure(figsize=(8, 5))
    grp_miss.plot(kind="bar", color="skyblue")
    plt.title("Average Missing Percentage by Feature Group")
    plt.ylabel("Missing %")
    plt.tight_layout()
    plt.savefig(fig_dir / "day5_feature_missingness.png", dpi=150)
    plt.close()
    
    top_df = auc_df.head(15)
    plt.figure(figsize=(10, 6))
    plt.barh(top_df["feature"][::-1], top_df["auc"][::-1], color="salmon")
    plt.title("Top 15 Features by ROC-AUC")
    plt.xlabel("ROC-AUC")
    plt.xlim(0.5, 1.0)
    plt.tight_layout()
    plt.savefig(fig_dir / "day5_top_feature_auc.png", dpi=150)
    plt.close()
    
    top_30_feats = auc_df.head(30)["feature"].tolist()
    top_corr = train_df[top_30_feats].corr()
    plt.figure(figsize=(12, 10))
    sns.heatmap(top_corr, cmap="coolwarm", center=0, vmin=-1, vmax=1)
    plt.title("Correlation Heatmap (Top 30 Features)")
    plt.tight_layout()
    plt.savefig(fig_dir / "day5_feature_correlation_heatmap.png", dpi=150)
    plt.close()
    
    key_feats = ["glu_delta_30m", "meal_cob_estimate", "meal_min_since_last", "glu_current", "act_steps_last_60m", "hr_vs_personal_baseline"]
    key_feats = [f for f in key_feats if f in features]
    
    plt.figure(figsize=(15, 10))
    for i, f in enumerate(key_feats):
        plt.subplot(2, 3, i+1)
        sns.violinplot(data=train_df, x="spike_next_2h", y=f, palette="Set2")
        plt.title(f)
    plt.tight_layout()
    plt.savefig(fig_dir / "day5_feature_distributions_by_label.png", dpi=150)
    plt.close()

if __name__ == "__main__":
    main()
