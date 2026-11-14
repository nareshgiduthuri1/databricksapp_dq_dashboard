CREATE TABLE sat_medical_condition
(
  medical_condition_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  disease_name STRING,
  disability_status STRING,
  pre_existing_condition STRING
);

ALTER TABLE sat_medical_condition
ADD CONSTRAINT XPKSAT_MEDICAL_CONDITION PRIMARY KEY (medical_condition_hash_key, load_ts);

ALTER TABLE sat_medical_condition
ADD CONSTRAINT FK_SAT_MEDICAL_CONDITION__CRM_MEDICAL_CONDITION_CATALOG_CSV
FOREIGN KEY (medical_condition_hash_key)
REFERENCES crm_medical_condition_catalog_csv (medical_condition_identifier_source_name);
