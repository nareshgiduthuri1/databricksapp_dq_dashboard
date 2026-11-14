# Databricks notebook source
# DBTITLE 1,Sat Configs - Product ID 3

sat_catastrophe_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_catastrophe_3",
  "object_type": "sat",
  "target_table": "sat_catastrophe",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(catastrophe_identifier, origin_sys)) AS catastrophe_hash_key,
  CAST(load_ts AS TIMESTAMP) AS load_ts,
  source_name AS record_source,
  catastrophe_cause AS catastrophe_cause,
  catastrophe_description AS catastrophe_description,
  catastrophe_begin_date AS catastrophe_begin_date,
  catastrophe_end_date AS catastrophe_end_date,
  cresta_zone AS cresta_zone,
  nat_cat_event_code AS nat_cat_event_code
FROM crm_catastrophe_event_register_csv
""",
  "source_table": "crm_catastrophe_event_register_csv"
}

sat_claim_crm_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_claim_crm_3",
  "object_type": "sat",
  "target_table": "sat_claim_crm",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(claim_identifier, source_name)) AS claim_hash_key,
  load_ts,
  source_name AS record_source,
  claim_type,
  claim_number,
  third_party_claim_number,
  claim_status,
  claim_state,
  claim_status_date,
  claim_open_date,
  claim_close_date,
  claim_reopen_date,
  claim_reopen_reason,
  claims_made_date,
  movement_date,
  claim_duration,
  claim_type_code,
  claim_process_method,
  claim_specific_flag,
  bodily_injury_indicator,
  applicable_deductible_flag,
  total_loss_flag,
  litigation_flag,
  proven_claim_fraud_flag,
  cross_border_claim_indicator,
  intercompany_agreement_flag,
  no_claims_discount,
  claim_requested_amount,
  outstanding_subrogation_amount,
  recovery_actual,
  recovery_type,
  claims_rejection_reason,
  finalization_reason,
  indemnity_logic,
  coverage_verification_result,
  instruction_closure_date,
  subrogation_paid_date,
  claims_history_lob,
  fire_brigade_fees_and_levies,
  total_incurred,
  total_payment_amount,
  reimbursable_claim_amount,
  settlement_amount_pc,
  claim_approval_date,
  claim_payment_date,
  claim_amounts_description,
  NULL AS insured_entity_id,
  outstanding_reserve,
  claims_expenses,
  is_claim_suspicious,
  suspected_amt,
  fraud_amt,
  is_recovery_happened,
  days_to_first_recovery,
  days_to_last_recovery,
  litigation_duration_days,
  claim_reason,
  claim_channel,
  claim_product,
  claim_band,
  claim_band_sort,
  claim_fraud_status,
  claim_fraud_type,
  claim_fraud_detection_method,
  recovery_band,
  recovery_category,
  recovery_source
FROM crm_claim_register_csv
UNION ALL
SELECT DISTINCT
  md5(concat(claim_identifier, source_name)) AS claim_hash_key,
  load_ts,
  source_name AS record_source,
  claim_type,
  claim_number,
  third_party_claim_number,
  claim_status,
  claim_state,
  claim_status_date,
  claim_open_date,
  claim_close_date,
  claim_reopen_date,
  claim_reopen_reason,
  claims_made_date,
  movement_date,
  claim_duration,
  claim_type_code,
  claim_process_method,
  claim_specific_flag,
  bodily_injury_indicator,
  applicable_deductible_flag,
  total_loss_flag,
  litigation_flag,
  proven_claim_fraud_flag,
  cross_border_claim_indicator,
  intercompany_agreement_flag,
  no_claims_discount,
  claim_requested_amount,
  outstanding_subrogation_amount,
  recovery_actual,
  recovery_type,
  claims_rejection_reason,
  finalization_reason,
  indemnity_logic,
  coverage_verification_result,
  instruction_closure_date,
  subrogation_paid_date,
  claims_history_lob,
  fire_brigade_fees_and_levies,
  total_incurred,
  total_payment_amount,
  reimbursable_claim_amount,
  settlement_amount_pc,
  claim_approval_date,
  claim_payment_date,
  claim_amounts_description,
  claim_participant_identifier AS insured_entity_id,
  outstanding_reserve,
  claims_expense AS claims_expenses,
  is_claim_suspicious,
  suspected_amt,
  fraud_amt,
  is_recovery_happened,
  days_to_first_recovery,
  days_to_last_recovery,
  litigation_duration_days,
  claim_reason,
  claim_channel,
  claim_product,
  claim_band,
  claim_band_sort,
  claim_fraud_status,
  claim_fraud_type,
  claim_fraud_detection_method,
  recovery_band,
  recovery_category,
  recovery_source
FROM crm_claim_participant_register_csv
""",
  "source_table": "crm_claim_register_csv,crm_claim_participant_register_csv"
}

