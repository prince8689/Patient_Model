# User Data Entry Feature

## Overview
The Personalized Data Entry feature allows users (e.g., clinicians, researchers) to enter a patient's custom profile and physiological data directly into the DiaTwin Streamlit dashboard to generate real-time glucose risk forecasts using the frozen risk models.

## Tiers and Confidence Rules
User data is evaluated against strict data sufficiency requirements to ensure the underlying models behave predictably.

1. **Full Tier**
   - Requires at least 24 hours of continuous glucose history (same rules as the backend engine).
   - The result is identical to the main simulation engine, utilizing full rolling feature capabilities.
   - Confidence: **High**

2. **Partial Tier**
   - Requires at least 3 glucose readings in the last 45 minutes spanning at least 30 minutes.
   - Uses an "Indicative Estimate" path that skips the 24-hour warm-up requirement.
   - Confidence: **Medium** (if allowed by config) or **Low**.

3. **Single Tier**
   - Requires at least one recent reading (no older than 20 minutes).
   - Confidence: **Low**.

## Defaulted Values
For the indicative paths (Partial/Single), certain missing groups are filled with training medians or logical defaults:
- **Heart Rate**: 70.0 bpm
- **Steps**: 0.0 (or user-provided steps in last hour)
- **Sleep State**: Assumed schedule (light sleep between bedtime and wake time, awake otherwise; defaults to 23:00 to 07:00).
- **Missing 24h history features**: Cumulatives like `meal_min_since_last` default to 120.0 minutes to prevent edge-case explosions.

## Privacy and Data Storage
- **Privacy Guarantee**: User data lives strictly within `st.session_state` for the duration of the browser session.
- It is **never** written to a file, database, log, cache, or the demo bundle.
- The UI explicitly prevents analytics or tracking.

## Limitations
This prototype is built on synthetic physiological approximations designed for research demonstration. If an entered profile or glucose reading falls outside the model's training range, a prominent warning is displayed indicating that the prediction is extrapolated. No treatment decisions should ever be made based on this tool.
