CREATE TABLE hub_diagnosis
(
  diagnosis_hash_key STRING NOT NULL,
  diagnosis_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_diagnosis
ADD CONSTRAINT XPKHUB_DIAGNOSIS PRIMARY KEY (diagnosis_hash_key);
