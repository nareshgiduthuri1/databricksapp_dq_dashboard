CREATE TABLE sat_medical_report
(
  medical_report_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  document_id STRING,
  health_declaration STRING
);

ALTER TABLE sat_medical_report
ADD CONSTRAINT XPKSAT_MEDICAL_REPORT PRIMARY KEY (medical_report_hash_key, load_ts);

ALTER TABLE sat_medical_report
ADD CONSTRAINT FK_SAT_MEDICAL_REPORT__CRM_MEDICAL_REPORT_REGISTER_CSV
FOREIGN KEY (medical_report_hash_key)
REFERENCES crm_medical_report_register_csv (medical_report_identifier_source_name);
