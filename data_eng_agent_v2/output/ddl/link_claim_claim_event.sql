CREATE TABLE link_claim_claim_event
(
  claim_claim_event_hash_key STRING NOT NULL,
  claim_hash_key STRING,
  claim_event_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_claim_claim_event
ADD CONSTRAINT XPKLINK_CLAIM_CLAIM_EVENT PRIMARY KEY (claim_claim_event_hash_key);

ALTER TABLE link_claim_claim_event
ADD CONSTRAINT FK_LINK_CLAIM_CLAIM_EVENT__CRM_CLAIM_REGISTER_CSV_SAP_CLAIM_DB
FOREIGN KEY (claim_hash_key)
REFERENCES crm_claim_register_csv_sap_claim_db (claim_identifier_source_name_claim_ref_id_source_name);

ALTER TABLE link_claim_claim_event
ADD CONSTRAINT FK_LINK_CLAIM_CLAIM_EVENT__CRM_CLAIM_EVENT_LOG_CSV
FOREIGN KEY (claim_event_hash_key)
REFERENCES crm_claim_event_log_csv (claim_event_identifier_source_name);
