CREATE TABLE hub_medical_assessment
(
  medical_assessment_hash_key STRING NOT NULL,
  medical_assessment_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_medical_assessment
ADD CONSTRAINT XPKHUB_MEDICAL_ASSESSMENT PRIMARY KEY (medical_assessment_hash_key);
