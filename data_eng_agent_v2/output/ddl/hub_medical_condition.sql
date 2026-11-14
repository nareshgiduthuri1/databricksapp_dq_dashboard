CREATE TABLE hub_medical_condition
(
  medical_condition_hash_key STRING NOT NULL,
  medical_condition_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_medical_condition
ADD CONSTRAINT XPKHUB_MEDICAL_CONDITION PRIMARY KEY (medical_condition_hash_key);
