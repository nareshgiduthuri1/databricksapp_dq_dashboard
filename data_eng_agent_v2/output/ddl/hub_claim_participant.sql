CREATE TABLE hub_claim_participant
(
  claim_participant_hash_key STRING NOT NULL,
  claim_participant_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_claim_participant
ADD CONSTRAINT XPKHUB_CLAIM_PARTICIPANT PRIMARY KEY (claim_participant_hash_key);
