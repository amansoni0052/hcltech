-- Oracle 12c+ | Star schema for Hospital Admissions & Bed Occupancy
-- Run order: 01_ddl.sql -> 02_load (SQL*Loader, see sql/loader) -> 02b_dim_date.sql -> 04_views.sql -> 03_queries.sql

BEGIN
  FOR t IN (SELECT table_name FROM user_tables WHERE table_name IN ('FACT_ADMISSION','DIM_PATIENT','DIM_DEPARTMENT','DIM_DATE')) LOOP
    EXECUTE IMMEDIATE 'DROP TABLE ' || t.table_name || ' CASCADE CONSTRAINTS';
  END LOOP;
END;
/

CREATE TABLE dim_department (
  department_id   NUMBER(3)     PRIMARY KEY,
  department_name VARCHAR2(50)  NOT NULL UNIQUE,
  bed_capacity    NUMBER(4)     NOT NULL CHECK (bed_capacity > 0)
);

CREATE TABLE dim_patient (
  patient_id VARCHAR2(10) PRIMARY KEY,
  gender     CHAR(1)      CHECK (gender IN ('M','F'))
);

CREATE TABLE dim_date (
  date_key     DATE         PRIMARY KEY,
  year_num     NUMBER(4)    NOT NULL,
  month_num    NUMBER(2)    NOT NULL,
  month_start  DATE         NOT NULL,
  month_name   VARCHAR2(10) NOT NULL,
  day_name     VARCHAR2(3)  NOT NULL,
  is_weekend   CHAR(1)      NOT NULL
);

CREATE TABLE fact_admission (
  admission_id     VARCHAR2(10) PRIMARY KEY,
  patient_id       VARCHAR2(10) NOT NULL REFERENCES dim_patient(patient_id),
  department_id    NUMBER(3)    NOT NULL REFERENCES dim_department(department_id),
  admit_date       DATE         NOT NULL,
  discharge_date   DATE,                       -- NULL = missing or still admitted (see status)
  age_at_admission NUMBER(3),
  los_days         NUMBER(4),                  -- discharge - admit; 0 for same-day; NULL if not completed/valid
  bed_days         NUMBER(4),
  occ_end_date     DATE,                       -- last date the bed was occupied (midnight-census rule)
  status           VARCHAR2(20) NOT NULL CHECK (status IN ('DISCHARGED','ADMITTED','MISSING_DISCHARGE','INVALID')),
  same_day_flag    CHAR(1)      NOT NULL CHECK (same_day_flag IN ('Y','N')),
  dq_flag          VARCHAR2(20) NOT NULL,      -- OK / MISSING_DISCHARGE / INVALID_DATES / OVERLAP
  is_valid         CHAR(1)      NOT NULL CHECK (is_valid IN ('Y','N'))
);
CREATE INDEX ix_fact_dept_dates ON fact_admission (department_id, admit_date, occ_end_date);
CREATE INDEX ix_fact_patient    ON fact_admission (patient_id, admit_date);
