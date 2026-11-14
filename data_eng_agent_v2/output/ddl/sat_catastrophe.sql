CREATE TABLE sat_catastrophe
(
  catastrophe_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  catastrophe_cause STRING,
  catastrophe_description STRING,
  catastrophe_begin_date DATE,
  catastrophe_end_date DATE,
  cresta_zone STRING,
  nat_cat_event_code STRING
);

ALTER TABLE sat_catastrophe
ADD CONSTRAINT XPKSAT_CATASTROPHE PRIMARY KEY (catastrophe_hash_key, load_ts);

ALTER TABLE sat_catastrophe
ADD CONSTRAINT FK_SAT_CATASTROPHE__CRM_CATASTROPHE_EVENT_REGISTER_CSV
FOREIGN KEY (catastrophe_hash_key)
REFERENCES crm_catastrophe_event_register_csv (catastrophe_identifier_source_name);
