# Databricks notebook source
# DBTITLE 1,Link Configs - Product ID 3

link_loss_event_catastrophe_3 =  {
  "product_id": "3",
  "vault_object_id": "link_loss_event_catastrophe_3",
  "object_type": "link",
  "target_table": "link_loss_event_catastrophe",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(loss_event_identifier, source_name)) AS loss_event_hash_key,
    md5(CONCAT(catastrophe_identifier, source_name)) AS catastrophe_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_loss_event_register_csv a
  INNER JOIN crm_catastrophe_event_register_csv b
    ON a.loss_event_identifier = b.loss_event_identifier

  UNION ALL

  SELECT
    md5(CONCAT(incident_id, source_name)) AS loss_event_hash_key,
    md5(CONCAT(catastrophe_identifier, source_name)) AS catastrophe_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM sap_loss_event_db a
  INNER JOIN crm_catastrophe_event_register_csv b
    ON a.incident_id = b.loss_event_identifier
)
SELECT
  md5(CONCAT(loss_event_hash_key, catastrophe_hash_key, origin_sys)) AS loss_event_catastrophe_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  loss_event_hash_key,
  catastrophe_hash_key
FROM combined
""",
  "source_table": "crm_loss_event_register_csv,sap_loss_event_db,crm_catastrophe_event_register_csv"
}

link_policy_claim_3 =  {
  "product_id": "3",
  "vault_object_id": "link_policy_claim_3",
  "object_type": "link",
  "target_table": "link_policy_claim",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(a.policy_identifier, a.source_name)) AS policy_hash_key,
    md5(CONCAT(a.claim_identifier, a.source_name)) AS claim_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM crm_claim_register_csv a
  INNER JOIN crm_policy_register_csv b
    ON a.policy_identifier = b.policy_identifier

  UNION ALL

  SELECT
    md5(CONCAT(b.policy_identifier, b.source_name)) AS policy_hash_key,
    md5(CONCAT(a.claim_ref_id, a.source_name)) AS claim_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM sap_claim_db a
  INNER JOIN crm_policy_register_csv b
    ON a.policy_reference = b.policy_identifier
)
SELECT
  md5(CONCAT(policy_hash_key, claim_hash_key, origin_sys)) AS policy_claim_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  policy_hash_key,
  claim_hash_key
FROM combined
""",
  "source_table": "crm_policy_register_csv,crm_claim_register_csv,sap_claim_db"
}

link_claim_claim_event_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_claim_event_3",
  "object_type": "link",
  "target_table": "link_claim_claim_event",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(a.claim_identifier, a.source_name)) AS claim_hash_key,
    md5(CONCAT(b.claim_event_identifier, b.source_name)) AS claim_event_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM crm_claim_register_csv a
  INNER JOIN crm_claim_event_log_csv b
    ON a.claim_identifier = b.claim_identifier

  UNION ALL

  SELECT
    md5(CONCAT(a.claim_ref_id, a.source_name)) AS claim_hash_key,
    md5(CONCAT(b.claim_event_identifier, b.source_name)) AS claim_event_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM sap_claim_db a
  INNER JOIN crm_claim_event_log_csv b
    ON a.claim_ref_id = b.claim_identifier
)
SELECT
  md5(CONCAT(claim_hash_key, claim_event_hash_key, origin_sys)) AS claim_claim_event_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_hash_key,
  claim_event_hash_key
FROM combined
""",
  "source_table": "crm_claim_register_csv,sap_claim_db,crm_claim_event_log_csv"
}

link_claim_event_claim_investigation_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_event_claim_investigation_3",
  "object_type": "link",
  "target_table": "link_claim_event_claim_investigation",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(a.claim_event_identifier, a.source_name)) AS claim_event_hash_key,
    md5(CONCAT(b.claim_investigation_identifier, b.source_name)) AS claim_investigation_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM crm_claim_event_log_csv a
  INNER JOIN crm_claim_investigation_register_csv b
    ON a.claim_event_identifier = b.claim_event_identifier

  UNION ALL

  SELECT
    md5(CONCAT(a.claim_event_identifier, a.source_name)) AS claim_event_hash_key,
    md5(CONCAT(b.claim_ref_id, b.source_name)) AS claim_investigation_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM crm_claim_event_log_csv a
  INNER JOIN sap_claim_investigation_db b
    ON a.claim_event_identifier = b.case_event_id
)
SELECT
  md5(CONCAT(claim_event_hash_key, claim_investigation_hash_key, origin_sys)) AS claim_event_claim_investigation_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_event_hash_key,
  claim_investigation_hash_key
FROM combined
""",
  "source_table": "crm_claim_investigation_register_csv,sap_claim_investigation_db,crm_claim_event_log_csv"
}

