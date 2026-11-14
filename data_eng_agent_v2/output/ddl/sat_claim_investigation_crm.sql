CREATE TABLE sat_claim_investigation_crm
(
  claim_investigation_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  claim_handler_identifier STRING,
  claim_handler_notes STRING,
  claim_investigation_start_date DATE,
  claim_investigation_end_date DATE,
  fraud_indicator STRING,
  investigator_flag STRING,
  claim_fraud_assessment STRING
);

ALTER TABLE sat_claim_investigation_crm
ADD CONSTRAINT XPKSAT_CLAIM_INVESTIGATION_CRM PRIMARY KEY (claim_investigation_hash_key, load_ts);

ALTER TABLE sat_claim_investigation_crm
ADD CONSTRAINT FK_SAT_CLAIM_INVESTIGATION_CRM__CRM_CLAIM_INVESTIGATION_REGISTER_CSV
FOREIGN KEY (claim_investigation_hash_key)
REFERENCES crm_claim_investigation_register_csv (claim_investigation_identifier_source_name);