sat_claim_event_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_claim_event_3",
  "object_type": "sat",
  "target_table": "sat_claim_event",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(claim_event_identifier, source_name)) AS claim_event_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  event_type AS event_type,
  event_date AS event_date,
  event_description AS event_description
FROM crm_claim_event_log_csv
""",
  "source_table": "crm_claim_event_log_csv"
}

sat_claim_investigation_crm_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_claim_investigation_crm_3",
  "object_type": "sat",
  "target_table": "sat_claim_investigation_crm",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(claim_investigation_identifier, source_name)) AS claim_investigation_hash_key,
  load_ts AS load_ts,
  source_name AS record_source,
  claim_handler_identifier AS claim_handler_identifier,
  claim_handler_notes AS claim_handler_notes,
  claim_investigation_start_date AS claim_investigation_start_date,
  claim_investigation_end_date AS claim_investigation_end_date,
  fraud_indicator AS fraud_indicator,
  investigator_flag AS investigator_flag,
  claim_fraud_assessment AS claim_fraud_assessment
FROM crm_claim_investigation_register_csv
""",
  "source_table": "crm_claim_investigation_register_csv"
}

sat_claim_participant_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_claim_participant_3",
  "object_type": "sat",
  "target_table": "sat_claim_participant",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(claim_participant_identifier, source_name)) AS claim_participant_hash_key,
  load_ts,
  source_name AS record_source,
  role_in_claim,
  is_primary_indicator,
  liability_percentage,
  injury_flag,
  involvement_type,
  role_start_date,
  role_end_date
FROM crm_claim_participant_register_csv
""",
  "source_table": "crm_claim_participant_register_csv"
}

sat_coverage_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_coverage_3",
  "object_type": "sat",
  "target_table": "sat_coverage",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(coverage_identifier, source_name)) AS coverage_hash_key,
  load_ts,
  source_name AS record_source,
  coverage_type,
  coverage_description,
  coverage_start_date,
  coverage_end_date,
  coverage_type_identifier AS coverage_type_id,
  maximum_deductible,
  limit_identifier AS limit_id,
  exclusion_identifier AS exclusion_id,
  deductible_identifier AS deductible_id,
  benefit_identifier AS benefit_id,
  risk_identifier AS risk_id,
  peril_identifier AS peril_id,
  product_element_identifier AS product_element_id
FROM crm_coverage_catalog_csv
""",
  "source_table": "crm_coverage_catalog_csv"
}

sat_diagnosis_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_diagnosis_3",
  "object_type": "sat",
  "target_table": "sat_diagnosis",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(CONCAT(diagnosis_identifier, source_name)) AS diagnosis_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  diagnosis_code AS diagnosis_code,
  diagnosis_description AS diagnosis_description,
  diagnosis_priority AS diagnosis_priority,
  diagnosis_standard AS diagnosis_standard
FROM crm_diagnosis_register_csv
""",
  "source_table": "crm_diagnosis_register_csv"
}

sat_health_insurance_claim_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_health_insurance_claim_3",
  "object_type": "sat",
  "target_table": "sat_health_insurance_claim",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(health_insurance_claim_identifier, source_name)) AS health_insurance_claim_hash_key,
  CAST(load_ts AS TIMESTAMP) AS load_ts,
  source_name AS record_source,
  date_of_first_medical_expert_report AS date_of_first_medical_expert_report,
  health_data_consent AS health_data_consent
FROM crm_health_claim_register_csv
""",
  "source_table": "crm_health_claim_register_csv"
}

sat_injury_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_injury_3",
  "object_type": "sat",
  "target_table": "sat_injury",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(CONCAT(injury_identifier, source_name)) AS injury_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  bodily_injury_date AS bodily_injury_date,
  injury_description AS injury_description
