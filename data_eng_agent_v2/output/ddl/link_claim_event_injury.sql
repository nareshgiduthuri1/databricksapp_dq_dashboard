CREATE TABLE link_claim_event_injury
(
  claim_event_injury_hash_key STRING NOT NULL,
  claim_event_hash_key STRING,
  injury_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_claim_event_injury
ADD CONSTRAINT XPKLINK_CLAIM_EVENT_INJURY PRIMARY KEY (claim_event_injury_hash_key);

ALTER TABLE link_claim_event_injury
ADD CONSTRAINT FK_LINK_CLAIM_EVENT_INJURY__CRM_CLAIM_EVENT_LOG_CSV
FOREIGN KEY (claim_event_hash_key)
REFERENCES crm_claim_event_log_csv (claim_event_identifier_source_name);

ALTER TABLE link_claim_event_injury
ADD CONSTRAINT FK_LINK_CLAIM_EVENT_INJURY__CRM_INJURY_REGISTER_CSV
FOREIGN KEY (injury_hash_key)
REFERENCES crm_injury_register_csv (injury_identifier_source_name);