link_person_claim_participant_3 =  {
  "product_id": "3",
  "vault_object_id": "link_person_claim_participant_3",
  "object_type": "link",
  "target_table": "link_person_claim_participant",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(person_identifier, source_name)) AS person_hash_key,
    md5(CONCAT(claim_participant_identifier, source_name)) AS claim_participant_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_party_master_csv
  INNER JOIN crm_claim_participant_register_csv
    ON crm_party_master_csv.person_identifier = crm_claim_participant_register_csv.person_identifier
)
SELECT
  md5(CONCAT(person_hash_key, claim_participant_hash_key, origin_sys)) AS person_claim_participant_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  person_hash_key,
  claim_participant_hash_key
FROM combined
""",
  "source_table": "crm_party_master_csv,crm_claim_participant_register_csv"
}

link_claim_claim_participant_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_claim_participant_3",
  "object_type": "link",
  "target_table": "link_claim_claim_participant",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(a.claim_identifier, a.source_name)) AS claim_hash_key,
    md5(CONCAT(b.claim_participant_identifier, b.source_name)) AS claim_participant_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM crm_claim_register_csv a
  INNER JOIN crm_claim_participant_register_csv b
    ON a.claim_identifier = b.claim_identifier

  UNION ALL

  SELECT
    md5(CONCAT(a.claim_ref_id, a.source_name)) AS claim_hash_key,
    md5(CONCAT(b.claim_participant_identifier, b.source_name)) AS claim_participant_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM sap_claim_db a
  INNER JOIN crm_claim_participant_register_csv b
    ON a.claim_ref_id = b.claim_identifier
)
SELECT
  md5(CONCAT(claim_hash_key, claim_participant_hash_key)) AS claim_claim_participant_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_hash_key,
  claim_participant_hash_key
FROM combined
""",
  "source_table": "crm_claim_register_csv,sap_claim_db,crm_claim_participant_register_csv"
}

link_medical_condition_diagnosis_3 =  {
  "product_id": "3",
  "vault_object_id": "link_medical_condition_diagnosis_3",
  "object_type": "link",
  "target_table": "link_medical_condition_diagnosis",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(medical_condition_identifier, source_name)) AS medical_condition_hash_key,
    md5(CONCAT(diagnosis_identifier, source_name)) AS diagnosis_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_medical_condition_catalog_csv a
  INNER JOIN crm_diagnosis_register_csv b
  ON a.medical_condition_identifier = b.medical_condition_identifier
)
SELECT
  md5(CONCAT(medical_condition_hash_key, diagnosis_hash_key, origin_sys)) AS medical_condition_diagnosis_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  medical_condition_hash_key,
  diagnosis_hash_key
FROM combined
""",
  "source_table": "crm_medical_condition_catalog_csv,crm_diagnosis_register_csv"
}

link_injury_diagnosis_3 =  {
  "product_id": "3",
  "vault_object_id": "link_injury_diagnosis_3",
  "object_type": "link",
  "target_table": "link_injury_diagnosis",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(injury_identifier, source_name)) AS injury_hash_key,
    md5(CONCAT(diagnosis_identifier, source_name)) AS diagnosis_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_injury_register_csv a
  INNER JOIN crm_diagnosis_register_csv b
    ON a.injury_identifier = b.injury_identifier
)
SELECT
  md5(CONCAT(injury_hash_key, diagnosis_hash_key, origin_sys)) AS injury_diagnosis_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  injury_hash_key,
  diagnosis_hash_key
FROM combined
""",
  "source_table": "crm_injury_register_csv,crm_diagnosis_register_csv"
}