FROM crm_injury_register_csv
""",
  "source_table": "crm_injury_register_csv"
}

sat_insured_entity_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_insured_entity_3",
  "object_type": "sat",
  "target_table": "sat_insured_entity",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(insured_entity_identifier, source_name)) AS insured_entity_hash_key,
  CAST(load_ts AS TIMESTAMP) AS load_ts,
  source_name AS record_source,
  entity_type AS entity_type,
  insured_person_identifier AS insured_person_identifier,
  insured_object_owner_identifier AS insured_object_owner_identifier,
  insured_object_address_flag AS insured_object_address_flag,
  insured_object_sum_insured AS insured_object_sum_insured,
  exposure_base AS exposure_base,
  grouped_location_flag AS grouped_location_flag,
  replacement_value AS replacement_value,
  type_of_insured_entity AS type_of_insured_entity,
  value_of_content AS value_of_content,
  value_of_goods_carried AS value_of_goods_carried,
  actual_pre_event_entity_value AS actual_pre_event_entity_value,
  damaged_entity AS damaged_entity,
  insured_object_description AS insured_object_desc,
  insured_object_current_status AS insured_object_current_status,
  insured_object_start_date AS insured_object_start_date,
  insured_object_end_date AS insured_object_end_date,
  wall_construction_material_type AS wall_construction_material_type,
  home_risk_address AS home_risk_address,
  home_type AS home_type,
  home_state AS home_state,
  vehicle_body_type AS vehicle_body_type,
  vehicle_fuel_type AS vehicle_fuel_type,
  vehicle_risk_address AS vehicle_risk_address,
  vehicle_risk_class_code AS vehicle_risk_class_code,
  vehicle_variant AS vehicle_variant,
  vehicle_reg_state AS vehicle_reg_state,
  vehicle_class AS vehicle_class,
  vehicle_model AS vehicle_model
FROM crm_insured_entity_register_csv
""",
  "source_table": "crm_insured_entity_register_csv"
}

sat_litigation_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_litigation_3",
  "object_type": "sat",
  "target_table": "sat_litigation",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(litigation_identifier, source_name)) AS litigation_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  court_matter_type AS court_matter_type,
  date_of_legal_representation AS date_of_legal_representation,
  first_litigation_date AS first_litigation_date,
  litigation_date AS litigation_date,
  decision_of_court AS decision_of_court,
  litigation_start_date AS litigation_start_date,
  litigation_end_date AS litigation_end_date
FROM crm_litigation_register_csv
""",
  "source_table": "crm_litigation_register_csv"
}

sat_loss_event_crm_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_loss_event_crm_3",
  "object_type": "sat",
  "target_table": "sat_loss_event_crm",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(loss_event_identifier, source_name)) AS loss_event_hash_key,
  CAST(load_ts AS TIMESTAMP) AS load_ts,
  source_name AS record_source,
  loss_event_name AS loss_event_name,
  loss_event_description AS loss_event_description,
  loss_date AS loss_date,
  loss_time AS loss_time,
  loss_event_start_date AS loss_event_start_date,
  loss_event_end_date AS loss_event_end_date,
  loss_event_status AS loss_event_status,
  loss_type AS loss_type,
  loss_category AS loss_category,
  loss_cause AS loss_cause,
  property_liability_loss_cause AS property_liability_loss_cause,
  date_of_effective_loss AS effective_loss_date,
  notification_date AS notification_date,
  notification_channel AS notification_channel,
  fatality_indicator AS fatality_flag,
  minimal_impact_flag AS minimal_impact_flag,
  number_of_injured_parties AS number_of_injured_parties,
  number_of_people_involved AS number_of_people_involved,
  number_of_vehicles_involved AS number_of_vehicles_involved,
  claimant_drugs_or_alcohol AS drugs_alcohol_indicator,
  contributory_negligence AS contributory_negligence_flag,
  damage_specification AS damage_specification
FROM crm_loss_event_register_csv
""",
  "source_table": "crm_loss_event_register_csv"
}

