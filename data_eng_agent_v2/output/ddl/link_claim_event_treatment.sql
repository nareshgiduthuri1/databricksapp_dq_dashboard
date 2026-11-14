CREATE TABLE link_claim_event_treatment
(
  claim_event_treatment_hash_key STRING NOT NULL,
  claim_event_hash_key STRING,
  treatment_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_claim_event_treatment
ADD CONSTRAINT XPKLINK_CLAIM_EVENT_TREATMENT PRIMARY KEY (claim_event_treatment_hash_key);

ALTER TABLE link_claim_event_treatment
ADD CONSTRAINT FK_LINK_CLAIM_EVENT_TREATMENT__CRM_CLAIM_EVENT_LOG_CSV
FOREIGN KEY (claim_event_hash_key)
REFERENCES crm_claim_event_log_csv (claim_event_identifier_source_name);

ALTER TABLE link_claim_event_treatment
ADD CONSTRAINT FK_LINK_CLAIM_EVENT_TREATMENT__CRM_TREATMENT_REGISTER_CSV
FOREIGN KEY (treatment_hash_key)
REFERENCES crm_treatment_register_csv (treatment_identifier_source_name);
