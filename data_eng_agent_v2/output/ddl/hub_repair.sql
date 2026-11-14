CREATE TABLE hub_repair
(
  repair_hash_key STRING NOT NULL,
  repair_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_repair
ADD CONSTRAINT XPKHUB_REPAIR PRIMARY KEY (repair_hash_key);
