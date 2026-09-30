import sys
from pathlib import Path
import numpy as np
import hashlib
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from src.data_gen.glucose_dynamics import simulate_glucose

def main():
    rng = np.random.default_rng(42)
    n_steps = 288 * 2  # 2 days
    
    meal_carbs = np.zeros(n_steps)
    meal_carbs[20] = 50
    meal_carbs[100] = 30
    
    activity = np.zeros(n_steps)
    activity[50:60] = 1
    
    sleep_state = np.array(['awake'] * n_steps)
    sleep_state[200:250] = 'deep'
    
    true_glucose, observed_glucose = simulate_glucose(
        baseline=110.0,
        dawn_amp=20.0,
        carb_sens=1.5,
        decay=0.05,
        ex_sens=1.2,
        meal_carbs=meal_carbs,
        activity=activity,
        sleep_state=sleep_state,
        sleep_quality=0.8,
        sensor_noise_sd=2.0,
        rng=rng,
        initial_glucose=100.0
    )
    
    df = pd.DataFrame({
        'true_glucose': true_glucose,
        'observed_glucose': observed_glucose
    })
    
    golden_dir = Path("tests/golden")
    golden_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(golden_dir / "day3_glucose_fixture.parquet")
    
    sha = hashlib.sha256(open(golden_dir / "day3_glucose_fixture.parquet", "rb").read()).hexdigest()
    print(f"Golden fixture created. SHA256: {sha}")
    
    with open(golden_dir / "fixture_hash.txt", "w") as f:
        f.write(sha)

if __name__ == "__main__":
    main()
