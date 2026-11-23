"""Clean raw admissions, compute LOS / bed-days / occupancy, and write all outputs.
Run:  python python/clean_data.py      (after generate_data.py)
(Cells marked '# %%' can be pasted into a Jupyter notebook as-is.)

KEY RULES (also in docs/problem_statement_kpis.md)
  * Dates parsed with explicit formats; slash dates are DD/MM/YYYY.
  * LOS (days)      = discharge_date - admit_date   (same-day discharge -> 0)
  * Bed occupancy   = midnight-census style: a stay occupies a bed on each date admit..discharge-1;
                      a same-day stay occupies the bed on its admit date (min 1 bed-day).
  * Missing discharge: if admitted within last 30 days of extract -> ADMITTED (still in hospital),
                      else MISSING_DISCHARGE -> excluded from LOS & occupancy and reported.
  * Overlap: a patient's later stay starting before an earlier valid stay ends -> OVERLAP, excluded.
    (Admit date == previous discharge date is a legitimate transfer, NOT an overlap.)"""
from datetime import datetime, date
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT, DOCS = ROOT / "data/raw", ROOT / "data/processed", ROOT / "docs"
EXTRACT = pd.Timestamp("2025-06-30"); WIN_START = pd.Timestamp("2024-01-01"); ONGOING_DAYS = 30
FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y"]
ALIASES = {"ER": "Emergency", "EMERGENCY": "Emergency", "GENMED": "General Medicine", "GENERALMEDICINE": "General Medicine",
           "SURGERY": "Surgery", "ORTHO": "Orthopedics", "ORTHOPEDICS": "Orthopedics", "CARDIO": "Cardiology",
           "CARDIOLOGY": "Cardiology", "PEDS": "Pediatrics", "PEDIATRICS": "Pediatrics", "MATERNITY": "Maternity", "ICU": "ICU"}

# %% 1. Load & parse dates
def parse_date(s):
    if pd.isna(s) or str(s).strip() == "": return pd.NaT
    for f in FORMATS:
        try: return pd.Timestamp(datetime.strptime(str(s).strip(), f))
        except ValueError: pass
    return pd.NaT

raw = pd.read_csv(RAW / "admissions_raw.csv", dtype=str)
beds = pd.read_csv(RAW / "department_beds.csv"); beds["department_id"] = range(1, len(beds) + 1)
dq = {"raw_rows": len(raw)}
df = raw.copy()
df["admit_date"] = raw.admit_date.map(parse_date); df["discharge_date"] = raw.discharge_date.map(parse_date)
dq["non_iso_date_strings"] = int(((raw.admit_date.str.contains("/|[A-Za-z]", na=False)) | (raw.discharge_date.str.contains("/|[A-Za-z]", na=False))).sum())
dq["unparseable_dates"] = int((df.admit_date.isna() | (raw.discharge_date.notna() & df.discharge_date.isna())).sum())

# %% 2. Duplicates, departments, ages
dup = df.duplicated("admission_id", keep="first"); dq["duplicate_rows_removed"] = int(dup.sum()); df = df[~dup].copy()
df = df[df.admit_date.notna()].copy()
key = df.department.str.upper().str.replace(r"[^A-Z]", "", regex=True)
canon = key.map(ALIASES); dq["department_names_standardised"] = int((df.department != canon).sum()); dq["unknown_departments"] = int(canon.isna().sum())
df["department"] = canon; df = df[df.department.notna()].copy()
df["age_at_admission"] = pd.to_numeric(df.age_at_admission); dq["missing_age"] = int(df.age_at_admission.isna().sum())

# %% 3. Status & DQ flags
df["status"] = np.where(df.discharge_date.notna(), "DISCHARGED",
                np.where(df.admit_date > EXTRACT - pd.Timedelta(days=ONGOING_DAYS), "ADMITTED", "MISSING_DISCHARGE"))