sat_medical_assessment_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_medical_assessment_3",
  "object_type": "sat",
  "target_table": "sat_medical_assessment",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(CONCAT(medical_assessment_identifier, source_name)) AS medical_assessment_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  assessed_disability_degree AS assessed_disability_degree,
  permanent_disability_degree AS permanent_disability_degree,
  permanent_disability_flag AS permanent_disability_flag,
  medical_report_flag AS medical_report_flag,
  medical_report_date AS medical_report_date,
  person_hospital_status AS person_hospital_status,
  psychological_factors AS psychological_factors,
  medical_condition_description AS medical_condition_description
FROM crm_medical_assessment_register_csv
""",
  "source_table": "crm_medical_assessment_register_csv"
}

sat_medical_condition_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_medical_condition_3",
  "object_type": "sat",
  "target_table": "sat_medical_condition",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(CONCAT(medical_condition_identifier, source_name)) AS medical_condition_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  disease_name AS disease_name,
  disability_status AS disability_status,
  pre_existing_condition AS pre_existing_condition
FROM crm_medical_condition_catalog_csv
""",
  "source_table": "crm_medical_condition_catalog_csv"
}

sat_medical_report_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_medical_report_3",
  "object_type": "sat",
  "target_table": "sat_medical_report",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(medical_report_identifier, source_name)) AS medical_report_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  document_identifier AS document_id,
  health_declaration AS health_declaration
FROM crm_medical_report_register_csv
""",
  "source_table": "crm_medical_report_register_csv"
}

sat_person_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_person_3",
  "object_type": "sat",
  "target_table": "sat_person",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(person_identifier, source_name)) AS person_hash_key,
  load_ts AS load_ts,
  source_name AS record_source,
  is_lead AS is_lead,
  language_pref AS preferred_language,
  source_identifier AS source_identifier,
  source_type AS source_type,
  tenant_identifier AS tenant_identifier,
  disability_degree AS assessed_disability_degree,
  is_operational_paperless_consent AS is_operational_paperless_consent,
  is_opt_in_legitimate_interest AS is_opt_in_legitimate_interest,
  is_opt_in_validated AS is_opt_in_validated,
  person_type AS person_type,
  digital_identifier AS digital_id,
  identification_type AS identification_type,
  legal_consent_flag AS legal_consent_flag,
  credit_rating AS credit_rating,
  credit_rating_provider AS credit_rating_provider,
  rate_class AS rate_class,
  person_status AS person_status,
  natural_ref AS natural_ref,
  given_nm AS first_name,
  family_nm AS last_name,
  display_nm AS full_name,
  title_txt AS courtesy_title,
  occupation_txt AS occupation,
  dob AS birth_date,
  birth_yr AS birth_year,
  nationality_txt AS nationality,
  gender_txt AS gender,
  marital_txt AS marital_status,
  job_title_txt AS job_title,
  role_txt AS role,
  lead_conv_dt AS converted_date,
  legal_score_no AS person_score,
  email_home_txt AS email_home,
  email_work_txt AS email_work,
  phone_work_txt AS phone_work,
  phone_home_txt AS phone_home,
  legal_ref AS legal_ref,
  legal_name AS company_name,
  constitution_dt AS date_of_constitution,
  legal_job_title_txt AS legal_job_title,
  legal_src_ref AS legal_src_ref,
  legal_src_type AS legal_src_type,
  legal_status_txt AS legal_status
FROM crm_party_master_csv
""",
  "source_table": "crm_party_master_csv"
}

sat_physical_place_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_physical_place_3",
  "object_type": "sat",
  "target_table": "sat_physical_place",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(physical_place_identifier, source_name)) AS physical_place_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  place_identifier AS place_id,
  city AS city,
  state AS state,
  country AS country,
  applicable_jurisdiction AS applicable_jurisdiction,
  census_zone AS census_zone,
  commune_code AS commune_code,
  geocoding_level AS geocoding_level,
  latitude AS latitude,
  longitude AS longitude,
  municipal_district AS municipal_district,
  natcat_hazard_zone_scheme AS natcat_hazard_zone_scheme,
  point_of_interest AS point_of_interest,
  possible_max_business_interruption AS possible_max_business_interruption,
  sub_region AS sub_region,
  surface_elevation AS surface_elevation
FROM crm_physical_place_register_csv
""",
  "source_table": "crm_physical_place_register_csv"
}

sat_police_report_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_police_report_3",
  "object_type": "sat",
  "target_table": "sat_police_report",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(police_report_identifier, source_name)) AS police_report_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  police_report_number AS police_report_number,
  police_report_date AS police_report_date,
  police_report_flag AS police_report_flag
FROM crm_police_report_register_csv
""",
  "source_table": "crm_police_report_register_csv"
}

