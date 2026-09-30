# Features Registry
This document is auto-generated. Do not edit directly.

| Feature Name | Group | Type | Description | Units |
|---|---|---|---|---|
| `glu_current` | A | float | Current observed glucose | mg/dL |
| `glu_lag_5m` | A | float | Glucose 5 min ago | mg/dL |
| `glu_lag_15m` | A | float | Glucose 15 min ago | mg/dL |
| `glu_lag_30m` | A | float | Glucose 30 min ago | mg/dL |
| `glu_lag_60m` | A | float | Glucose 60 min ago | mg/dL |
| `glu_lag_120m` | A | float | Glucose 120 min ago | mg/dL |
| `glu_delta_5m` | A | float | Glucose change over 5 min | mg/dL |
| `glu_delta_15m` | A | float | Glucose change over 15 min | mg/dL |
| `glu_delta_30m` | A | float | Glucose change over 30 min | mg/dL |
| `glu_delta_60m` | A | float | Glucose change over 60 min | mg/dL |
| `glu_slope_30m` | A | float | Glucose slope over 30 min | mg/dL/min |
| `glu_accel` | A | float | Glucose slope acceleration (15m - prev 15m) | mg/dL/min |
| `glu_roll_mean_30m` | A | float | Rolling mean glucose 30 min | mg/dL |
| `glu_roll_mean_60m` | A | float | Rolling mean glucose 60 min | mg/dL |
| `glu_roll_mean_120m` | A | float | Rolling mean glucose 120 min | mg/dL |
| `glu_roll_std_30m` | A | float | Rolling std glucose 30 min | mg/dL |
| `glu_roll_std_60m` | A | float | Rolling std glucose 60 min | mg/dL |
| `glu_roll_std_120m` | A | float | Rolling std glucose 120 min | mg/dL |
| `glu_roll_min_30m` | A | float | Rolling min glucose 30 min | mg/dL |
| `glu_roll_min_60m` | A | float | Rolling min glucose 60 min | mg/dL |
| `glu_roll_min_120m` | A | float | Rolling min glucose 120 min | mg/dL |
| `glu_roll_max_30m` | A | float | Rolling max glucose 30 min | mg/dL |
| `glu_roll_max_60m` | A | float | Rolling max glucose 60 min | mg/dL |
| `glu_roll_max_120m` | A | float | Rolling max glucose 120 min | mg/dL |
| `glu_range_60m` | A | float | Glucose range (max-min) over 60 min | mg/dL |
| `glu_above_180_frac_60m` | A | float | Fraction > 180 in 60m | ratio |
| `glu_below_70_frac_60m` | A | float | Fraction < 70 in 60m | ratio |
| `meal_carbs_last_60m` | B | float | Carbs eaten in last 60m | g |
| `meal_carbs_last_120m` | B | float | Carbs eaten in last 120m | g |
| `meal_carbs_last_240m` | B | float | Carbs eaten in last 240m | g |
| `meal_min_since_last` | B | float | Minutes since last meal | min |
| `meal_any_in_history` | B | int | Has any meal occurred in history | bool |
| `meal_last_carbs_g` | B | float | Carbs of last meal | g |
| `meal_count_last_6h` | B | float | Number of meals in last 6h | count |
| `meal_cob_estimate` | B | float | Carbs on board estimate | g |
| `act_steps_last_30m` | C | float | Steps in last 30m | count |
| `act_steps_last_60m` | C | float | Steps in last 60m | count |
| `act_steps_last_120m` | C | float | Steps in last 120m | count |
| `act_max_intensity_last_60m` | C | float | Max activity intensity in last 60m | level |
| `act_min_since_moderate` | C | float | Minutes since intensity >= 2 | min |
| `act_current_intensity` | C | int | Current activity intensity | level |
| `hr_current` | D | float | Current heart rate | bpm |
| `hr_roll_mean_30m` | D | float | Rolling mean HR 30m | bpm |
| `hr_roll_mean_60m` | D | float | Rolling mean HR 60m | bpm |
| `hr_roll_std_30m` | D | float | Rolling std HR 30m | bpm |
| `hr_delta_30m` | D | float | HR change over 30m | bpm |
| `hr_vs_personal_baseline` | D | float | HR vs rolling past 24h median | bpm |
| `sleep_is_asleep` | E | int | Currently asleep | bool |
| `sleep_state_awake` | E | int | Sleep state: awake | bool |
| `sleep_state_light` | E | int | Sleep state: light | bool |
| `sleep_state_deep` | E | int | Sleep state: deep | bool |
| `sleep_state_rem` | E | int | Sleep state: rem | bool |
| `sleep_minutes_last_12h` | E | float | Minutes asleep in last 12h | min |
| `sleep_deep_rem_frac_last_12h` | E | float | Fraction of sleep in deep/rem last 12h | ratio |
| `sleep_min_since_wake` | E | float | Minutes since last wake transition | min |
| `time_hour_sin` | F | float | Hour of day sine | unitless |
| `time_hour_cos` | F | float | Hour of day cosine | unitless |
| `time_dow_sin` | F | float | Day of week sine | unitless |
| `time_dow_cos` | F | float | Day of week cosine | unitless |
| `time_is_weekend` | F | int | Is weekend | bool |
| `ehr_age` | G | float | Age | years |
| `ehr_sex_male` | G | int | Sex is male | bool |
| `ehr_bmi` | G | float | BMI | kg/m2 |
| `ehr_hba1c` | G | float | HbA1c | % |
| `ehr_duration_years` | G | float | Diabetes duration | years |
| `ehr_on_insulin` | G | int | On insulin | bool |
| `ehr_on_metformin` | G | int | On metformin | bool |
| `ehr_hypertension` | G | int | Has hypertension | bool |
| `pers_glu_mean_24h` | H | float | Past 24h mean glucose | mg/dL |
| `pers_glu_std_24h` | H | float | Past 24h std glucose | mg/dL |
| `pers_glu_deviation` | H | float | Current glucose minus past 24h mean | mg/dL |
| `pers_time_in_range_24h` | H | float | Fraction 70-180 in past 24h | ratio |
| `miss_glucose_current` | I | int | Current glucose is missing | bool |
| `miss_glucose_frac_60m` | I | float | Fraction missing in 60m | ratio |
| `miss_min_since_last_obs` | I | float | Minutes since last observed glucose | min |
