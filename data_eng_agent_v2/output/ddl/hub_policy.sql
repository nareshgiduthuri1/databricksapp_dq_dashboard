CREATE TABLE hub_policy
(
  policy_hash_key STRING NOT NULL,
  policy_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_policy
ADD CONSTRAINT XPKHUB_POLICY PRIMARY KEY (policy_hash_key);
