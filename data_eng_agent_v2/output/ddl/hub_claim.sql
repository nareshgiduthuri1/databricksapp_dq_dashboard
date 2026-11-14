CREATE TABLE hub_claim
(
  claim_hash_key STRING NOT NULL,
  claim_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_claim
ADD CONSTRAINT XPKHUB_CLAIM PRIMARY KEY (claim_hash_key);
