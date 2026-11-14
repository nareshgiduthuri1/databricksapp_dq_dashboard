CREATE TABLE sat_litigation
(
  litigation_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  court_matter_type STRING,
  date_of_legal_representation DATE,
  first_litigation_date DATE,
  litigation_date DATE,
  decision_of_court STRING,
  litigation_start_date DATE,
  litigation_end_date DATE
)
USING DELTA;

ALTER TABLE sat_litigation
ADD CONSTRAINT XPKSAT_LITIGATION PRIMARY KEY (litigation_hash_key, load_ts);

ALTER TABLE sat_litigation
ADD CONSTRAINT FK_sat_litigation__crm_litigation_register_csv
FOREIGN KEY (litigation_hash_key)
REFERENCES crm_litigation_register_csv (litigation_identifier_source_name);
