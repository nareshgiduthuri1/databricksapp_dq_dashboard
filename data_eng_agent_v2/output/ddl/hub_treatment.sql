CREATE TABLE hub_treatment
(
  treatment_hash_key STRING NOT NULL,
  treatment_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_treatment
ADD CONSTRAINT XPKHUB_TREATMENT PRIMARY KEY (treatment_hash_key);
