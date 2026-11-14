CREATE TABLE sat_coverage
(
  coverage_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  coverage_type STRING,
  coverage_description STRING,
  coverage_start_date DATE,
  coverage_end_date DATE,
  coverage_type_id STRING,
  maximum_deductible DOUBLE,
  limit_id STRING,
  exclusion_id STRING,
  deductible_id STRING,
  benefit_id STRING,
  risk_id STRING,
  peril_id STRING,
  product_element_id STRING
)
USING DELTA;

ALTER TABLE sat_coverage
ADD CONSTRAINT XPKSAT_COVERAGE PRIMARY KEY (coverage_hash_key, load_ts);

ALTER TABLE sat_coverage
ADD CONSTRAINT FK_sat_coverage__crm_coverage_catalog_csv
FOREIGN KEY (coverage_hash_key)
REFERENCES crm_coverage_catalog_csv (coverage_identifier_source_name);
