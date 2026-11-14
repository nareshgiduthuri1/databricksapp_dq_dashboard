CREATE TABLE link_claim_litigation
(
  claim_litigation_hash_key STRING NOT NULL,
  claim_hash_key STRING,
  litigation_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
)
USING DELTA;

ALTER TABLE link_claim_litigation
ADD CONSTRAINT XPKLINK_CLAIM_LITIGATION PRIMARY KEY (claim_litigation_hash_key);

ALTER TABLE link_claim_litigation
ADD CONSTRAINT FK_LINK_CLAIM_LITIGATION__CRM_CLAIM_REGISTER_CSV_SAP_CLAIM_DB
FOREIGN KEY (claim_hash_key)
REFERENCES crm_claim_register_csv_sap_claim_db (claim_identifier_source_name_claim_ref_id_source_name);

ALTER TABLE link_claim_litigation
ADD CONSTRAINT FK_LINK_CLAIM_LITIGATION__CRM_LITIGATION_REGISTER_CSV
FOREIGN KEY (litigation_hash_key)
REFERENCES crm_litigation_register_csv (litigation_identifier_source_name);
