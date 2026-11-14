# Databricks notebook source
# DBTITLE 1,Hub Configs - Product ID 3

hub_catastrophe_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_catastrophe_3",
  "object_type": "hub",
  "target_table": "hub_catastrophe",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(catastrophe_identifier, origin_sys)) AS catastrophe_hash_key,
  catastrophe_identifier AS catastrophe_id,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source
FROM crm_catastrophe_event_register_csv
""",
  "source_table": "crm_catastrophe_event_register_csv"
}

hub_claim_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_claim_3",
  "object_type": "hub",
  "target_table": "hub_claim",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(claim_identifier, source_name)) AS claim_hash_key,
  claim_identifier AS claim_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_claim_register_csv
UNION ALL
SELECT
  md5(CONCAT(claim_ref_id, source_name)) AS claim_hash_key,
  claim_ref_id AS claim_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM sap_claim_db
""",
  "source_table": "crm_claim_register_csv,sap_claim_db"
}

hub_claim_event_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_claim_event_3",
  "object_type": "hub",
  "target_table": "hub_claim_event",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(claim_event_identifier, source_name)) AS claim_event_hash_key,
  claim_event_identifier AS claim_event_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_claim_event_log_csv
""",
  "source_table": "crm_claim_event_log_csv"
}

hub_claim_investigation_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_claim_investigation_3",
  "object_type": "hub",
  "target_table": "hub_claim_investigation",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(claim_investigation_identifier, source_name)) AS claim_investigation_hash_key,
  claim_investigation_identifier AS claim_investigation_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_claim_investigation_register_csv

UNION ALL

SELECT
  md5(CONCAT(claim_ref_id, source_name)) AS claim_investigation_hash_key,
  claim_ref_id AS claim_investigation_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM sap_claim_investigation_db
""",
  "source_table": "crm_claim_investigation_register_csv,sap_claim_investigation_db"
}

hub_claim_participant_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_claim_participant_3",
  "object_type": "hub",
  "target_table": "hub_claim_participant",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(claim_participant_identifier, source_name)) AS claim_participant_hash_key,
  claim_participant_identifier AS claim_participant_id,
  CAST(load_ts AS timestamp) AS load_date,
  source_name AS record_source
FROM crm_claim_participant_register_csv
""",
  "source_table": "crm_claim_participant_register_csv"
}

hub_coverage_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_coverage_3",
  "object_type": "hub",
  "target_table": "hub_coverage",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(coverage_identifier, source_name)) AS coverage_hash_key,
  coverage_identifier AS coverage_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_coverage_catalog_csv
""",
  "source_table": "crm_coverage_catalog_csv"
}

hub_diagnosis_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_diagnosis_3",
  "object_type": "hub",
  "target_table": "hub_diagnosis",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(diagnosis_identifier, source_name)) AS diagnosis_hash_key,
  diagnosis_identifier AS diagnosis_id,
  CAST(load_ts AS TIMESTAMP) AS load_ts,
  source_name AS record_source
FROM crm_diagnosis_register_csv
""",
  "source_table": "crm_diagnosis_register_csv"
}

hub_health_insurance_claim_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_health_insurance_claim_3",
  "object_type": "hub",
  "target_table": "hub_health_insurance_claim",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(health_insurance_claim_identifier, source_name)) AS health_insurance_claim_hash_key,
  health_insurance_claim_identifier AS health_insurance_claim_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_health_claim_register_csv
""",
  "source_table": "crm_health_claim_register_csv"
}

hub_injury_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_injury_3",
  "object_type": "hub",
  "target_table": "hub_injury",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(injury_identifier, source_name)) AS injury_hash_key,
  injury_identifier AS injury_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_injury_register_csv
""",
  "source_table": "crm_injury_register_csv"
}

hub_insured_entity_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_insured_entity_3",
  "object_type": "hub",
  "target_table": "hub_insured_entity",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(insured_entity_identifier, source_name)) AS insured_entity_hash_key,
  insured_entity_identifier AS insured_entity_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_insured_entity_register_csv
""",
  "source_table": "crm_insured_entity_register_csv"
}

hub_litigation_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_litigation_3",
  "object_type": "hub",
  "target_table": "hub_litigation",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(litigation_identifier, source_name)) AS litigation_hash_key,
  litigation_identifier AS litigation_id,
  CAST(load_ts AS TIMESTAMP) AS load_ts,
  source_name AS record_source
