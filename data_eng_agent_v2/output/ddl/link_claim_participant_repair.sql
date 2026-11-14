CREATE TABLE link_claim_participant_repair
(
  claim_participant_repair_hash_key STRING NOT NULL,
  claim_participant_hash_key STRING,
  repair_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_claim_participant_repair
ADD CONSTRAINT XPKLINK_CLAIM_PARTICIPANT_REPAIR PRIMARY KEY (claim_participant_repair_hash_key);

ALTER TABLE link_claim_participant_repair
ADD CONSTRAINT FK_LINK_CLAIM_PARTICIPANT_REPAIR__CRM_CLAIM_PARTICIPANT_REGISTER_CSV
FOREIGN KEY (claim_participant_hash_key)
REFERENCES crm_claim_participant_register_csv (claim_participant_identifier_source_name);

ALTER TABLE link_claim_participant_repair
ADD CONSTRAINT FK_LINK_CLAIM_PARTICIPANT_REPAIR__CRM_REPAIR_REGISTER_CSV
FOREIGN KEY (repair_hash_key)
REFERENCES crm_repair_register_csv (repair_identifier_source_name);
