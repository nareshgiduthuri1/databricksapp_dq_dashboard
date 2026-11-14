CREATE TABLE hub_catastrophe
(
  catastrophe_hash_key STRING NOT NULL,
  catastrophe_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_catastrophe
ADD CONSTRAINT XPKHUB_CATASTROPHE PRIMARY KEY (catastrophe_hash_key);
