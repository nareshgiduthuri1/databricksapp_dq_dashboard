CREATE TABLE hub_settlement
(
  settlement_hash_key STRING NOT NULL,
  settlement_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_settlement
ADD CONSTRAINT XPKHUB_SETTLEMENT PRIMARY KEY (settlement_hash_key);