sat_policy_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_policy_3",
  "object_type": "sat",
  "target_table": "sat_policy",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(policy_identifier, source_name)) AS policy_hash_key,
  load_ts AS load_ts,
  source_name AS record_source,
  policy_type AS policy_type,
  policy_number AS policy_number,
  aspire_policy_identifier AS aspire_policy_id,
  policy_status_code AS policy_status_code,
  policy_status_date AS policy_status_date,
  policy_inception_date AS policy_inception_date,
  policy_inception_date_as_new_business AS policy_inception_date_as_new_business,
  policy_inception_date_of_first_allianz_policy AS policy_inception_date_of_first_allianz_policy,
  policy_issue_date AS policy_issue_date,
  policy_end_date AS policy_end_date,
  policy_expiry_date AS policy_expiry_date,
  policy_cancellation_date AS policy_cancellation_date,
  policy_cancellation_notification_date AS policy_cancellation_notification_date,
  policy_cancellation_reason AS policy_cancellation_reason,
  policy_renewal_date AS policy_renewal_date,
  policy_renewal_notification_date AS policy_renewal_notification_date,
  policy_duration AS policy_duration,
  premium AS premium,
  gross_written_premium AS gross_written_premium,
  gross_earned_premium AS gross_earned_premium,
  gross_original_premium AS gross_original_premium,
  paid_premium AS paid_premium,
  sum_of_paid_premium AS sum_of_paid_premium,
  unearned_premium_amount AS unearned_premium_amount,
  adjustment_premium AS adjustment_premium,
  adjustment_earned_premium AS adjustment_earned_premium,
  estimated_premium_income AS estimated_premium_income,
  subject_premium_income AS subject_premium_income,
  technical_price AS technical_price,
  technical_expected_loss AS technical_expected_loss,
  projected_loss_ratio AS projected_loss_ratio,
  underwriting_premium_surcharge AS underwriting_premium_surcharge,
  commission_due_amount AS commission_due_amount,
  gross_written_commission_amount AS gross_written_commission_amount,
  gross_earned_commission AS gross_earned_commission,
  gross_original_commission AS gross_original_commission,
  commission_share AS commission_share,
  differed_acquisition_cost AS differed_acquisition_cost,
  frequency_of_installments AS frequency_of_installments,
  preferred_payment_date AS preferred_payment_date,
  date_of_debit AS date_of_debit,
  tax_code AS tax_code,
  tariff_version AS tariff_version,
  premium_configuration_code AS premium_configuration_code,
  ifrs17_measurement_model AS ifrs17_measurement_model,
  current_bonus_malus_class AS current_bonus_malus_class,
  previous_bonus_malus_class AS previous_bonus_malus_class,
  no_claims_discount AS no_claims_discount,
  annual_aggregate_deductible AS annual_aggregate_deductible,
  limit_for_indemnification AS limit_for_indemnification,
  limit_business_interruption AS limit_business_interruption,
  number_of_insured_persons AS number_of_insured_persons,
  number_of_substituting_policy AS number_of_substituting_policy,
  automatic_renewal_years AS automatic_renewal_years,
  reinsurance_flag AS reinsurance_flag,
  retention_flag AS retention_flag,
  tacit_renewal_flag AS tacit_renewal_flag,
  multi_year_contracts AS multi_year_contracts,
  lapse_flag AS lapse_flag,
  flag_change_of_contract AS flag_change_of_contract,
  flag_cross_selling AS flag_cross_selling,
  flag_quote_conversion AS flag_quote_conversion,
  marketing_campaign_flag AS marketing_campaign_flag,
  primary_excess_liability_flag AS primary_excess_liability_flag,
  operational_paperless_consent AS operational_paperless_consent,
  legal_consent AS legal_consent,
  declared_driver AS declared_driver,
  broker_wording AS broker_wording,
  manual_clauses AS manual_clauses,
  rationale_for_cession AS rationale_for_cession,
  statute_of_limitation_date AS statute_of_limitation_date,
  product_group_identifier AS product_group_id,
  policy_holder_identifier AS policy_holder_id,
  portfolio_identifier AS portfolio_id,
  party_in_role_identifier AS party_in_role_id
