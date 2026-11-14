CREATE TABLE hub_health_insurance_claim
(
  health_insurance_claim_hash_key STRING NOT NULL,
  health_insurance_claim_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_health_insurance_claim
ADD CONSTRAINT XPKHUB_HEALTH_INSURANCE_CLAIM PRIMARY KEY (health_insurance_claim_hash_key);
