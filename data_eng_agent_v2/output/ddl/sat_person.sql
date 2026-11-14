CREATE TABLE sat_person
(
  person_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  is_lead STRING,
  preferred_language STRING,
  source_identifier STRING,
  source_type STRING,
  tenant_identifier STRING,
  assessed_disability_degree STRING,
  is_operational_paperless_consent STRING,
  is_opt_in_legitimate_interest STRING,
  is_opt_in_validated STRING,
  person_type STRING,
  digital_id STRING,
  identification_type STRING,
  legal_consent_flag STRING,
  credit_rating STRING,
  credit_rating_provider STRING,
  rate_class STRING,
  person_status STRING,
  natural_ref STRING,
  first_name STRING,
  last_name STRING,
  full_name STRING,
  courtesy_title STRING,
  occupation STRING,
  birth_date DATE,
  birth_year BIGINT,
  nationality STRING,
  gender STRING,
  marital_status STRING,
  job_title STRING,
  role STRING,
  converted_date TIMESTAMP,
  person_score BIGINT,
  email_home STRING,
  email_work STRING,
  phone_work STRING,
  phone_home STRING,
  legal_ref STRING,
  company_name STRING,
  date_of_constitution TIMESTAMP,
  legal_job_title STRING,
  legal_src_ref STRING,
  legal_src_type STRING,
  legal_status STRING
)
USING DELTA;

ALTER TABLE sat_person
ADD CONSTRAINT XPKSAT_PERSON PRIMARY KEY (person_hash_key, load_ts);

ALTER TABLE sat_person
ADD CONSTRAINT FK_SAT_PERSON__CRM_PARTY_MASTER_CSV
FOREIGN KEY (person_hash_key)
REFERENCES crm_party_master_csv (person_identifier_source_name);
