CREATE TABLE link_policy_claim
(
  policy_claim_hash_key STRING NOT NULL,
  policy_hash_key STRING,
  claim_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_policy_claim
ADD CONSTRAINT XPKLINK_POLICY_CLAIM PRIMARY KEY (policy_claim_hash_key);

ALTER TABLE link_policy_claim
ADD CONSTRAINT FK_LINK_POLICY_CLAIM__CRM_POLICY_REGISTER_CSV
FOREIGN KEY (policy_hash_key)
REFERENCES crm_policy_register_csv (policy_identifier_source_name);

ALTER TABLE link_policy_claim
ADD CONSTRAINT FK_LINK_POLICY_CLAIM__CRM_CLAIM_REGISTER_CSV_SAP_CLAIM_DB
FOREIGN KEY (claim_hash_key)
REFERENCES crm_claim_register_csv_sap_claim_db (claim_identifier_source_name_claim_ref_id_source_name);
