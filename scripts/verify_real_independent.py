import json
import math
from pathlib import Path
import pandas as pd
from sklearn.linear_model import LinearRegression


def verify_real_independent():
    root = Path(__file__).resolve().parent.parent
    profiles_path = root / "data" / "processed" / "real_profiles.csv"
    glucose_path = root / "data" / "processed" / "real_glucose.csv"
    report_path = root / "reports" / "realism_comparison.json"

    if not profiles_path.exists() or not glucose_path.exists():
        print("Real data files are not present in this checkout.")
        return True

    if not report_path.exists():
        print("Realism report is not present.")
        return False

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    profiles = pd.read_csv(profiles_path)
    glucose = pd.read_csv(glucose_path)

    # 1. Counts
    samples = len(glucose)
    patients = int(profiles["patient_id"].nunique())
    recordings = int(glucose["recording_id"].nunique())

    exp_counts = report["real_counts"]
    assert samples == exp_counts["samples"], f"Sample count mismatch: {samples} vs {exp_counts['samples']}"
    assert patients == exp_counts["patients"], f"Patient count mismatch: {patients} vs {exp_counts['patients']}"
    assert recordings == exp_counts["recordings"], f"Recording count mismatch: {recordings} vs {exp_counts['recordings']}"

    # 2. Insulin use share
    insulin_share = float(profiles["use_insulin"].mean())
    assert math.isclose(insulin_share, report["real_use_insulin"], abs_tol=1e-4), (
        f"Insulin share mismatch: {insulin_share} vs {report['real_use_insulin']}"
    )

    # 3. Label prevalence
    prevalence = float(glucose["label"].mean())
    assert math.isclose(prevalence, report["real_label_prevalence"], abs_tol=1e-4), (
        f"Prevalence mismatch: {prevalence} vs {report['real_label_prevalence']}"
    )

    # 4. Regression of mean glucose on HbA1c
    mean_glucose = glucose.groupby("patient_id")["glucose_mgdl"].mean().reset_index()
    merged = profiles[["patient_id", "hba1c"]].merge(mean_glucose, on="patient_id").dropna()
    X = merged[["hba1c"]].values
    y = merged["glucose_mgdl"].values

    reg = LinearRegression().fit(X, y)
    exp_reg = report["real_regression"]

    assert len(X) == exp_reg["patients"], f"Regression patient count mismatch: {len(X)} vs {exp_reg['patients']}"
    assert math.isclose(reg.coef_[0], exp_reg["slope"], abs_tol=1e-4), (
        f"Slope mismatch: {reg.coef_[0]} vs {exp_reg['slope']}"
    )
    assert math.isclose(reg.intercept_, exp_reg["intercept"], abs_tol=1e-4), (
        f"Intercept mismatch: {reg.intercept_} vs {exp_reg['intercept']}"
    )
    assert math.isclose(reg.score(X, y), exp_reg["r_squared"], abs_tol=1e-4), (
        f"R-squared mismatch: {reg.score(X, y)} vs {exp_reg['r_squared']}"
    )

    print("Independent real data verification: PASS")
    print(f"Recordings: {recordings}, Patients: {patients}, Samples: {samples}")
    print(f"Label prevalence: {prevalence:.4f}, Insulin share: {insulin_share:.4f}")
    print(f"Regression on HbA1c: slope={reg.coef_[0]:.4f}, intercept={reg.intercept_:.4f}, r2={reg.score(X, y):.4f}")
    return True


if __name__ == "__main__":
    verify_real_independent()