link_claim_health_insurance_claim_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_health_insurance_claim_3",
  "object_type": "link",
  "target_table": "link_claim_health_insurance_claim",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(a.claim_identifier, b.health_insurance_claim_identifier)) AS claim_health_insurance_claim_hash_key,
    md5(CONCAT(a.claim_identifier, a.source_name)) AS claim_hash_key,
    md5(CONCAT(b.health_insurance_claim_identifier, b.source_name)) AS health_insurance_claim_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM crm_claim_register_csv a
  INNER JOIN crm_health_claim_register_csv b
    ON a.claim_identifier = b.claim_identifier

  UNION ALL

  SELECT
    md5(CONCAT(a.claim_ref_id, b.health_insurance_claim_identifier)) AS claim_health_insurance_claim_hash_key,
    md5(CONCAT(a.claim_ref_id, a.source_name)) AS claim_hash_key,
    md5(CONCAT(b.health_insurance_claim_identifier, b.source_name)) AS health_insurance_claim_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM sap_claim_db a
  INNER JOIN crm_health_claim_register_csv b
    ON a.claim_ref_id = b.claim_identifier
)
SELECT
  md5(CONCAT(claim_hash_key, health_insurance_claim_hash_key, origin_sys)) AS claim_health_insurance_claim_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_hash_key,
  health_insurance_claim_hash_key
FROM combined
""",
  "source_table": "crm_claim_register_csv,sap_claim_db,crm_health_claim_register_csv"
}

link_claim_event_injury_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_event_injury_3",
  "object_type": "link",
  "target_table": "link_claim_event_injury",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(claim_event_identifier, source_name)) AS claim_event_hash_key,
    md5(CONCAT(injury_identifier, source_name)) AS injury_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_claim_event_log_csv a
  INNER JOIN crm_injury_register_csv b
    ON a.claim_event_identifier = b.claim_event_identifier
)
SELECT
  md5(CONCAT(claim_event_hash_key, injury_hash_key, origin_sys)) AS claim_event_injury_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_event_hash_key,
  injury_hash_key
FROM combined
""",
  "source_table": "crm_claim_event_log_csv,crm_injury_register_csv"
}

link_claim_litigation_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_litigation_3",
  "object_type": "link",
  "target_table": "link_claim_litigation",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(claim_identifier, source_name)) AS claim_hash_key,
    md5(CONCAT(litigation_identifier, source_name)) AS litigation_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_claim_register_csv a
  INNER JOIN crm_litigation_register_csv b
    ON a.claim_identifier = b.claim_identifier

  UNION ALL

  SELECT
    md5(CONCAT(claim_ref_id, a.source_name)) AS claim_hash_key,
    md5(CONCAT(litigation_identifier, b.source_name)) AS litigation_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM sap_claim_db a
  INNER JOIN crm_litigation_register_csv b
    ON a.claim_ref_id = b.claim_identifier
)
SELECT
  md5(CONCAT(claim_hash_key, litigation_hash_key, origin_sys)) AS claim_litigation_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_hash_key,
  litigation_hash_key
FROM combined
""",
  "source_table": "crm_claim_register_csv,sap_claim_db,crm_litigation_register_csv"
}

link_claim_event_litigation_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_event_litigation_3",
  "object_type": "link",
  "target_table": "link_claim_event_litigation",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(claim_event_identifier, source_name)) AS claim_event_hash_key,
    md5(CONCAT(litigation_identifier, source_name)) AS litigation_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_claim_event_log_csv a
  INNER JOIN crm_litigation_register_csv b
    ON a.claim_event_identifier = b.claim_event_identifier
)
SELECT
  md5(CONCAT(claim_event_hash_key, litigation_hash_key, origin_sys)) AS claim_event_litigation_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_event_hash_key,
  litigation_hash_key
FROM combined
""",
  "source_table": "crm_claim_event_log_csv,crm_litigation_register_csv"
}

