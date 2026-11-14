CREATE TABLE sat_settlement
(
  settlement_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  date_of_final_settlement DATE,
  date_of_settlement_offer_decision DATE,
  insurers_current_settlement_offer_amount DOUBLE,
  insurers_first_settlement_offer_amount DOUBLE,
  outstanding_medical_expenses DOUBLE,
  settlement_table STRING,
  settlement_type STRING
);

ALTER TABLE sat_settlement
ADD CONSTRAINT XPKSAT_SETTLEMENT PRIMARY KEY (settlement_hash_key, load_ts);

ALTER TABLE sat_settlement
ADD CONSTRAINT FK_SAT_SETTLEMENT__CRM_SETTLEMENT_REGISTER_CSV
FOREIGN KEY (settlement_hash_key)
REFERENCES crm_settlement_register_csv (settlement_identifier_source_name);