df["dq_flag"] = "OK"
df.loc[df.status == "MISSING_DISCHARGE", "dq_flag"] = "MISSING_DISCHARGE"
bad = (df.discharge_date < df.admit_date) | (df.admit_date > EXTRACT)
df.loc[bad, ["dq_flag", "status"]] = ["INVALID_DATES", "INVALID"]
cand = df[df.dq_flag == "OK"].assign(end=lambda x: x.discharge_date.fillna(EXTRACT)).sort_values(["patient_id", "admit_date", "admission_id"])
overlap = []
for _, g in cand.groupby("patient_id"):
    if len(g) < 2: continue
    mx = None
    for aid, a, e in zip(g.admission_id, g.admit_date, g.end):
        if mx is not None and a < mx: overlap.append(aid)
        else: mx = e if mx is None else max(mx, e)
df.loc[df.admission_id.isin(overlap), ["dq_flag", "status"]] = ["OVERLAP", "INVALID"]
df["is_valid"] = np.where(df.dq_flag == "OK", "Y", "N")

# %% 4. LOS, bed-days, occupancy end date
v = df.is_valid == "Y"
df["same_day_flag"] = np.where(v & (df.discharge_date == df.admit_date), "Y", "N")
df["los_days"] = np.where(v & (df.status == "DISCHARGED"), (df.discharge_date - df.admit_date).dt.days, np.nan)
prev = df.discharge_date - pd.Timedelta(days=1)
occ_end = prev.where(prev >= df.admit_date, df.admit_date)
occ_end = occ_end.where(df.status != "ADMITTED", EXTRACT).where(v, pd.NaT)
df["occ_end_date"] = occ_end
df["bed_days"] = np.where(v, (occ_end - df.admit_date).dt.days + 1, np.nan)
df = df.merge(beds[["department_name", "department_id"]].rename(columns={"department_name": "department"}), on="department")
df = df.sort_values("admission_id").reset_index(drop=True)

# %% 5. Daily occupancy (department + hospital)
days = pd.date_range(WIN_START, EXTRACT); n = len(days); good = df[df.is_valid == "Y"]
rows = []
for _, b in beds.iterrows():
    x = good[good.department == b.department_name]
    s = (x.admit_date.clip(lower=WIN_START) - WIN_START).dt.days.values
    e = np.minimum((x.occ_end_date - WIN_START).dt.days.values, n - 1); ok = e >= 0
    arr = np.zeros(n + 1); np.add.at(arr, s[ok], 1); np.add.at(arr, e[ok] + 1, -1)
    rows.append(pd.DataFrame({"date": days, "department_id": b.department_id, "department_name": b.department_name,
                              "bed_capacity": b.bed_capacity, "occupied_beds": np.cumsum(arr)[:n].astype(int)}))
daily = pd.concat(rows, ignore_index=True); daily["occupancy_pct"] = (100 * daily.occupied_beds / daily.bed_capacity).round(1)
hosp = daily.groupby("date").agg(occupied_beds=("occupied_beds", "sum"), bed_capacity=("bed_capacity", "sum")).reset_index()
hosp["occupancy_pct"] = (100 * hosp.occupied_beds / hosp.bed_capacity).round(1)

# %% 6. Manual verification sample (20 patients)
comp = good[(good.status == "DISCHARGED") & (good.admit_date >= WIN_START)]
samp = pd.concat([comp[comp.same_day_flag == "Y"].sample(4, random_state=1), comp[comp.same_day_flag == "N"].sample(16, random_state=1)])
def los_independent(a, d): return (date.fromisoformat(d) - date.fromisoformat(a)).days   # plain-python cross-check
ver = samp[["admission_id", "patient_id", "department", "admit_date", "discharge_date", "los_days"]].copy()
ver["admit_date"] = ver.admit_date.dt.strftime("%Y-%m-%d"); ver["discharge_date"] = ver.discharge_date.dt.strftime("%Y-%m-%d")
ver["los_python_pipeline"] = ver.los_days.astype(int)
ver["los_independent_check"] = [los_independent(a, d) for a, d in zip(ver.admit_date, ver.discharge_date)]
def los_calendar_count(a, d):   # "manual" method: step through the calendar one day at a time
    x, n = date.fromisoformat(a), 0
    while x < date.fromisoformat(d): x += pd.Timedelta(days=1).to_pytimedelta(); n += 1
    return n