link_claim_loss_event_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_loss_event_3",
  "object_type": "link",
  "target_table": "link_claim_loss_event",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(claim_identifier, source_name)) AS claim_hash_key,
    md5(CONCAT(loss_event_identifier, source_name)) AS loss_event_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_claim_register_csv a
  INNER JOIN crm_loss_event_register_csv b
    ON a.claim_identifier = b.claim_identifier

  UNION ALL

  SELECT
    md5(CONCAT(claim_identifier, source_name)) AS claim_hash_key,
    md5(CONCAT(incident_id, source_name)) AS loss_event_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM crm_claim_register_csv a
  INNER JOIN sap_loss_event_db b
    ON a.claim_identifier = b.claim_reference

  UNION ALL

  SELECT
    md5(CONCAT(claim_ref_id, source_name)) AS claim_hash_key,
    md5(CONCAT(loss_event_identifier, source_name)) AS loss_event_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM sap_claim_db a
  INNER JOIN crm_loss_event_register_csv b
    ON a.claim_ref_id = b.claim_identifier

  UNION ALL

  SELECT
    md5(CONCAT(claim_ref_id, source_name)) AS claim_hash_key,
    md5(CONCAT(incident_id, source_name)) AS loss_event_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM sap_claim_db a
  INNER JOIN sap_loss_event_db b
    ON a.claim_identifier = b.claim_reference
)
SELECT
  md5(CONCAT(claim_hash_key, loss_event_hash_key, origin_sys)) AS claim_loss_event_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_hash_key,
  loss_event_hash_key
FROM combined
""",
  "source_table": "crm_claim_register_csv,sap_claim_db,crm_loss_event_register_csv,sap_loss_event_db"
}

link_physical_place_loss_event_3 =  {
  "product_id": "3",
  "vault_object_id": "link_physical_place_loss_event_3",
  "object_type": "link",
  "target_table": "link_physical_place_loss_event",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(a.loss_event_identifier, b.physical_place_identifier, a.source_name)) AS loss_event_hash_key,
    md5(CONCAT(b.physical_place_identifier, b.source_name)) AS physical_place_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM crm_loss_event_register_csv a
  INNER JOIN crm_physical_place_register_csv b
    ON a.physical_place_identifier = b.physical_place_identifier

  UNION ALL

  SELECT
    md5(CONCAT(a.incident_id, b.physical_place_identifier, a.source_name)) AS loss_event_hash_key,
    md5(CONCAT(b.physical_place_identifier, b.source_name)) AS physical_place_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM sap_loss_event_db a
  INNER JOIN crm_physical_place_register_csv b
    ON a.physical_place_identifier = b.physical_place_identifier
)
SELECT
  md5(CONCAT(loss_event_hash_key, physical_place_hash_key, origin_sys)) AS physical_place_loss_event_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  physical_place_hash_key,
  loss_event_hash_key
FROM combined
""",
  "source_table": "crm_loss_event_register_csv,sap_loss_event_db,crm_physical_place_register_csv"
}

link_claim_event_medical_assessment_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_event_medical_assessment_3",
  "object_type": "link",
  "target_table": "link_claim_event_medical_assessment",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(claim_event_identifier, source_name)) AS claim_event_hash_key,
    md5(CONCAT(medical_assessment_identifier, source_name)) AS medical_assessment_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_claim_event_log_csv a
  INNER JOIN crm_medical_assessment_register_csv b
    ON a.claim_event_identifier = b.claim_event_identifier
)
SELECT
  md5(CONCAT(claim_event_hash_key, medical_assessment_hash_key, origin_sys)) AS claim_event_medical_assessment_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_event_hash_key,
  medical_assessment_hash_key
FROM combined
""",
  "source_table": "crm_claim_event_log_csv,crm_medical_assessment_register_csv"
}

link_claim_medical_report_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_medical_report_3",
  "object_type": "link",
  "target_table": "link_claim_medical_report",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(a.claim_identifier, a.source_name)) AS claim_hash_key,
    md5(CONCAT(b.medical_report_identifier, b.source_name)) AS medical_report_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM crm_claim_register_csv a
  INNER JOIN crm_medical_report_register_csv b
    ON a.claim_identifier = b.claim_identifier

  UNION ALL

  SELECT
    md5(CONCAT(a.claim_ref_id, a.source_name)) AS claim_hash_key,
    md5(CONCAT(b.medical_report_identifier, b.source_name)) AS medical_report_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM sap_claim_db a
  INNER JOIN crm_medical_report_register_csv b
    ON a.claim_ref_id = b.claim_identifier
)
SELECT
  md5(CONCAT(claim_hash_key, medical_report_hash_key, origin_sys)) AS claim_medical_report_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_hash_key,
  medical_report_hash_key
FROM combined
""",
  "source_table": "crm_claim_register_csv,sap_claim_db,crm_medical_report_register_csv"
}

