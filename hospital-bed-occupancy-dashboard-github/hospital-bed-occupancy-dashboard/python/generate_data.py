"""Generate a synthetic (but realistic) hospital admissions dataset with deliberate data-quality problems.
Run:  python python/generate_data.py
Output: data/raw/admissions_raw.csv, data/raw/department_beds.csv
Injected problems: mixed date formats, department spelling variants, missing discharge dates,
discharge-before-admit (swapped dates), duplicate rows, overlapping stays, missing ages.
Same-day discharges occur naturally (esp. Emergency)."""
import numpy as np, pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
ROOT = Path(__file__).resolve().parents[1]
DEPTS = {  # name: (bed_capacity, mean_LOS_days)
    "Emergency": (30, 1.5), "General Medicine": (60, 4.5), "Surgery": (45, 4.0),
    "Orthopedics": (30, 5.0), "Cardiology": (35, 4.0), "Pediatrics": (25, 3.0),
    "Maternity": (25, 2.5), "ICU": (20, 5.0),
}
START, EXTRACT = pd.Timestamp("2023-12-10"), pd.Timestamp("2025-06-30")  # 3 weeks warm-up before analysis window
N_PAT = 30000
pat_gender = rng.choice(["M", "F"], N_PAT)
fem_ids = np.where(pat_gender == "F")[0]

recs = []
for d in pd.date_range(START, EXTRACT):
    m = 1.0
    if d.month in (12, 1, 2): m *= 1.18           # winter surge
    if d.dayofweek >= 5: m *= 0.85                # weekends quieter
    for dept, (cap, mlos) in DEPTS.items():
        dm = m * (1.2 if (dept == "Emergency" and d.dayofweek == 0) else 1.0)
        for _ in range(rng.poisson(cap * 0.80 / mlos * dm)):
            los = int(rng.gamma(2.0, mlos / 2.0))
            p = rng.choice(fem_ids) if dept == "Maternity" else rng.integers(0, N_PAT)
            if dept == "Pediatrics": age = int(rng.integers(0, 15))
            elif dept == "Maternity": age = int(rng.integers(18, 43))
            else: age = int(np.clip(rng.normal(55, 20), 18, 95))
            dis = d + pd.Timedelta(days=los)
            recs.append((dept, f"P{p+1:05d}", pat_gender[p], d, dis if dis <= EXTRACT else pd.NaT, age))

df = pd.DataFrame(recs, columns=["department", "patient_id", "gender", "admit_date", "discharge_date", "age_at_admission"])
df.insert(0, "admission_id", [f"A{i+1:06d}" for i in range(len(df))])

# --- inject problems ---
done = df[df.discharge_date.notna()]
ov = done[(done.discharge_date - done.admit_date).dt.days >= 3].sample(100, random_state=1).copy()
ov["admission_id"] = [f"A{len(df)+i+1:06d}" for i in range(len(ov))]
ov["admit_date"] += pd.Timedelta(days=1); ov["discharge_date"] += pd.Timedelta(days=2)
ov["discharge_date"] = ov.discharge_date.where(ov.discharge_date <= EXTRACT, pd.NaT)
df = pd.concat([df, ov], ignore_index=True)
cand = df[df.discharge_date.notna() & (df.admit_date < EXTRACT - pd.Timedelta(days=60))].sample(frac=0.015, random_state=2).index
df.loc[cand, "discharge_date"] = pd.NaT
cand = df[df.discharge_date.notna() & (df.discharge_date > df.admit_date)].sample(frac=0.008, random_state=3).index
df.loc[cand, ["admit_date", "discharge_date"]] = df.loc[cand, ["discharge_date", "admit_date"]].values
df.loc[df.sample(frac=0.02, random_state=4).index, "age_at_admission"] = np.nan
def fmt(series):
    out = []
    for v in series:
        if pd.isna(v): out.append(""); continue
        r = rng.random()
        out.append(v.strftime("%Y-%m-%d") if r < 0.90 else v.strftime("%d/%m/%Y") if r < 0.97 else v.strftime("%d-%b-%Y"))
    return out
df["admit_date"], df["discharge_date"] = fmt(df.admit_date), fmt(df.discharge_date)
variants = {"Emergency": ["ER", "emergency"], "General Medicine": ["Gen Med", "GENERAL MEDICINE"], "Surgery": ["surgery "],
            "Orthopedics": ["Ortho", "orthopedics"], "Cardiology": ["Cardio", "CARDIOLOGY"], "Pediatrics": ["Peds"],
            "Maternity": ["maternity"], "ICU": ["icu"]}
for i in df.sample(frac=0.04, random_state=5).index:
    df.at[i, "department"] = rng.choice(variants[df.at[i, "department"]])
df = pd.concat([df, df.sample(frac=0.005, random_state=6)], ignore_index=True)
df = df.sample(frac=1, random_state=7).reset_index(drop=True)

(ROOT / "data/raw").mkdir(parents=True, exist_ok=True)
df.to_csv(ROOT / "data/raw/admissions_raw.csv", index=False)
pd.DataFrame([(k, v[0]) for k, v in DEPTS.items()], columns=["department_name", "bed_capacity"]).to_csv(ROOT / "data/raw/department_beds.csv", index=False)
print(f"Generated {len(df):,} raw rows")
