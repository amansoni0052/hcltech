# Problem Statement & KPI Definitions

## Problem
Hospital managers cannot easily see how full the hospital is, how long patients stay, or which days/departments are under
pressure. Raw admission records are messy (mixed date formats, missing discharge dates, overlapping stays), so even basic
numbers like "average length of stay" are unreliable. This project cleans the data, models it, and delivers a dashboard
that answers: **How long do patients stay? How full are our beds? When are we overloaded?**

## Scope
Source: hospital admissions extract (synthetic here; 8 departments, 270 beds). Analysis window 2024-01-01 to 2025-06-30.

## KPI definitions
| KPI | Definition |
|---|---|
| Length of Stay (LOS) | `discharge_date - admit_date` in days. Same-day discharge = 0 days. |
| Average LOS | Mean LOS of valid, completed (discharged) stays. |
| Bed-day | One bed occupied for one calendar date. Stay occupies dates `admit .. discharge-1`; same-day stay = 1 bed-day (admit date). |
| Occupied beds (day, dept) | Count of valid stays occupying a bed on that date. |
| Occupancy % | Occupied bed-days / Available bed-days (capacity x days). |
| Peak-load day | Hospital occupancy >= 90% (threshold is adjustable). Top-10 days also reported. |
| Same-day discharge % | Same-day stays / completed valid stays. |

## Edge-case rules
| Case | Rule |
|---|---|
| Same-day discharge | Valid. LOS = 0, counts as 1 bed-day. |
| Missing discharge date | Admitted in last 30 days of extract -> **ADMITTED**, occupies bed until extract date. Older -> **MISSING_DISCHARGE**, excluded and reported. |
| Discharge before admit | **INVALID_DATES**, excluded. |
| Overlapping stays (same patient) | Later stay flagged **OVERLAP**, excluded. Admit date = previous discharge date is a valid transfer. |
| Duplicates / department typos / mixed date formats | De-duplicated / mapped to canonical names / parsed explicitly (slash dates = DD/MM/YYYY). |
