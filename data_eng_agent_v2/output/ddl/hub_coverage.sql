CREATE TABLE hub_coverage
(
  coverage_hash_key STRING NOT NULL,
  coverage_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_coverage
ADD CONSTRAINT XPKHUB_COVERAGE PRIMARY KEY (coverage_hash_key);