ver["los_manual_calendar_count"] = [los_calendar_count(a, d) for a, d in zip(ver.admit_date, ver.discharge_date)]
ver = ver.drop(columns="los_days")
assert (ver.los_python_pipeline == ver.los_independent_check).all() and (ver.los_python_pipeline == ver.los_manual_calendar_count).all(), "LOS mismatch!"

# %% 7. Write outputs
OUT.mkdir(exist_ok=True, parents=True)
fact = df[["admission_id", "patient_id", "department_id", "admit_date", "discharge_date", "age_at_admission", "los_days", "bed_days",
           "occ_end_date", "status", "same_day_flag", "dq_flag", "is_valid"]].copy()
for c in ["admit_date", "discharge_date", "occ_end_date"]: fact[c] = fact[c].dt.strftime("%Y-%m-%d")
for c in ["los_days", "bed_days", "age_at_admission"]: fact[c] = fact[c].astype("Int64")
fact.to_csv(OUT / "fact_admission.csv", index=False)
df.groupby("patient_id").gender.first().reset_index().to_csv(OUT / "dim_patient.csv", index=False)
beds[["department_id", "department_name", "bed_capacity"]].to_csv(OUT / "dim_department.csv", index=False)
daily.assign(date=daily.date.dt.strftime("%Y-%m-%d")).to_csv(OUT / "daily_occupancy.csv", index=False)
ver.to_csv(OUT / "los_verification_20.csv", index=False)
ids = ",".join(f"'{i}'" for i in ver.admission_id)
(ROOT / "sql/05_verify_los.sql").write_text(
    "-- Compare with data/processed/los_verification_20.csv (and your manual counts)\n"
    "SELECT admission_id, patient_id, admit_date, discharge_date,\n       discharge_date - admit_date AS los_days_sql, los_days AS los_days_stored\n"
    f"FROM fact_admission\nWHERE admission_id IN ({ids})\nORDER BY admission_id;\n")

# %% 8. Data-quality report
cnt = df.dq_flag.value_counts()
valid_done = df[(df.is_valid == "Y") & (df.status == "DISCHARGED")]
rep = f"""# Data Quality Report
Generated by `python/clean_data.py` from `data/raw/admissions_raw.csv`.

| Check | Count | Treatment |
|---|---:|---|
| Raw rows | {dq['raw_rows']:,} | - |
| Exact duplicate admission_id rows | {dq['duplicate_rows_removed']:,} | Removed (first kept) |
| Rows with non-ISO dates (DD/MM/YYYY or DD-Mon-YYYY) | {dq['non_iso_date_strings']:,} | Parsed with explicit formats |
| Unparseable dates | {dq['unparseable_dates']:,} | Row dropped |
| Department names standardised (ER, Ortho, case, spaces...) | {dq['department_names_standardised']:,} | Mapped to 8 canonical names |
| Unknown departments | {dq['unknown_departments']:,} | Row dropped |
| Missing age | {dq['missing_age']:,} | Kept (age not used in KPIs) |
| Rows after de-duplication | {len(df):,} | - |
| Still admitted (no discharge, admitted in last {ONGOING_DAYS} days) | {int((df.status=='ADMITTED').sum()):,} | Valid; occupy a bed until extract date {EXTRACT.date()} |
| **MISSING_DISCHARGE** (old stay, no discharge date) | {int(cnt.get('MISSING_DISCHARGE',0)):,} | Flagged, excluded from LOS and occupancy |
| **INVALID_DATES** (discharge before admit) | {int(cnt.get('INVALID_DATES',0)):,} | Flagged, excluded |
| **OVERLAP** (same patient, overlapping stays) | {int(cnt.get('OVERLAP',0)):,} | Later stay flagged, excluded |
| **Same-day discharge** (valid, LOS = 0) | {int((df.same_day_flag=='Y').sum()):,} | Kept; LOS 0, counts as 1 bed-day |
| Valid rows used for KPIs | {int((df.is_valid=='Y').sum()):,} ({100*(df.is_valid=='Y').mean():.1f}%) | - |

## LOS verification (20 patients)
`data/processed/los_verification_20.csv` holds 20 stays (4 same-day, 16 normal). The pipeline LOS equals an independent
plain-Python date subtraction AND a day-by-day calendar count (`los_manual_calendar_count`) for all 20 (asserted in the script).
`sql/05_verify_los.sql` shows the same 20 rows from Oracle (`discharge_date - admit_date`).
"""
(DOCS / "data_quality_report.md").write_text(rep)

