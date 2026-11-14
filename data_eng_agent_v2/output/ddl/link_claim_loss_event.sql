CREATE TABLE link_claim_loss_event
(
  claim_loss_event_hash_key STRING NOT NULL,
  claim_hash_key STRING,
  loss_event_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_claim_loss_event
ADD CONSTRAINT XPKLINK_CLAIM_LOSS_EVENT PRIMARY KEY (claim_loss_event_hash_key);

ALTER TABLE link_claim_loss_event
ADD CONSTRAINT FK_LINK_CLAIM_LOSS_EVENT__CRM_CLAIM_REGISTER_CSV_SAP_CLAIM_DB
FOREIGN KEY (claim_hash_key)
REFERENCES crm_claim_register_csv_sap_claim_db (claim_identifier_source_name_claim_ref_id_source_name);

ALTER TABLE link_claim_loss_event
ADD CONSTRAINT FK_LINK_CLAIM_LOSS_EVENT__CRM_LOSS_EVENT_REGISTER_CSV_SAP_LOSS_EVENT_DB
FOREIGN KEY (loss_event_hash_key)
REFERENCES crm_loss_event_register_csv_sap_loss_event_db (loss_event_identifier_source_name_incident_id_source_name);
