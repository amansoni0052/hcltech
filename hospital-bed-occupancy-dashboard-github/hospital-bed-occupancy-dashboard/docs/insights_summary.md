# Insights Summary  (window 2024-01-01 to 2025-06-30; synthetic data)
- **Overall average LOS:** 2.78 days (completed valid stays). Longest: ICU (4.54 d); shortest: Emergency (1.0 d).
- **Overall bed occupancy:** 71.4%. Highest department: Emergency (75.1%); lowest: Maternity (67.7%).
- **Peak load:** 11 days had hospital-wide occupancy >= 90%. Top 10 peak days: 19 Jan 2024 (95.2%), 21 Feb 2025 (94.4%), 19 Feb 2024 (94.4%), 17 Feb 2024 (92.2%), 19 Feb 2025 (91.1%), 03 Jan 2024 (90.4%), 04 Jan 2024 (90.4%), 18 Feb 2025 (90.0%), 22 Jan 2024 (90.0%), 21 Jan 2024 (90.0%).
- **Seasonality:** busiest month 2024-01 (84.3%), quietest 2025-06 (65.9%).
- **Weekday vs weekend:** weekdays 72.5% vs weekends 68.8% average occupancy.
- **Departments over capacity (>100% on at least one day):** ICU (57 days), Emergency (39 days), Orthopedics (29 days), Pediatrics (21 days), Maternity (18 days), Cardiology (15 days), Surgery (15 days), General Medicine (3 days).
- **Same-day discharge:** 17.9% of stays overall; highest in Emergency (39.1%).
- **Data quality:** 97.3% of de-duplicated rows were valid; see data_quality_report.md.

## Recommendations
1. Plan extra staffed beds for Jan-Feb, where the peak-load days cluster.
2. Review discharge planning in the longest-LOS department to free beds.
3. Fix source-system entry: mandatory discharge date, controlled department list, date validation.
