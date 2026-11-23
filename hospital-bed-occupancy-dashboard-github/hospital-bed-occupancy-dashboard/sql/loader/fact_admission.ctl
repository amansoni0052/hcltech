OPTIONS (SKIP=1, ROWS=5000)
LOAD DATA INFILE '../../data/processed/fact_admission.csv'
APPEND INTO TABLE fact_admission
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' TRAILING NULLCOLS
(admission_id, patient_id, department_id,
 admit_date DATE "YYYY-MM-DD", discharge_date DATE "YYYY-MM-DD",
 age_at_admission, los_days, bed_days,
 occ_end_date DATE "YYYY-MM-DD",
 status, same_day_flag, dq_flag, is_valid)
