-- Compare with data/processed/los_verification_20.csv (and your manual counts)
SELECT admission_id, patient_id, admit_date, discharge_date,
       discharge_date - admit_date AS los_days_sql, los_days AS los_days_stored
FROM fact_admission
WHERE admission_id IN ('A004623','A020776','A035072','A020167','A032556','A006686','A013295','A026591','A019275','A015601','A024882','A011689','A007797','A006412','A022163','A001708','A037122','A004904','A026887','A003410')
ORDER BY admission_id;
