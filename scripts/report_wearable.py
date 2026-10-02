import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config


def main():
    config = load_config()
    raw_dir = Path(config["paths"]["data_raw"])
    fig_dir = Path(config["paths"]["reports"]) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    patients_df = pd.read_csv(raw_dir / "patients.csv")
    sim_params_df = pd.read_csv(raw_dir / "patient_sim_params.csv")
    wearable_df = pd.read_csv(raw_dir / "wearable.csv")
    
    merged = wearable_df.merge(sim_params_df[["patient_id", "archetype"]], on="patient_id")
    
    # 1. day3_sample_patient_3days.png
    plt.figure(figsize=(15, 10))
    archetypes = ["well_controlled", "moderate", "poorly_controlled"]
    for i, arch in enumerate(archetypes):
        pid = sim_params_df[sim_params_df["archetype"] == arch].iloc[0]["patient_id"]
        p_data = wearable_df[wearable_df["patient_id"] == pid].iloc[:288*3]
        
        plt.subplot(3, 1, i+1)
        plt.plot(range(len(p_data)), p_data["glucose_mgdl"], label="Glucose", color="blue")
        plt.axhspan(70, 180, color='green', alpha=0.2, label="Target Range")
        
        meals = p_data[p_data["meal_carbs_g"] > 0]
        for idx in meals.index:
            rel_idx = idx - p_data.index[0]
            plt.axvline(rel_idx, color='red', linestyle='--', alpha=0.5)
            
        plt.title(f"Patient {pid} ({arch}) - 3 Days")
        plt.ylabel("Glucose (mg/dL)")
        if i == 2:
            plt.xlabel("Time (5-min intervals)")
            
    plt.tight_layout()
    plt.savefig(fig_dir / "day3_sample_patient_3days.png", dpi=150)
    plt.close()
    
    # 2. day3_mean_daily_glucose_profile.png
    merged["hour"] = (merged.groupby("patient_id").cumcount() % 288) / 12.0
    hourly_mean = merged.groupby(["archetype", "hour"])["glucose_mgdl"].mean().reset_index()
    
    plt.figure(figsize=(10, 6))
    for arch in archetypes:
        d = hourly_mean[hourly_mean["archetype"] == arch]
        plt.plot(d["hour"], d["glucose_mgdl"], label=arch)
        
    plt.title("Mean Daily Glucose Profile by Archetype")
    plt.xlabel("Hour of Day")
    plt.ylabel("Mean Glucose (mg/dL)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(fig_dir / "day3_mean_daily_glucose_profile.png", dpi=150)
    plt.close()
    
    # 3. day3_time_in_range_by_archetype.png
    def calc_tir(x):
        below = (x < 70).mean() * 100
        in_range = x.between(70, 180).mean() * 100
        above = (x > 180).mean() * 100
        return pd.Series({"<70": below, "70-180": in_range, ">180": above})
        
    tir_df = merged.groupby("archetype")["glucose_mgdl"].apply(calc_tir).unstack().reindex(archetypes)
    
    tir_df.plot(kind="bar", stacked=True, figsize=(8, 6), color=["red", "green", "orange"])
    plt.title("Time in Range by Archetype")
    plt.ylabel("% of Time")
    plt.xticks(rotation=0)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(fig_dir / "day3_time_in_range_by_archetype.png", dpi=150)
    plt.close()
    
    # 4. day3_hr_by_sleep_state.png
    plt.figure(figsize=(8, 6))
    sleep_states = ["awake", "light", "deep", "rem"]
    data = [merged[merged["sleep_state"] == s]["heart_rate"].dropna() for s in sleep_states]
    plt.boxplot(data)
    plt.xticks([1, 2, 3, 4], sleep_states)
    plt.title("Heart Rate by Sleep State")
    plt.ylabel("Heart Rate (bpm)")
    plt.tight_layout()
    plt.savefig(fig_dir / "day3_hr_by_sleep_state.png", dpi=150)
    plt.close()
    
    print("Wearable figures saved in reports/figures/")

if __name__ == "__main__":
    main()
