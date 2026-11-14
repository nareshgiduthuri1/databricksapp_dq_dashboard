CREATE TABLE link_claim_event_litigation
(
  claim_event_litigation_hash_key STRING NOT NULL,
  claim_event_hash_key STRING,
  litigation_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_claim_event_litigation
ADD CONSTRAINT XPKLINK_CLAIM_EVENT_LITIGATION PRIMARY KEY (claim_event_litigation_hash_key);

ALTER TABLE link_claim_event_litigation
ADD CONSTRAINT FK_LINK_CLAIM_EVENT_LITIGATION__CRM_CLAIM_EVENT_LOG_CSV
FOREIGN KEY (claim_event_hash_key)
REFERENCES crm_claim_event_log_csv (claim_event_identifier_source_name);

ALTER TABLE link_claim_event_litigation
ADD CONSTRAINT FK_LINK_CLAIM_EVENT_LITIGATION__CRM_LITIGATION_REGISTER_CSV
FOREIGN KEY (litigation_hash_key)
REFERENCES crm_litigation_register_csv (litigation_identifier_source_name);
