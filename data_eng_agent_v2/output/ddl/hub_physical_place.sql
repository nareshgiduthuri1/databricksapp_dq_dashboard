CREATE TABLE hub_physical_place
(
  physical_place_hash_key STRING NOT NULL,
  physical_place_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_physical_place
ADD CONSTRAINT XPKHUB_PHYSICAL_PLACE PRIMARY KEY (physical_place_hash_key);
