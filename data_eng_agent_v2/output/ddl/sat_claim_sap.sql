CREATE TABLE sat_claim_sap
(
  claim_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  ext_claim_number STRING,
  loss_category STRING,
  tp_claim_ref STRING,
  claim_stage STRING,
  case_state STRING,
  stage_update_date STRING,
  first_notice_date DATE,
  claim_settlement_date DATE,
  last_activity_date DATE,
  case_age_days BIGINT,
  category_code STRING,
  handling_method STRING,
  risk_level STRING,
  injury_flag STRING,
  write_off_flag STRING,
  legal_case_flag STRING,
  confirmed_fraud_flag STRING,
  hospitalization_flag STRING,
  estimated_loss_amount DOUBLE,
  expected_recovery_amount DOUBLE,
  recovered_amount DOUBLE,
  recovery_category STRING,
  denial_reason STRING,
  closure_reason STRING,
  recovery_payment_date DATE,
  work_status_prior_incident STRING,
  return_to_work_status STRING,
  total_estimated_cost DOUBLE,
  total_paid_amount DOUBLE,
  eligible_reimbursement_amount DOUBLE,
  medical_reimbursement_amount DOUBLE,
  proposed_settlement_amount DOUBLE,
  approval_date DATE,
  payment_release_date DATE
)
USING DELTA;

ALTER TABLE sat_claim_sap
ADD CONSTRAINT XPKSAT_CLAIM_SAP PRIMARY KEY (claim_hash_key, load_ts);

ALTER TABLE sat_claim_sap
ADD CONSTRAINT FK_SAT_CLAIM_SAP__SAP_CLAIM_DB
FOREIGN KEY (claim_hash_key)
REFERENCES sap_claim_db (claim_ref_id_source_name);
