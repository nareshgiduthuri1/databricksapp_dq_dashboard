CREATE TABLE hub_person
(
  person_hash_key STRING NOT NULL,
  person_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_person
ADD CONSTRAINT XPKHUB_PERSON PRIMARY KEY (person_hash_key);
