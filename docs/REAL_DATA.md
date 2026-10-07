# Real Data: ShanghaiT2DM

## Attribution
The dataset used for realism comparison is the ShanghaiT2DM cohort.
Citation: Zhao Q, Zhu J, Shen X, Lin C, Zhang Y, Liang Y, Cao B, Li J, Liu X, Rao W, Wang C. Chinese diabetes datasets for data-driven machine learning. Scientific Data 10, 35 (2023). doi:10.1038/s41597-023-01940-7.
Dataset: figshare DOI 10.6084/m9.figshare.c.6310860.
License: CC BY 4.0 as listed on the figshare page.

## Notes shipped with the dataset
This version is to add 188 CGM measurements on ShanghaiT2DM. 
In the "Shanghai_T2DM" folder, the file "2003_0_20210615" has extended rows from 586 to 670, with rows from 587 to 670 newly added.

In the "Shanghai_T2DM" folder, the file "2029_0_20210526" has extended rows from 742 to 846 with rows from 743 to 846 newly added. From line 743 to 755, the CGM values are missing because the CGM device has been changed to a new one. The readings of the new CGM device started from 2021/6/3 12:46.


“Shanghai_T2DM”文件夹中的“2003_0_20210615”文件从586行增加到670行，587~670行为新增数据
“Shanghai_T2DM”文件夹中的“2029_0_20210526”文件从742行增加到846行，743~846行为新增数据


2023/10/26

## Limitations
- **Missing Sensors**: The data lacks auxiliary wearable signals such as heart rate, steps, and sleep states.
- **Sampling Frequency**: It uses a 15-minute sampling grid instead of the 5-minute grid assumed by DiaTwin.
- **Cohort Size & Diversity**: It is a small cohort (100 patients) from one city and one population.
- **Dietary Data Format**: Dietary intake is recorded in textual format, lacking quantified carbohydrate grams.
- **Model Incompatibility**: The frozen DiaTwin model cannot be applied directly without resampling and feature imputation.
- **What-if Validation**: The What-if scenario generator cannot be validated on real data because the true counterfactual is unknown.

## Incident Record
A review found that a previous training run loaded the real test split and reported a test AUC, which broke the sealing rule. The real test split is no longer sealed. Real-data results below use patient-wise cross-validation over all patients instead of a single held-out test.

## Dataset File Inventory
* **Folder Layout:** 
  * Shanghai_T2DM_Summary.xlsx: Contains patient profiles, one row per patient.
  * Shanghai_T2DM/: Contains 109 timeseries files (either .xls or .xlsx).
* **Columns per File Type:** 
  * Summary: Patient Number, Gender, Age, Height, Weight, BMI, etc.
  * CGM timeseries: Date, CGM, CBG, Dietary intake, Insulin doses, etc.
* **Time Format:** YYYY-MM-DD HH:MM:SS at 15-minute intervals.
* **Recordings per Patient:** 1 to 3 recordings per patient identifier.
* **Units:** 
  * The dataset summary lists Fasting Plasma Glucose in (mg/dl).
  * The CGM files explicitly name the column CGM (mg / dl) in most files.
  * The raw values are typically between 80 and 250, which mathematically corresponds to mg/dL (mmol/L values would be ~4.0 to 15.0).
  * The dataset provides HbA1c in mmol/mol (IFCC). It is converted to % (DCCT) using the formula: HbA1c (%) = (HbA1c_mmol_mol / 10.929) + 2.15.
