CREATE TABLE link_claim_event_repair
(
  claim_event_repair_hash_key STRING NOT NULL,
  claim_event_hash_key STRING,
  repair_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_claim_event_repair
ADD CONSTRAINT XPKLINK_CLAIM_EVENT_REPAIR PRIMARY KEY (claim_event_repair_hash_key);

ALTER TABLE link_claim_event_repair
ADD CONSTRAINT FK_LINK_CLAIM_EVENT_REPAIR__CRM_CLAIM_EVENT_LOG_CSV
FOREIGN KEY (claim_event_hash_key)
REFERENCES crm_claim_event_log_csv (claim_event_identifier_source_name);

ALTER TABLE link_claim_event_repair
ADD CONSTRAINT FK_LINK_CLAIM_EVENT_REPAIR__CRM_REPAIR_REGISTER_CSV
FOREIGN KEY (repair_hash_key)
REFERENCES crm_repair_register_csv (repair_identifier_source_name);
