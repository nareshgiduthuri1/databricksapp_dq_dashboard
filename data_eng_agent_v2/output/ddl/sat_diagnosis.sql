CREATE TABLE sat_diagnosis
(
  diagnosis_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  diagnosis_code STRING,
  diagnosis_description STRING,
  diagnosis_priority BIGINT,
  diagnosis_standard STRING
)
USING DELTA;

ALTER TABLE sat_diagnosis
ADD CONSTRAINT XPKSAT_DIAGNOSIS PRIMARY KEY (diagnosis_hash_key, load_ts);

ALTER TABLE sat_diagnosis
ADD CONSTRAINT FK_SAT_DIAGNOSIS__CRM_DIAGNOSIS_REGISTER_CSV
FOREIGN KEY (diagnosis_hash_key)
REFERENCES crm_diagnosis_register_csv (diagnosis_identifier_source_name);
