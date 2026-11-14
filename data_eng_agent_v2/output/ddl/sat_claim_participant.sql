CREATE TABLE sat_claim_participant
(
  claim_participant_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  role_in_claim STRING,
  is_primary_indicator STRING,
  liability_percentage DECIMAL(5,2),
  injury_flag STRING,
  involvement_type STRING,
  role_start_date DATE,
  role_end_date DATE
);

ALTER TABLE sat_claim_participant
ADD CONSTRAINT XPKSAT_CLAIM_PARTICIPANT PRIMARY KEY (claim_participant_hash_key, load_ts);

ALTER TABLE sat_claim_participant
ADD CONSTRAINT FK_SAT_CLAIM_PARTICIPANT__CRM_CLAIM_PARTICIPANT_REGISTER_CSV
FOREIGN KEY (claim_participant_hash_key)
REFERENCES crm_claim_participant_register_csv (claim_participant_identifier_source_name);
