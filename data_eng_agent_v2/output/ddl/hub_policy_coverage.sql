CREATE TABLE hub_policy_coverage
(
  policy_coverage_hash_key STRING NOT NULL,
  policy_coverage_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_policy_coverage
ADD CONSTRAINT XPKHUB_POLICY_COVERAGE PRIMARY KEY (policy_coverage_hash_key);
