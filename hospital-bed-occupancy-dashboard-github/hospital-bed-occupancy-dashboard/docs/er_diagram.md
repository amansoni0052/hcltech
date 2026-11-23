# Star Schema (ER Diagram)
```mermaid
erDiagram
    DIM_PATIENT    ||--o{ FACT_ADMISSION : "has"
    DIM_DEPARTMENT ||--o{ FACT_ADMISSION : "treats"
    DIM_DEPARTMENT ||--o{ VW_DAILY_DEPT_OCCUPANCY : "capacity"
    DIM_DATE       ||--o{ VW_DAILY_DEPT_OCCUPANCY : "calendar"
    DIM_PATIENT { varchar patient_id PK
                  char gender }
    DIM_DEPARTMENT { number department_id PK
                     varchar department_name
                     number bed_capacity }
    DIM_DATE { date date_key PK
               number year_num
               number month_num
               date month_start
               varchar day_name
               char is_weekend }
    FACT_ADMISSION { varchar admission_id PK
                     varchar patient_id FK
                     number department_id FK
                     date admit_date
                     date discharge_date
                     number los_days
                     number bed_days
                     date occ_end_date
                     varchar status
                     char same_day_flag
                     varchar dq_flag
                     char is_valid }
    VW_DAILY_DEPT_OCCUPANCY { date date_key
                              number department_id
                              number occupied_beds
                              number occupancy_pct }
```
**Why a daily view?** Occupancy is a per-day measure, but admissions are per-stay. The view expands each stay across the dates it
occupies a bed (`date BETWEEN admit_date AND occ_end_date`) so occupancy can be sliced by department, month, and day.
