-- Analysis queries (Oracle). Valid rows only unless stated.

-- Q1. Average length of stay: overall and by department (completed valid stays in analysis window)
SELECT NVL(d.department_name, 'ALL DEPARTMENTS') AS department,
       COUNT(*) AS stays, ROUND(AVG(a.los_days), 2) AS avg_los_days
FROM fact_admission a JOIN dim_department d ON d.department_id = a.department_id
WHERE a.is_valid = 'Y' AND a.status = 'DISCHARGED' AND a.admit_date >= DATE '2024-01-01'
GROUP BY ROLLUP (d.department_name);

-- Q2. Bed occupancy % by department over the whole window
SELECT department_name, ROUND(100 * SUM(occupied_beds) / SUM(bed_capacity), 1) AS occupancy_pct
FROM vw_daily_dept_occupancy GROUP BY department_name ORDER BY occupancy_pct DESC;

-- Q3. Monthly hospital occupancy %
SELECT TO_CHAR(month_start,'YYYY-MM') AS month, ROUND(100 * SUM(occupied_beds) / SUM(bed_capacity), 1) AS occupancy_pct
FROM vw_daily_hospital_occupancy GROUP BY month_start ORDER BY month_start;

-- Q4. Peak-load days
SELECT date_key, TO_CHAR(date_key,'DY','NLS_DATE_LANGUAGE=ENGLISH') AS weekday, occupied_beds, bed_capacity, occupancy_pct, peak_rank
FROM vw_peak_days ORDER BY peak_rank, date_key;

-- Q5. Departments that exceeded 100% on any day
SELECT department_name, COUNT(*) AS days_over_capacity, MAX(occupancy_pct) AS worst_day_pct
FROM vw_daily_dept_occupancy WHERE occupancy_pct > 100 GROUP BY department_name ORDER BY days_over_capacity DESC;

-- Q6. Same-day discharge rate by department
SELECT d.department_name, COUNT(*) AS stays,
       SUM(CASE WHEN a.same_day_flag = 'Y' THEN 1 ELSE 0 END) AS same_day,
       ROUND(100 * AVG(CASE WHEN a.same_day_flag = 'Y' THEN 1 ELSE 0 END), 1) AS same_day_pct
FROM fact_admission a JOIN dim_department d ON d.department_id = a.department_id
WHERE a.is_valid = 'Y' AND a.status = 'DISCHARGED'
GROUP BY d.department_name ORDER BY same_day_pct DESC;

-- Q7. Data-quality summary
SELECT dq_flag, COUNT(*) AS rows_cnt, ROUND(100 * RATIO_TO_REPORT(COUNT(*)) OVER (), 2) AS pct
FROM fact_admission GROUP BY dq_flag ORDER BY rows_cnt DESC;

-- Q8. Independent overlap detector: every row returned should be a later stay already flagged OVERLAP
SELECT a.patient_id, a.admission_id AS earlier_stay, b.admission_id AS later_stay, b.dq_flag AS later_flag
FROM fact_admission a
JOIN fact_admission b
  ON a.patient_id = b.patient_id
 AND (a.admit_date < b.admit_date OR (a.admit_date = b.admit_date AND a.admission_id < b.admission_id))
WHERE a.dq_flag = 'OK' AND a.discharge_date IS NOT NULL
  AND b.dq_flag NOT IN ('MISSING_DISCHARGE','INVALID_DATES')
  AND b.admit_date < a.discharge_date;   -- admit == previous discharge is a transfer, not an overlap

-- Q9. Occupancy sanity check for one date (compare with Power BI card): beds occupied on 2024-01-19
SELECT SUM(occupied_beds) AS occupied, SUM(bed_capacity) AS capacity FROM vw_daily_dept_occupancy WHERE date_key = DATE '2024-01-19';
