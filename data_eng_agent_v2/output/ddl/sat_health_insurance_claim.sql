CREATE TABLE sat_health_insurance_claim
(
  health_insurance_claim_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  date_of_first_medical_expert_report DATE,
  health_data_consent STRING
);

ALTER TABLE sat_health_insurance_claim
ADD CONSTRAINT XPKSAT_HEALTH_INSURANCE_CLAIM PRIMARY KEY (health_insurance_claim_hash_key, load_ts);

ALTER TABLE sat_health_insurance_claim
ADD CONSTRAINT FK_SAT_HEALTH_INSURANCE_CLAIM__CRM_HEALTH_CLAIM_REGISTER_CSV
FOREIGN KEY (health_insurance_claim_hash_key)
REFERENCES crm_health_claim_register_csv (health_insurance_claim_identifier_source_name);
