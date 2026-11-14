CREATE TABLE sat_injury
(
  injury_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  bodily_injury_date DATE,
  injury_description STRING
);

ALTER TABLE sat_injury
ADD CONSTRAINT XPKSAT_INJURY PRIMARY KEY (injury_hash_key, load_ts);

ALTER TABLE sat_injury
ADD CONSTRAINT FK_SAT_INJURY__CRM_INJURY_REGISTER_CSV
FOREIGN KEY (injury_hash_key)
REFERENCES crm_injury_register_csv (injury_identifier_source_name);