link_claim_police_report_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_police_report_3",
  "object_type": "link",
  "target_table": "link_claim_police_report",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(a.claim_identifier, a.source_name)) AS claim_hash_key,
    md5(CONCAT(b.police_report_identifier, b.source_name)) AS police_report_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM crm_claim_register_csv a
  INNER JOIN crm_police_report_register_csv b
    ON a.claim_identifier = b.claim_identifier

  UNION ALL

  SELECT
    md5(CONCAT(a.claim_ref_id, a.source_name)) AS claim_hash_key,
    md5(CONCAT(b.police_report_identifier, b.source_name)) AS police_report_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM sap_claim_db a
  INNER JOIN crm_police_report_register_csv b
    ON a.claim_ref_id = b.claim_identifier
)
SELECT
  md5(CONCAT(claim_hash_key, police_report_hash_key, origin_sys)) AS claim_police_report_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_hash_key,
  police_report_hash_key
FROM combined
""",
  "source_table": "crm_claim_register_csv,sap_claim_db,crm_police_report_register_csv"
}

link_coverage_policy_coverage_3 =  {
  "product_id": "3",
  "vault_object_id": "link_coverage_policy_coverage_3",
  "object_type": "link",
  "target_table": "link_coverage_policy_coverage",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(coverage_identifier, source_name)) AS coverage_hash_key,
    md5(CONCAT(policy_coverage_identifier, source_name)) AS policy_coverage_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_coverage_catalog_csv
  INNER JOIN crm_policy_coverage_register_csv
    ON crm_coverage_catalog_csv.coverage_identifier = crm_policy_coverage_register_csv.coverage_identifier
)
SELECT
  md5(CONCAT(coverage_hash_key, policy_coverage_hash_key, origin_sys)) AS coverage_policy_coverage_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  coverage_hash_key,
  policy_coverage_hash_key
FROM combined
""",
  "source_table": "crm_coverage_catalog_csv,crm_policy_coverage_register_csv"
}

link_insured_entity_policy_coverage_3 =  {
  "product_id": "3",
  "vault_object_id": "link_insured_entity_policy_coverage_3",
  "object_type": "link",
  "target_table": "link_insured_entity_policy_coverage",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(a.insured_entity_identifier, a.source_name)) AS insured_entity_hash_key,
    md5(CONCAT(b.policy_coverage_identifier, b.source_name)) AS policy_coverage_hash_key,
    a.load_ts AS pull_ts,
    a.source_name AS origin_sys
  FROM crm_insured_entity_register_csv a
  INNER JOIN crm_policy_coverage_register_csv b
    ON a.insured_entity_identifier = b.insured_entity_identifier
)
SELECT
  md5(CONCAT(insured_entity_hash_key, policy_coverage_hash_key)) AS insured_entity_policy_coverage_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  insured_entity_hash_key,
  policy_coverage_hash_key
FROM combined
""",
  "source_table": "crm_insured_entity_register_csv,crm_policy_coverage_register_csv"
}

link_policy_policy_coverage_3 =  {
  "product_id": "3",
  "vault_object_id": "link_policy_policy_coverage_3",
  "object_type": "link",
  "target_table": "link_policy_policy_coverage",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(policy_identifier, source_name)) AS policy_hash_key,
    md5(CONCAT(policy_coverage_identifier, source_name)) AS policy_coverage_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_policy_register_csv a
  INNER JOIN crm_policy_coverage_register_csv b
    ON a.policy_coverage_identifier = b.policy_coverage_identifier
)
SELECT
  md5(CONCAT(policy_hash_key, policy_coverage_hash_key, origin_sys)) AS policy_policy_coverage_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  policy_hash_key,
  policy_coverage_hash_key
FROM combined
""",
  "source_table": "crm_policy_register_csv,crm_policy_coverage_register_csv"
}

link_claim_event_repair_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_event_repair_3",
  "object_type": "link",
  "target_table": "link_claim_event_repair",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(claim_event_identifier, source_name)) AS claim_event_hash_key,
    md5(CONCAT(repair_identifier, source_name)) AS repair_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_claim_event_log_csv
  UNION ALL
  SELECT
    md5(CONCAT(claim_event_identifier, source_name)) AS claim_event_hash_key,
    md5(CONCAT(repair_identifier, source_name)) AS repair_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_repair_register_csv
)
SELECT
  md5(CONCAT(claim_event_hash_key, repair_hash_key)) AS claim_event_repair_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_event_hash_key,
  repair_hash_key
