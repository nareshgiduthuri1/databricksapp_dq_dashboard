CREATE TABLE link_claim_police_report
(
  claim_police_report_hash_key STRING NOT NULL,
  claim_hash_key STRING,
  police_report_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
)
USING DELTA;

ALTER TABLE link_claim_police_report
ADD CONSTRAINT XPKLINK_CLAIM_POLICE_REPORT PRIMARY KEY (claim_police_report_hash_key);

ALTER TABLE link_claim_police_report
ADD CONSTRAINT FK_LINK_CLAIM_POLICE_REPORT__CRM_CLAIM_REGISTER_CSV_SAP_CLAIM_DB
FOREIGN KEY (claim_hash_key)
REFERENCES crm_claim_register_csv_sap_claim_db (claim_identifier_source_name_claim_ref_id_source_name);

ALTER TABLE link_claim_police_report
ADD CONSTRAINT FK_LINK_CLAIM_POLICE_REPORT__CRM_POLICE_REPORT_REGISTER_CSV
FOREIGN KEY (police_report_hash_key)
REFERENCES crm_police_report_register_csv (police_report_identifier_source_name);
