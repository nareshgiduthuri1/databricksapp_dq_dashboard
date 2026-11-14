CREATE TABLE link_policy_policy_coverage
(
  policy_policy_coverage_hash_key STRING NOT NULL,
  policy_hash_key STRING,
  policy_coverage_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_policy_policy_coverage
ADD CONSTRAINT XPKLINK_POLICY_POLICY_COVERAGE PRIMARY KEY (policy_policy_coverage_hash_key);

ALTER TABLE link_policy_policy_coverage
ADD CONSTRAINT FK_LINK_POLICY_POLICY_COVERAGE__CRM_POLICY_REGISTER_CSV
FOREIGN KEY (policy_hash_key)
REFERENCES crm_policy_register_csv (policy_identifier_source_name);

ALTER TABLE link_policy_policy_coverage
ADD CONSTRAINT FK_LINK_POLICY_POLICY_COVERAGE__CRM_POLICY_COVERAGE_REGISTER_CSV
FOREIGN KEY (policy_coverage_hash_key)
REFERENCES crm_policy_coverage_register_csv (policy_coverage_identifier_source_name);
