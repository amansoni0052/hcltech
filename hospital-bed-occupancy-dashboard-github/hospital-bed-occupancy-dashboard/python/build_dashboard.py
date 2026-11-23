"""Build dashboard/index.html (self-contained, no internet needed) from data/processed/*.csv.
Run:  python python/build_dashboard.py   then open dashboard/index.html in any browser."""
import json, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; P = ROOT / "data/processed"
daily = pd.read_csv(P / "daily_occupancy.csv"); dep = pd.read_csv(P / "dim_department.csv")
fact = pd.read_csv(P / "fact_admission.csv", parse_dates=["admit_date"])
depts = [{"n": r.department_name, "cap": int(r.bed_capacity),
          "occ": daily[daily.department_id == r.department_id].sort_values("date").occupied_beds.tolist()} for r in dep.itertuples()]
f = fact[(fact.is_valid == "Y") & (fact.status == "DISCHARGED") & (fact.admit_date >= "2024-01-01")].copy()
f["m"] = f.admit_date.dt.strftime("%Y-%m"); f["sd"] = (f.same_day_flag == "Y").astype(int)
los = {f"{int(d)-1}|{m}": [int(g.los_days.sum()), len(g), int(g.sd.sum())] for (d, m), g in f.groupby(["department_id", "m"])}
data = {"start": str(daily.date.min()), "depts": depts, "los": los}
html = (ROOT / "dashboard/template.html").read_text().replace("__DATA__", json.dumps(data, separators=(",", ":")))
(ROOT / "dashboard/index.html").write_text(html); print("dashboard/index.html", round(len(html) / 1024), "KB")
