CREATE TABLE hub_claim_event
(
  claim_event_hash_key STRING NOT NULL,
  claim_event_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_claim_event
ADD CONSTRAINT XPKHUB_CLAIM_EVENT PRIMARY KEY (claim_event_hash_key);
