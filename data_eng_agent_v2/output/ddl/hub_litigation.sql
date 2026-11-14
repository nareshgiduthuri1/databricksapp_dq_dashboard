CREATE TABLE hub_litigation
(
  litigation_hash_key STRING NOT NULL,
  litigation_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_litigation
ADD CONSTRAINT XPKHUB_LITIGATION PRIMARY KEY (litigation_hash_key);
