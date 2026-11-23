OPTIONS (SKIP=1)
LOAD DATA INFILE '../../data/processed/dim_department.csv'
APPEND INTO TABLE dim_department
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' TRAILING NULLCOLS
(department_id, department_name, bed_capacity)
