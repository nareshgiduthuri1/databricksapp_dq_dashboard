CREATE TABLE link_claim_event_settlement
(
  claim_event_settlement_hash_key STRING NOT NULL,
  claim_event_hash_key STRING,
  settlement_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_claim_event_settlement
ADD CONSTRAINT XPKLINK_CLAIM_EVENT_SETTLEMENT PRIMARY KEY (claim_event_settlement_hash_key);

ALTER TABLE link_claim_event_settlement
ADD CONSTRAINT FK_LINK_CLAIM_EVENT_SETTLEMENT__CRM_CLAIM_EVENT_LOG_CSV
FOREIGN KEY (claim_event_hash_key)
REFERENCES crm_claim_event_log_csv (claim_event_identifier_source_name);

ALTER TABLE link_claim_event_settlement
ADD CONSTRAINT FK_LINK_CLAIM_EVENT_SETTLEMENT__CRM_SETTLEMENT_REGISTER_CSV
FOREIGN KEY (settlement_hash_key)
REFERENCES crm_settlement_register_csv (settlement_identifier_source_name);
