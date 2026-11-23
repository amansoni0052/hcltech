# Power BI Dashboard Build Guide  (.pbix must be built in Power BI Desktop on Windows)
1. **Get Data** -> Oracle Database (or Text/CSV from `data/processed/`). Load `vw_daily_dept_occupancy`, `fact_admission`, `dim_department`, `dim_date`.
2. **Model**: create the relationships and paste measures from `powerbi/dax_measures.dax`. Mark `dim_date` as Date table.
3. **Page 1 - Overview**: cards (Occupancy %, Avg LOS, Admissions Count, Same-Day Discharge %, Peak Days Count);
   line chart Occupancy % by month; bar chart Occupancy % by department (conditional colour = `Occupancy Colour`).
   Slicers: Department, Month, Year.
4. **Page 2 - Peak Load**: line chart of daily Occupancy % with a 90% constant line; table of top-10 days using `Peak Day Rank <= 10`.
   Heatmap (matrix): rows = department, columns = month, value = Occupancy %.
5. **Page 3 - Length of Stay**: Avg LOS by department; histogram-style column chart of LOS buckets; **drill-down** hierarchy Year > Month > Day.
6. **Page 4 - Data Quality**: card Valid Row %; bar chart of `dq_flag` counts (filter out OK).
7. **Drill-through**: right-click a department bar -> drill-through page showing its daily occupancy and stays.
8. Sanity test: Power BI card for **19 Jan 2024** must show 257 / 270 beds = 95.2% (same as SQL Q9 and `daily_occupancy.csv`).
9. Save as `powerbi/hospital_dashboard.pbix`. `docs/dashboard_preview.png` shows the expected shape of the key charts.
