CREATE TABLE sat_treatment
(
  treatment_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  treatment_code STRING,
  treatment_code_standard STRING,
  treatment_description STRING,
  treatment_complexity_level STRING,
  initial_treatment_date DATE,
  treatment_start_date DATE,
  number_of_treatments BIGINT,
  paid_treatment_amount DOUBLE,
  treatment_amount_currency STRING,
  medication_code STRING,
  treatment_type STRING
);

ALTER TABLE sat_treatment
ADD CONSTRAINT XPKSAT_TREATMENT PRIMARY KEY (treatment_hash_key, load_ts);

ALTER TABLE sat_treatment
ADD CONSTRAINT FK_sat_treatment__crm_treatment_register_csv
FOREIGN KEY (treatment_hash_key)
REFERENCES crm_treatment_register_csv (treatment_identifier_source_name);
