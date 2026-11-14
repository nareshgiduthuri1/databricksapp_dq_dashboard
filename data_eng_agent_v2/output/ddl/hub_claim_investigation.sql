CREATE TABLE hub_claim_investigation
(
  claim_investigation_hash_key STRING NOT NULL,
  claim_investigation_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_claim_investigation
ADD CONSTRAINT XPKHUB_CLAIM_INVESTIGATION PRIMARY KEY (claim_investigation_hash_key);