FROM crm_litigation_register_csv
""",
  "source_table": "crm_litigation_register_csv"
}

hub_loss_event_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_loss_event_3",
  "object_type": "hub",
  "target_table": "hub_loss_event",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(loss_event_identifier, source_name)) AS loss_event_hash_key,
  loss_event_identifier AS loss_event_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_loss_event_register_csv

UNION ALL

SELECT
  md5(CONCAT(incident_id, source_name)) AS loss_event_hash_key,
  incident_id AS loss_event_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM sap_loss_event_db
""",
  "source_table": "crm_loss_event_register_csv,sap_loss_event_db"
}

hub_medical_assessment_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_medical_assessment_3",
  "object_type": "hub",
  "target_table": "hub_medical_assessment",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(medical_assessment_identifier, source_name)) AS medical_assessment_hash_key,
  medical_assessment_identifier AS medical_assessment_id,
  CAST(load_ts AS timestamp) AS load_date,
  source_name AS record_source
FROM crm_medical_assessment_register_csv
""",
  "source_table": "crm_medical_assessment_register_csv"
}

hub_medical_condition_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_medical_condition_3",
  "object_type": "hub",
  "target_table": "hub_medical_condition",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(medical_condition_identifier, source_name)) AS medical_condition_hash_key,
  medical_condition_identifier AS medical_condition_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_medical_condition_catalog_csv
""",
  "source_table": "crm_medical_condition_catalog_csv"
}

hub_medical_report_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_medical_report_3",
  "object_type": "hub",
  "target_table": "hub_medical_report",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(medical_report_identifier, source_name)) AS medical_report_hash_key,
  medical_report_identifier AS medical_report_id,
  load_ts,
  source_name AS record_source
FROM crm_medical_report_register_csv
""",
  "source_table": "crm_medical_report_register_csv"
}

hub_person_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_person_3",
  "object_type": "hub",
  "target_table": "hub_person",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(person_identifier, source_name)) AS person_hash_key,
  person_identifier AS person_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_party_master_csv
""",
  "source_table": "crm_party_master_csv"
}

hub_physical_place_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_physical_place_3",
  "object_type": "hub",
  "target_table": "hub_physical_place",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(physical_place_identifier, source_name)) AS physical_place_hash_key,
  physical_place_identifier AS physical_place_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_physical_place_register_csv
""",
  "source_table": "crm_physical_place_register_csv"
}

hub_police_report_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_police_report_3",
  "object_type": "hub",
  "target_table": "hub_police_report",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(police_report_identifier, source_name)) AS police_report_hash_key,
  police_report_identifier AS police_report_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_police_report_register_csv
""",
  "source_table": "crm_police_report_register_csv"
}

hub_policy_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_policy_3",
  "object_type": "hub",
  "target_table": "hub_policy",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(policy_identifier, source_name)) AS policy_hash_key,
  policy_identifier AS policy_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_policy_register_csv
""",
  "source_table": "crm_policy_register_csv"
}

hub_policy_coverage_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_policy_coverage_3",
  "object_type": "hub",
  "target_table": "hub_policy_coverage",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(policy_coverage_identifier, source_name)) AS policy_coverage_hash_key,
  policy_coverage_identifier AS policy_coverage_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_policy_coverage_register_csv
""",
  "source_table": "crm_policy_coverage_register_csv"
}

hub_repair_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_repair_3",
  "object_type": "hub",
  "target_table": "hub_repair",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(repair_identifier, source_name)) AS repair_hash_key,
  repair_identifier AS repair_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_repair_register_csv
""",
  "source_table": "crm_repair_register_csv"
}

hub_settlement_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_settlement_3",
  "object_type": "hub",
  "target_table": "hub_settlement",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(settlement_identifier, source_name)) AS settlement_hash_key,
  settlement_identifier AS settlement_id,
  CAST(load_ts AS timestamp) AS load_ts,
  source_name AS record_source
FROM crm_settlement_register_csv
""",
  "source_table": "crm_settlement_register_csv"
}

hub_treatment_3 =  {
  "product_id": "3",
  "vault_object_id": "hub_treatment_3",
  "object_type": "hub",
  "target_table": "hub_treatment",
  "process_order": "1",
  "build_sql": f"""
SELECT
  md5(CONCAT(treatment_identifier, source_name)) AS treatment_hash_key,
  treatment_identifier AS treatment_id,
  CAST(load_ts AS timestamp) AS load_date,
  source_name AS record_source
FROM crm_treatment_register_csv
""",
  "source_table": "crm_treatment_register_csv"
}
