-- Reporting views (Power BI imports these)

-- Daily occupancy per department (includes days with zero occupancy)
CREATE OR REPLACE VIEW vw_daily_dept_occupancy AS
SELECT dt.date_key, dt.year_num, dt.month_num, dt.month_start, dt.month_name, dt.day_name, dt.is_weekend,
       dp.department_id, dp.department_name, dp.bed_capacity,
       COUNT(a.admission_id)                                   AS occupied_beds,
       ROUND(100 * COUNT(a.admission_id) / dp.bed_capacity, 1) AS occupancy_pct
FROM dim_date dt
CROSS JOIN dim_department dp
LEFT JOIN fact_admission a
       ON a.department_id = dp.department_id
      AND a.is_valid = 'Y'
      AND dt.date_key BETWEEN a.admit_date AND a.occ_end_date
GROUP BY dt.date_key, dt.year_num, dt.month_num, dt.month_start, dt.month_name, dt.day_name, dt.is_weekend,
         dp.department_id, dp.department_name, dp.bed_capacity;

-- Hospital-wide daily occupancy
CREATE OR REPLACE VIEW vw_daily_hospital_occupancy AS
SELECT date_key, month_start, SUM(occupied_beds) AS occupied_beds, SUM(bed_capacity) AS bed_capacity,
       ROUND(100 * SUM(occupied_beds) / SUM(bed_capacity), 1) AS occupancy_pct
FROM vw_daily_dept_occupancy
GROUP BY date_key, month_start;

-- Top 10 peak-load days (ties included)
CREATE OR REPLACE VIEW vw_peak_days AS
SELECT * FROM (
  SELECT h.*, RANK() OVER (ORDER BY occupancy_pct DESC) AS peak_rank FROM vw_daily_hospital_occupancy h
) WHERE peak_rank <= 10;

-- Department x month KPI table
CREATE OR REPLACE VIEW vw_dept_month_kpi AS
SELECT o.department_name, o.month_start,
       ROUND(100 * SUM(o.occupied_beds) / SUM(o.bed_capacity), 1) AS occupancy_pct,
       MAX(l.admissions)  AS admissions,
       MAX(l.avg_los)     AS avg_los_days
FROM vw_daily_dept_occupancy o
LEFT JOIN (
  SELECT department_id, TRUNC(admit_date,'MM') AS month_start, COUNT(*) AS admissions, ROUND(AVG(los_days),2) AS avg_los
  FROM fact_admission WHERE is_valid = 'Y' AND status = 'DISCHARGED'
  GROUP BY department_id, TRUNC(admit_date,'MM')
) l ON l.department_id = o.department_id AND l.month_start = o.month_start
GROUP BY o.department_name, o.month_start;
