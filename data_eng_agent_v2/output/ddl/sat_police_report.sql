CREATE TABLE sat_police_report
(
  police_report_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  police_report_number STRING,
  police_report_date DATE,
  police_report_flag STRING
);

ALTER TABLE sat_police_report
ADD CONSTRAINT XPKSAT_POLICE_REPORT PRIMARY KEY (police_report_hash_key, load_ts);

ALTER TABLE sat_police_report
ADD CONSTRAINT FK_SAT_POLICE_REPORT__CRM_POLICE_REPORT_REGISTER_CSV
FOREIGN KEY (police_report_hash_key)
REFERENCES crm_police_report_register_csv (police_report_identifier_source_name);
