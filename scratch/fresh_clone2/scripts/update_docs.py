with open("docs/SPEC.md", "a", encoding="utf-8") as f:
    f.write("\n## 14. Wearable Simulation Method\n")
    f.write("- **Glucose Dynamics**: Discrete-time compartmental model with 5-minute steps. Gut compartments model meal absorption, mean-reverting toward a dawn-adjusted baseline.\n")
    f.write("- **Behaviors**: Meals, sleep states, and step counts generated probabilistically based on patient archetype.\n")
    f.write("- **Heart Rate**: Baseline adjusted by age/BMI, affected by activity intensity and sleep state.\n")
    f.write("- **Missingness**: Random dropouts at 1.5% and structured multi-sample gaps (25% chance of one 30-90min gap daily).\n")
    f.write("- **Day 3 Assumptions added**: Heart rate recovery modeled by fast moving average. Spike rate bounds (8-35%) verified using forward rolling 120-min max on interpolated data.\n")

with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()
    
content = content.replace("## Usage", "## Data\nAll data is synthetic. Generate EHR via `python scripts/generate_patients.py` and timeseries via `python scripts/generate_wearable.py`.\n\n## Usage")

with open("README.md", "w", encoding="utf-8") as f:
    f.write(content)
