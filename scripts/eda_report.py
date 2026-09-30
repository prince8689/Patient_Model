import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config

def main():
    config = load_config()
    raw_dir = Path(config["paths"]["data_raw"])
    proc_dir = Path(config["paths"]["data_processed"])
    fig_dir = Path(config["paths"]["reports"]) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    wearable = pd.read_csv(raw_dir / "wearable.csv", parse_dates=["timestamp"])
    labels = pd.read_csv(proc_dir / "labels.csv", parse_dates=["timestamp"])
    splits = pd.read_csv(proc_dir / "splits.csv")
    sim_params = pd.read_csv(raw_dir / "patient_sim_params.csv")
    
    merged = labels.merge(wearable, on=["patient_id", "timestamp"]).merge(splits, on="patient_id").merge(sim_params[["patient_id", "archetype"]], on="patient_id")
    valid_df = merged[merged["valid"] == 1].copy()
    
    # 1. day4_label_rate_by_hour.png
    valid_df["hour"] = valid_df["timestamp"].dt.hour
    hourly_rate = valid_df.groupby("hour")["spike_next_2h"].mean()
    plt.figure(figsize=(8, 5))
    hourly_rate.plot(kind="bar", color="skyblue")
    plt.title("Spike Rate by Hour of Day")
    plt.ylabel("Spike Probability")
    plt.xlabel("Hour of Day")
    plt.tight_layout()
    plt.savefig(fig_dir / "day4_label_rate_by_hour.png", dpi=150)
    plt.close()
    
    # 2. day4_label_rate_per_patient.png
    pat_rates = valid_df.groupby(["patient_id", "split"])["spike_next_2h"].mean().reset_index()
    pat_rates = pat_rates.sort_values("spike_next_2h")
    colors = {"train": "blue", "val": "orange", "test": "green"}
    
    plt.figure(figsize=(12, 6))
    plt.bar(pat_rates["patient_id"], pat_rates["spike_next_2h"], color=pat_rates["split"].map(colors))
    plt.title("Spike Rate per Patient (colored by split)")
    plt.xticks(rotation=90)
    plt.ylabel("Spike Probability")
    handles = [plt.Rectangle((0,0),1,1, color=colors[s]) for s in colors]
    plt.legend(handles, colors.keys())
    plt.tight_layout()
    plt.savefig(fig_dir / "day4_label_rate_per_patient.png", dpi=150)
    plt.close()
    
    # 3. day4_glucose_distribution_by_split.png
    plt.figure(figsize=(8, 5))
    for s in ["train", "val", "test"]:
        merged[merged["split"] == s]["glucose_mgdl"].plot(kind="kde", label=s)
    plt.title("Glucose Distribution by Split")
    plt.xlabel("Glucose (mg/dL)")
    plt.xlim(40, 400)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "day4_glucose_distribution_by_split.png", dpi=150)
    plt.close()
    
    # 4. day4_missingness_patterns.png
    merged["is_missing"] = merged["glucose_mgdl"].isna()
    miss_by_hour = merged.groupby(merged["timestamp"].dt.hour)["is_missing"].mean()
    
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    miss_by_hour.plot(kind="bar", color="gray")
    plt.title("Missing Glucose by Hour")
    plt.ylabel("Missing Rate")
    plt.xlabel("Hour of Day")
    
    plt.subplot(1, 2, 2)
    miss_mask = merged["is_missing"]
    gap_groups = (miss_mask != miss_mask.shift()).cumsum()
    gap_lens = miss_mask.groupby(gap_groups).sum()
    gap_lens = gap_lens[gap_lens > 0] * config["sampling_interval_minutes"]
    plt.hist(gap_lens, bins=20, color="purple", alpha=0.7)
    plt.title("Distribution of Gap Lengths (minutes)")
    plt.xlabel("Gap Length (min)")
    plt.tight_layout()
    plt.savefig(fig_dir / "day4_missingness_patterns.png", dpi=150)
    plt.close()
    
    # 5. day4_spike_examples.png
    plt.figure(figsize=(15, 10))
    pos_samples = valid_df[valid_df["spike_next_2h"] == 1].sample(3, random_state=42)
    neg_samples = valid_df[valid_df["spike_next_2h"] == 0].sample(3, random_state=42)
    
    samples = pd.concat([pos_samples, neg_samples])
    for i, (idx, row) in enumerate(samples.iterrows()):
        pid = row["patient_id"]
        ts = row["timestamp"]
        mask = (merged["patient_id"] == pid) & (merged["timestamp"] >= ts - pd.Timedelta(hours=2)) & (merged["timestamp"] <= ts + pd.Timedelta(hours=2))
        window = merged[mask]
        
        plt.subplot(2, 3, i+1)
        plt.plot(window["timestamp"], window["glucose_mgdl"], marker='.', linestyle='-')
        plt.axvline(ts, color='red', linestyle='--')
        plt.axhline(row["glucose_mgdl"] + 50, color='orange', linestyle=':', label='+50 Threshold')
        plt.title(f"{'Spike' if row['spike_next_2h']==1 else 'No Spike'} - {pid}")
        plt.xticks(rotation=45)
        if i == 0: plt.legend()
        
    plt.tight_layout()
    plt.savefig(fig_dir / "day4_spike_examples.png", dpi=150)
    plt.close()
    
    # 6. day4_meal_vs_spike.png
    meal_times = merged[merged["meal_carbs_g"] > 0][["patient_id", "timestamp"]].copy()
    meal_times["last_meal"] = meal_times["timestamp"]
    merged_sorted = merged.sort_values("timestamp")
    meal_sorted = meal_times.sort_values("timestamp")
    merged_meal = pd.merge_asof(merged_sorted, meal_sorted, by="patient_id", on="timestamp", direction="backward")
    merged_meal["mins_since_meal"] = (merged_meal["timestamp"] - merged_meal["last_meal"]).dt.total_seconds() / 60.0
    
    valid_df2 = merged_meal[merged_meal["valid"] == 1].copy()
    valid_df2["meal_bin"] = pd.cut(valid_df2["mins_since_meal"], bins=np.arange(0, 390, 30))
    meal_spike = valid_df2.groupby("meal_bin", observed=False)["spike_next_2h"].mean()
    
    plt.figure(figsize=(10, 5))
    meal_spike.plot(kind="bar", color="salmon")
    plt.title("Spike Rate vs. Minutes Since Last Meal")
    plt.xlabel("Minutes Since Last Meal (30 min bins)")
    plt.ylabel("Spike Rate")
    plt.tight_layout()
    plt.savefig(fig_dir / "day4_meal_vs_spike.png", dpi=150)
    plt.close()
    
    # 7. day4_archetype_spike_rate.png
    arch_spike = valid_df.groupby("archetype")["spike_next_2h"].mean()
    plt.figure(figsize=(6, 5))
    arch_spike.plot(kind="bar", color="teal")
    plt.title("Spike Rate by Archetype\n(FOR ANALYSIS ONLY - Archetype is hidden from models)")
    plt.ylabel("Spike Rate")
    plt.tight_layout()
    plt.savefig(fig_dir / "day4_archetype_spike_rate.png", dpi=150)
    plt.close()

if __name__ == "__main__":
    main()
