# Real Data: ShanghaiT2DM

## Attribution
The dataset used for realism comparison is the ShanghaiT2DM cohort.
Citation: Zhao et al., Scientific Data 10, 35, 2023.
Source: figshare collection DOI 10.6084/m9.figshare.c.6310860.
License: CC BY 4.0 (as shown on the download page).

## Limitations
- **Missing Sensors**: The data lacks auxiliary wearable signals such as heart rate, steps, and sleep states.
- **Sampling Frequency**: It uses a 15-minute sampling grid instead of the 5-minute grid assumed by DiaTwin.
- **Cohort Size & Diversity**: It is a small cohort (100 patients) from one city and one population.
- **Dietary Data Format**: Dietary intake is recorded in textual format, lacking quantified carbohydrate grams.
- **Model Incompatibility**: The frozen DiaTwin model cannot be applied directly without resampling and feature imputation.
- **What-if Validation**: The What-if scenario generator cannot be validated on real data because the true counterfactual is unknown.