# %% 9. Insights + dashboard preview
win = valid_done[valid_done.admit_date >= WIN_START]
los_dept = win.groupby("department").los_days.mean().round(2).sort_values(ascending=False)
occ_dept = (daily.groupby("department_name").occupied_beds.sum() / daily.groupby("department_name").bed_capacity.sum() * 100).round(1).sort_values(ascending=False)
hosp["month"] = hosp.date.dt.to_period("M").astype(str)
mon = hosp.groupby("month")[["occupied_beds", "bed_capacity"]].sum(); mon = (100 * mon.occupied_beds / mon.bed_capacity).round(1)
peak = hosp.sort_values("occupancy_pct", ascending=False).head(10)
overall = round(100 * hosp.occupied_beds.sum() / hosp.bed_capacity.sum(), 1)
d90 = int((hosp.occupancy_pct >= 90).sum()); dept100 = daily[daily.occupancy_pct > 100].groupby("department_name").size().sort_values(ascending=False)
wk = hosp.assign(w=hosp.date.dt.dayofweek >= 5).groupby("w").occupancy_pct.mean().round(1)
sd_rate = round(100 * (win.same_day_flag == "Y").mean(), 1)
sd_dept = (win.assign(s=win.same_day_flag == "Y").groupby("department").s.mean() * 100).round(1).sort_values(ascending=False)
ins = f"""# Insights Summary  (window {WIN_START.date()} to {EXTRACT.date()}; synthetic data)
- **Overall average LOS:** {win.los_days.mean():.2f} days (completed valid stays). Longest: {los_dept.index[0]} ({los_dept.iloc[0]} d); shortest: {los_dept.index[-1]} ({los_dept.iloc[-1]} d).
- **Overall bed occupancy:** {overall}%. Highest department: {occ_dept.index[0]} ({occ_dept.iloc[0]}%); lowest: {occ_dept.index[-1]} ({occ_dept.iloc[-1]}%).
- **Peak load:** {d90} days had hospital-wide occupancy >= 90%. Top 10 peak days: {', '.join(f"{d:%d %b %Y} ({p}%)" for d, p in zip(peak.date, peak.occupancy_pct))}.
- **Seasonality:** busiest month {mon.idxmax()} ({mon.max()}%), quietest {mon.idxmin()} ({mon.min()}%).
- **Weekday vs weekend:** weekdays {wk[False]}% vs weekends {wk[True]}% average occupancy.
- **Departments over capacity (>100% on at least one day):** {', '.join(f'{k} ({x} days)' for k, x in dept100.items()) or 'none'}.
- **Same-day discharge:** {sd_rate}% of stays overall; highest in {sd_dept.index[0]} ({sd_dept.iloc[0]}%).
- **Data quality:** {100*(df.is_valid=='Y').mean():.1f}% of de-duplicated rows were valid; see data_quality_report.md.

## Recommendations
1. Plan extra staffed beds for Jan-Feb, where the peak-load days cluster.
2. Review discharge planning in the longest-LOS department to free beds.
3. Fix source-system entry: mandatory discharge date, controlled department list, date validation.
"""
(DOCS / "insights_summary.md").write_text(ins)

fig, ax = plt.subplots(1, 3, figsize=(18, 4.6))
ax[0].plot(mon.index, mon.values, marker="o"); ax[0].axhline(90, ls="--", c="r", lw=1)
ax[0].set_title("Monthly hospital occupancy %"); ax[0].tick_params(axis="x", rotation=60)
ax[1].barh(occ_dept.index[::-1], occ_dept.values[::-1]); ax[1].set_title("Occupancy % by department")
ax[2].barh([f"{d:%d %b %y}" for d in peak.date][::-1], peak.occupancy_pct.values[::-1]); ax[2].set_title("Top 10 peak-load days (hospital)")
plt.tight_layout(); plt.savefig(DOCS / "dashboard_preview.png", dpi=110)
print(rep.split("## LOS")[0]); print(ins)
