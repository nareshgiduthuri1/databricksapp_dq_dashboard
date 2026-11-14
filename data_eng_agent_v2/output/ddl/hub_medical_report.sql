CREATE TABLE hub_medical_report
(
  medical_report_hash_key STRING NOT NULL,
  medical_report_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_medical_report
ADD CONSTRAINT XPKHUB_MEDICAL_REPORT PRIMARY KEY (medical_report_hash_key);
