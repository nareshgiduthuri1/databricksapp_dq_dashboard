CREATE TABLE link_claim_medical_report
(
  claim_medical_report_hash_key STRING NOT NULL,
  claim_hash_key STRING,
  medical_report_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_claim_medical_report
ADD CONSTRAINT XPKLINK_CLAIM_MEDICAL_REPORT PRIMARY KEY (claim_medical_report_hash_key);

ALTER TABLE link_claim_medical_report
ADD CONSTRAINT FK_LINK_CLAIM_MEDICAL_REPORT__CRM_CLAIM_REGISTER_CSV_SAP_CLAIM_DB
FOREIGN KEY (claim_hash_key)
REFERENCES crm_claim_register_csv_sap_claim_db (claim_identifier_source_name_claim_ref_id_source_name);

ALTER TABLE link_claim_medical_report
ADD CONSTRAINT FK_LINK_CLAIM_MEDICAL_REPORT__CRM_MEDICAL_REPORT_REGISTER_CSV
FOREIGN KEY (medical_report_hash_key)
REFERENCES crm_medical_report_register_csv (medical_report_identifier_source_name);
