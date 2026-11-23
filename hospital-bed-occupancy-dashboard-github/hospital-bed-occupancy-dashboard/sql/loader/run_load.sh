#!/bin/bash
# Usage: ./run_load.sh user/password@//host:1521/service   (run from sql/loader). Load order matters (FKs).
CONN="$1"
sqlldr "$CONN" control=dim_department.ctl log=dim_department.log
sqlldr "$CONN" control=dim_patient.ctl    log=dim_patient.log
sqlldr "$CONN" control=fact_admission.ctl log=fact_admission.log