FROM crm_policy_register_csv
""",
  "source_table": "crm_policy_register_csv"
}

sat_policy_coverage_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_policy_coverage_3",
  "object_type": "sat",
  "target_table": "sat_policy_coverage",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(policy_coverage_identifier, source_name)) AS policy_coverage_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  coverage_group_identifier AS coverage_group_id,
  coverage_status_date AS coverage_status_date,
  coverage_status_code AS coverage_status_code,
  sum_insured AS sum_insured,
  sum_insured_after_coinsurance AS sum_insured_after_coinsurance,
  gross_annualized_premium AS gross_annualized_premium,
  peril_premium AS peril_premium,
  annual_aggregate_limit AS annual_aggregate_limit,
  excess AS excess,
  minimum_deductible AS minimum_deductible,
  indexation AS indexation,
  automatic_indexation_flag AS automatic_indexation_flag,
  coverage_extension AS coverage_extension,
  coverage_trigger AS coverage_trigger,
  coverage_level_lh AS coverage_level_lh,
  logic_of_limit AS logic_of_limit,
  scope_of_limit AS scope_of_limit,
  pct_loss_deductible AS pct_loss_deductible,
  actual_price AS actual_price,
  agreed_value AS agreed_value,
  technical_price_natural_perils AS technical_price_natural_perils,
  mandatory_participation AS mandatory_participation,
  liability_agreed_flag AS liability_agreed_flag,
  liability_exposure_value AS liability_exposure_value,
  flag_dual_insurance AS flag_dual_insurance,
  flag_inhabited_building AS flag_inhabited_building,
  motor_accessories_sum_insured AS motor_accessories_sum_insured,
  time_element_sum_insured AS time_element_sum_insured,
  value_insured_property_damage AS value_insured_property_damage,
  contingent_bi_flag AS contingent_bi_flag,
  contingent_bi_waiting_period AS contingent_bi_waiting_period,
  coverage_sum_at_risk AS coverage_sum_at_risk,
  employer_contribution_level AS employer_contribution_level,
  premium_paid_previous_period AS premium_paid_previous_period,
  position_grade AS position_grade,
  benefit_grouping AS benefit_grouping
FROM crm_policy_coverage_register_csv
""",
  "source_table": "crm_policy_coverage_register_csv"
}

sat_repair_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_repair_3",
  "object_type": "sat",
  "target_table": "sat_repair",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(repair_identifier, source_name)) AS repair_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  number_of_spare_parts_repaired AS number_of_spare_parts_repaired,
  paid_spare_parts_costs AS paid_spare_parts_costs,
  spare_part_repair_shop_price AS spare_part_repair_shop_price,
  spare_part_type AS spare_part_type
FROM crm_repair_register_csv
""",
  "source_table": "crm_repair_register_csv"
}

sat_settlement_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_settlement_3",
  "object_type": "sat",
  "target_table": "sat_settlement",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(CONCAT(settlement_identifier, source_name)) AS settlement_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  date_of_final_settlement AS date_of_final_settlement,
  date_of_settlement_offer_decision AS date_of_settlement_offer_decision,
  insurers_current_settlement_offer_amount AS insurers_current_settlement_offer_amount,
  insurers_first_settlement_offer_amount AS insurers_first_settlement_offer_amount,
  outstanding_medical_expenses AS outstanding_medical_expenses,
  settlement_table AS settlement_table,
  settlement_type AS settlement_type
FROM crm_settlement_register_csv
""",
  "source_table": "crm_settlement_register_csv"
}

sat_treatment_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_treatment_3",
  "object_type": "sat",
  "target_table": "sat_treatment",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(CONCAT(treatment_identifier, source_name)) AS treatment_hash_key,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source,
  treatment_code AS treatment_code,
  treatment_code_standard AS treatment_code_standard,
  treatment_description AS treatment_description,
  treatment_complexity_level AS treatment_complexity_level,
  initial_treatment_date AS initial_treatment_date,
  treatment_start_date AS treatment_start_date,
  number_of_treatments AS number_of_treatments,
  paid_treatment_amount AS paid_treatment_amount,
  treatment_amount_currency AS treatment_amount_currency,
  medication_code AS medication_code,
  treatment_type AS treatment_type