FROM combined
""",
  "source_table": "crm_claim_event_log_csv,crm_repair_register_csv"
}

link_claim_participant_repair_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_participant_repair_3",
  "object_type": "link",
  "target_table": "link_claim_participant_repair",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(claim_participant_identifier, source_name)) AS claim_participant_hash_key,
    md5(CONCAT(repair_identifier, source_name)) AS repair_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_claim_participant_register_csv a
  INNER JOIN crm_repair_register_csv b
    ON a.claim_participant_identifier = b.claim_participant_identifier
)
SELECT
  md5(CONCAT(claim_participant_hash_key, repair_hash_key, origin_sys)) AS claim_participant_repair_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_participant_hash_key,
  repair_hash_key
FROM combined
""",
  "source_table": "crm_claim_participant_register_csv,crm_repair_register_csv"
}

link_claim_event_settlement_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_event_settlement_3",
  "object_type": "link",
  "target_table": "link_claim_event_settlement",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(claim_event_identifier, source_name)) AS claim_event_hash_key,
    md5(CONCAT(settlement_identifier, source_name)) AS settlement_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_claim_event_log_csv a
  INNER JOIN crm_settlement_register_csv b
    ON a.claim_event_identifier = b.claim_event_identifier
)
SELECT
  md5(CONCAT(claim_event_hash_key, settlement_hash_key, origin_sys)) AS claim_event_settlement_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_event_hash_key,
  settlement_hash_key
FROM combined
""",
  "source_table": "crm_claim_event_log_csv,crm_settlement_register_csv"
}

link_claim_event_treatment_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_event_treatment_3",
  "object_type": "link",
  "target_table": "link_claim_event_treatment",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(a.claim_event_identifier, a.source_name)) AS claim_event_hash_key,
    md5(CONCAT(b.treatment_identifier, b.source_name)) AS treatment_hash_key,
    a.load_ts AS pull_ts,
    COALESCE(a.source_name, a.source_name) AS origin_sys
  FROM crm_claim_event_log_csv a
  INNER JOIN crm_treatment_register_csv b
    ON a.claim_event_identifier = b.claim_event_identifier
)
SELECT
  md5(CONCAT(claim_event_hash_key, treatment_hash_key)) AS claim_event_treatment_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_event_hash_key,
  treatment_hash_key
FROM combined
""",
  "source_table": "crm_claim_event_log_csv,crm_treatment_register_csv"
}

link_medical_condition_treatment_3 =  {
  "product_id": "3",
  "vault_object_id": "link_medical_condition_treatment_3",
  "object_type": "link",
  "target_table": "link_medical_condition_treatment",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(medical_condition_identifier, source_name)) AS medical_condition_hash_key,
    md5(CONCAT(treatment_identifier, source_name)) AS treatment_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_medical_condition_catalog_csv a
  INNER JOIN crm_treatment_register_csv b
    ON a.medical_condition_identifier = b.medical_condition_identifier
)
SELECT
  md5(CONCAT(medical_condition_hash_key, treatment_hash_key, origin_sys)) AS medical_condition_treatment_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  medical_condition_hash_key,
  treatment_hash_key
FROM combined
""",
  "source_table": "crm_medical_condition_catalog_csv,crm_treatment_register_csv"
}

link_claim_participant_treatment_3 =  {
  "product_id": "3",
  "vault_object_id": "link_claim_participant_treatment_3",
  "object_type": "link",
  "target_table": "link_claim_participant_treatment",
  "process_order": "2",
  "build_sql": f"""
WITH combined AS (
  SELECT
    md5(CONCAT(claim_participant_identifier, source_name)) AS claim_participant_hash_key,
    md5(CONCAT(treatment_identifier, source_name)) AS treatment_hash_key,
    load_ts AS pull_ts,
    source_name AS origin_sys
  FROM crm_claim_participant_register_csv a
  INNER JOIN crm_treatment_register_csv b
    ON a.claim_participant_identifier = b.claim_participant_identifier
)
SELECT
  md5(CONCAT(claim_participant_hash_key, treatment_hash_key)) AS claim_participant_treatment_hash_key,
  CAST(pull_ts AS timestamp) AS load_date,
  origin_sys AS record_source,
  claim_participant_hash_key,
  treatment_hash_key
FROM combined
""",
  "source_table": "crm_claim_participant_register_csv,crm_treatment_register_csv"
}
