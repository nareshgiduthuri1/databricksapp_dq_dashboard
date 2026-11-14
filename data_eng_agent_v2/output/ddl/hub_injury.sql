CREATE TABLE hub_injury
(
  injury_hash_key STRING NOT NULL,
  injury_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_injury
ADD CONSTRAINT XPKHUB_INJURY PRIMARY KEY (injury_hash_key);
