# Demo Video Script (~5 min)
1. **0:00** Problem: hospitals can't see occupancy and LOS because data is messy (show raw CSV with mixed dates, blanks).
2. **0:40** Python cleaning: run `clean_data.py`; show `data_quality_report.md` (duplicates, overlaps, missing discharge).
3. **1:40** LOS proof: open `los_verification_20.csv` - pipeline, independent and calendar-count columns match for all 20.
4. **2:20** Oracle: ER diagram, run DDL, load, views; run Q1, Q3, Q4.
5. **3:20** Dashboard (`dashboard/index.html`): department/month slicers, click a month to drill down, daily chart, peak-day table.
6. **4:30** Insights (from `insights_summary.md`) and recommendations. Close with GitHub link.
