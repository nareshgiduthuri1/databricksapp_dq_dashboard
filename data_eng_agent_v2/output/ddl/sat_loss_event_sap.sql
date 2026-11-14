CREATE TABLE sat_loss_event_sap
(
  loss_event_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  incident_name STRING,
  incident_description STRING,
  event_date DATE,
  event_time TIMESTAMP,
  incident_start_date DATE,
  incident_end_date DATE,
  incident_status STRING,
  event_type STRING,
  incident_category STRING,
  root_cause STRING,
  liability_cause STRING,
  reported_date DATE,
  reporting_channel STRING,
  days_to_fnol BIGINT,
  notification_duration BIGINT,
  casualty_indicator STRING,
  catastrophe_flag STRING,
  natcat_flag STRING,
  event_severity_low_flag STRING,
  casualty_count BIGINT,
  impacted_person_count BIGINT,
  impacted_vehicle_count BIGINT,
  impairment_flag STRING,
  shared_liability_flag STRING,
  impact_description STRING
)
USING DELTA;

ALTER TABLE sat_loss_event_sap
ADD CONSTRAINT XPKSAT_LOSS_EVENT_SAP PRIMARY KEY (loss_event_hash_key, load_ts);

ALTER TABLE sat_loss_event_sap
ADD CONSTRAINT FK_SAT_LOSS_EVENT_SAP__SAP_LOSS_EVENT_DB
FOREIGN KEY (loss_event_hash_key)
REFERENCES sap_loss_event_db (incident_id_source_name);
