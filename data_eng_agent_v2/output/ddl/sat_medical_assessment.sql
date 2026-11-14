CREATE TABLE sat_medical_assessment
(
  medical_assessment_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  assessed_disability_degree DOUBLE,
  permanent_disability_degree DOUBLE,
  permanent_disability_flag STRING,
  medical_report_flag STRING,
  medical_report_date DATE,
  person_hospital_status STRING,
  psychological_factors STRING,
  medical_condition_description STRING
);

ALTER TABLE sat_medical_assessment
ADD CONSTRAINT XPKSAT_MEDICAL_ASSESSMENT PRIMARY KEY (medical_assessment_hash_key, load_ts);

ALTER TABLE sat_medical_assessment
ADD CONSTRAINT FK_sat_medical_assessment__crm_medical_assessment_register_csv
FOREIGN KEY (medical_assessment_hash_key)
REFERENCES crm_medical_assessment_register_csv (medical_assessment_identifier);