FROM crm_treatment_register_csv
""",
  "source_table": "crm_treatment_register_csv"
}

sat_claim_sap_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_claim_sap_3",
  "object_type": "sat",
  "target_table": "sat_claim_sap",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(claim_ref_id, source_name)) AS claim_hash_key,
  load_ts AS load_ts,
  source_name AS record_source,
  ext_claim_number AS ext_claim_number,
  loss_category AS loss_category,
  tp_claim_ref AS tp_claim_ref,
  claim_stage AS claim_stage,
  case_state AS case_state,
  stage_update_date AS stage_update_date,
  first_notice_date AS first_notice_date,
  claim_settlement_date AS claim_settlement_date,
  last_activity_date AS last_activity_date,
  case_age_days AS case_age_days,
  category_code AS category_code,
  handling_method AS handling_method,
  risk_level AS risk_level,
  injury_flag AS injury_flag,
  write_off_flag AS write_off_flag,
  legal_case_flag AS legal_case_flag,
  confirmed_fraud_flag AS confirmed_fraud_flag,
  hospitalization_flag AS hospitalization_flag,
  estimated_loss_amount AS estimated_loss_amount,
  expected_recovery_amount AS expected_recovery_amount,
  recovered_amount AS recovered_amount,
  recovery_category AS recovery_category,
  denial_reason AS denial_reason,
  closure_reason AS closure_reason,
  recovery_payment_date AS recovery_payment_date,
  work_status_prior_incident AS work_status_prior_incident,
  return_to_work_status AS return_to_work_status,
  total_estimated_cost AS total_estimated_cost,
  total_paid_amount AS total_paid_amount,
  eligible_reimbursement_amount AS eligible_reimbursement_amount,
  medical_reimbursement_amount AS medical_reimbursement_amount,
  proposed_settlement_amount AS proposed_settlement_amount,
  approval_date AS approval_date,
  payment_release_date AS payment_release_date
FROM sap_claim_db
""",
  "source_table": "sap_claim_db"
}

sat_claim_investigation_sap_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_claim_investigation_sap_3",
  "object_type": "sat",
  "target_table": "sat_claim_investigation_sap",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(claim_ref_id, source_name)) AS claim_investigation_hash_key,
  CAST(load_ts AS TIMESTAMP) AS load_ts,
  source_name AS record_source,
  siu_investigator_id AS claim_investigator_id,
  investigation_notes AS investigation_notes,
  case_open_date AS case_open_date,
  case_close_date AS case_close_date,
  fraud_confirmed_flag AS fraud_confirmed_flag,
  siu_review_flag AS claim_review_flag,
  fraud_risk_assessment AS fraud_risk_assessment
FROM sap_claim_investigation_db
""",
  "source_table": "sap_claim_investigation_db"
}

sat_loss_event_sap_3 =  {
  "product_id": "3",
  "vault_object_id": "sat_loss_event_sap_3",
  "object_type": "sat",
  "target_table": "sat_loss_event_sap",
  "process_order": "3",
  "build_sql": f"""
SELECT DISTINCT
  md5(concat(incident_id, source_name)) AS loss_event_hash_key,
  load_ts AS load_ts,
  source_name AS record_source,
  incident_name AS incident_name,
  incident_description AS incident_description,
  event_date AS event_date,
  event_time AS event_time,
  incident_start_date AS incident_start_date,
  incident_end_date AS incident_end_date,
  incident_status AS incident_status,
  event_type AS event_type,
  incident_category AS incident_category,
  root_cause AS root_cause,
  liability_cause AS liability_cause,
  reported_date AS reported_date,
  reporting_channel AS reporting_channel,
  days_to_fnol AS days_to_fnol,
  notification_duration AS notification_duration,
  casualty_indicator AS casualty_indicator,
  catastrophe_flag AS catastrophe_flag,
  natcat_flag AS natcat_flag,
  event_severity_low_flag AS event_severity_low_flag,
  casualty_count AS casualty_count,
  impacted_person_count AS impacted_person_count,
  impacted_vehicle_count AS impacted_vehicle_count,
  impairment_flag AS impairment_flag,
  shared_liability_flag AS shared_liability_flag,
  impact_description AS impact_description
FROM sap_loss_event_db
""",
  "source_table": "sap_loss_event_db"
}
