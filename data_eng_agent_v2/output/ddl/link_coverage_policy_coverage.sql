CREATE TABLE link_coverage_policy_coverage
(
  coverage_policy_coverage_hash_key STRING NOT NULL,
  coverage_hash_key STRING,
  policy_coverage_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_coverage_policy_coverage
ADD CONSTRAINT XPKLINK_COVERAGE_POLICY_COVERAGE PRIMARY KEY (coverage_policy_coverage_hash_key);

ALTER TABLE link_coverage_policy_coverage
ADD CONSTRAINT FK_LINK_COVERAGE_POLICY_COVERAGE__CRM_COVERAGE_CATALOG_CSV
FOREIGN KEY (coverage_hash_key)
REFERENCES crm_coverage_catalog_csv (coverage_identifier_source_name);

ALTER TABLE link_coverage_policy_coverage
ADD CONSTRAINT FK_LINK_COVERAGE_POLICY_COVERAGE__CRM_POLICY_COVERAGE_REGISTER_CSV
FOREIGN KEY (policy_coverage_hash_key)
REFERENCES crm_policy_coverage_register_csv (policy_coverage_identifier_source_name);
