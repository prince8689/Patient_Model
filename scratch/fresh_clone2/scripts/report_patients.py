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
    
    patients_path = raw_dir / "patients.csv"
    sim_params_path = raw_dir / "patient_sim_params.csv"
    
    if not patients_path.exists() or not sim_params_path.exists():
        print("Data files not found. Run generate_patients.py first.")
        return
        
    patients_df = pd.read_csv(patients_path)
    sim_params_df = pd.read_csv(sim_params_path)
    merged_df = patients_df.merge(sim_params_df, on="patient_id")
    
    # Plot 1: hba1c_by_archetype.png (boxplot)
    plt.figure(figsize=(8, 6))
    archetypes = ["well_controlled", "moderate", "poorly_controlled"]
    data = [merged_df[merged_df["archetype"] == a]["hba1c"] for a in archetypes]
    plt.boxplot(data)
    plt.xticks([1, 2, 3], archetypes)
    plt.title("HbA1c Distribution by Patient Archetype")
    plt.xlabel("Archetype")
    plt.ylabel("HbA1c (%)")
    plt.tight_layout()
    plt.savefig(fig_dir / "hba1c_by_archetype.png", dpi=150)
    plt.close()
    
    # Plot 2: age_bmi_hba1c.png (histograms, 3 panels)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes[0].hist(patients_df["age"], bins=10, edgecolor='black', color='skyblue')
    axes[0].set_title("Age Distribution")
    axes[0].set_xlabel("Age (years)")
    axes[0].set_ylabel("Count")
    
    axes[1].hist(patients_df["bmi"], bins=10, edgecolor='black', color='lightgreen')
    axes[1].set_title("BMI Distribution")
    axes[1].set_xlabel("BMI")
    axes[1].set_ylabel("Count")
    
    axes[2].hist(patients_df["hba1c"], bins=10, edgecolor='black', color='salmon')
    axes[2].set_title("HbA1c Distribution")
    axes[2].set_xlabel("HbA1c (%)")
    axes[2].set_ylabel("Count")
    
    plt.tight_layout()
    plt.savefig(fig_dir / "age_bmi_hba1c.png", dpi=150)
    plt.close()
    
    # Plot 3: cohort_correlation_heatmap.png
    num_cols = ["age", "bmi", "hba1c", "diabetes_duration_years", "baseline_insulin_sensitivity"]
    corr = patients_df[num_cols].corr()
    
    fig, ax = plt.subplots(figsize=(8, 6))
    cax = ax.matshow(corr, vmin=-1, vmax=1, cmap="coolwarm")
    fig.colorbar(cax)
    
    ax.set_xticks(range(len(num_cols)))
    ax.set_yticks(range(len(num_cols)))
    ax.set_xticklabels(num_cols, rotation=45, ha='left')
    ax.set_yticklabels(num_cols)
    ax.xaxis.set_ticks_position('bottom')
    
    for i in range(len(num_cols)):
        for j in range(len(num_cols)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", color="black")
            
    plt.title("Correlation Heatmap of Key Clinical Variables", pad=20)
    plt.tight_layout()
    plt.savefig(fig_dir / "cohort_correlation_heatmap.png", dpi=150)
    plt.close()
    
    print("Figures saved in reports/figures/")

if __name__ == "__main__":
    main()
