CREATE TABLE sat_policy_coverage
(
  policy_coverage_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  coverage_group_id STRING,
  coverage_status_date DATE,
  coverage_status_code STRING,
  sum_insured DOUBLE,
  sum_insured_after_coinsurance DOUBLE,
  gross_annualized_premium DOUBLE,
  peril_premium DOUBLE,
  annual_aggregate_limit DOUBLE,
  excess DOUBLE,
  minimum_deductible DOUBLE,
  indexation STRING,
  automatic_indexation_flag STRING,
  coverage_extension STRING,
  coverage_trigger STRING,
  coverage_level_lh STRING,
  logic_of_limit STRING,
  scope_of_limit STRING,
  pct_loss_deductible DOUBLE,
  actual_price DOUBLE,
  agreed_value DOUBLE,
  technical_price_natural_perils DOUBLE,
  mandatory_participation STRING,
  liability_agreed_flag STRING,
  liability_exposure_value DOUBLE,
  flag_dual_insurance STRING,
  flag_inhabited_building STRING,
  motor_accessories_sum_insured DOUBLE,
  time_element_sum_insured DOUBLE,
  value_insured_property_damage DOUBLE,
  contingent_bi_flag STRING,
  contingent_bi_waiting_period BIGINT,
  coverage_sum_at_risk DOUBLE,
  employer_contribution_level DOUBLE,
  premium_paid_previous_period DOUBLE,
  position_grade STRING,
  benefit_grouping STRING
)
USING DELTA;

ALTER TABLE sat_policy_coverage
ADD CONSTRAINT XPKSAT_POLICY_COVERAGE PRIMARY KEY (policy_coverage_hash_key, load_ts);

ALTER TABLE sat_policy_coverage
ADD CONSTRAINT FK_SAT_POLICY_COVERAGE__CRM_POLICY_COVERAGE_REGISTER_CSV
FOREIGN KEY (policy_coverage_hash_key)
REFERENCES crm_policy_coverage_register_csv (policy_coverage_identifier_source_name);
