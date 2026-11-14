CREATE TABLE link_person_claim_participant
(
  person_claim_participant_hash_key STRING NOT NULL,
  person_hash_key STRING,
  claim_participant_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_person_claim_participant
ADD CONSTRAINT XPKLINK_PERSON_CLAIM_PARTICIPANT PRIMARY KEY (person_claim_participant_hash_key);

ALTER TABLE link_person_claim_participant
ADD CONSTRAINT FK_LINK_PERSON_CLAIM_PARTICIPANT__CRM_PARTY_MASTER_CSV
FOREIGN KEY (person_hash_key)
REFERENCES crm_party_master_csv (person_identifier_source_name);

ALTER TABLE link_person_claim_participant
ADD CONSTRAINT FK_LINK_PERSON_CLAIM_PARTICIPANT__CRM_CLAIM_PARTICIPANT_REGISTER_CSV
FOREIGN KEY (claim_participant_hash_key)
REFERENCES crm_claim_participant_register_csv (claim_participant_identifier_source_name);
