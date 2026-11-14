CREATE TABLE hub_insured_entity
(
  insured_entity_hash_key STRING NOT NULL,
  insured_entity_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_insured_entity
ADD CONSTRAINT XPKHUB_INSURED_ENTITY PRIMARY KEY (insured_entity_hash_key);
