CREATE TABLE sat_claim_investigation_sap
(
  claim_investigation_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  claim_investigator_id STRING,
  investigation_notes STRING,
  case_open_date DATE,
  case_close_date DATE,
  fraud_confirmed_flag STRING,
  claim_review_flag STRING,
  fraud_risk_assessment STRING
);

ALTER TABLE sat_claim_investigation_sap
ADD CONSTRAINT XPKSAT_CLAIM_INVESTIGATION_SAP PRIMARY KEY (claim_investigation_hash_key, load_ts);

ALTER TABLE sat_claim_investigation_sap
ADD CONSTRAINT FK_SAT_CLAIM_INVESTIGATION_SAP__SAP_CLAIM_INVESTIGATION_DB
FOREIGN KEY (claim_investigation_hash_key)
REFERENCES sap_claim_investigation_db (claim_ref_id_source_name);
