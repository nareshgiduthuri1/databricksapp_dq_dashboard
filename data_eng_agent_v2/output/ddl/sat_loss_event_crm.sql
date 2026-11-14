CREATE TABLE sat_loss_event_crm
(
  loss_event_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  loss_event_name STRING,
  loss_event_description STRING,
  loss_date DATE,
  loss_time TIMESTAMP,
  loss_event_start_date DATE,
  loss_event_end_date DATE,
  loss_event_status STRING,
  loss_type STRING,
  loss_category STRING,
  loss_cause STRING,
  property_liability_loss_cause STRING,
  effective_loss_date DATE,
  notification_date DATE,
  notification_channel STRING,
  fatality_flag STRING,
  minimal_impact_flag STRING,
  number_of_injured_parties BIGINT,
  number_of_people_involved BIGINT,
  number_of_vehicles_involved BIGINT,
  drugs_alcohol_indicator STRING,
  contributory_negligence_flag STRING,
  damage_specification STRING
)
USING DELTA;

ALTER TABLE sat_loss_event_crm
ADD CONSTRAINT XPKSAT_LOSS_EVENT_CRM PRIMARY KEY (loss_event_hash_key, load_ts);

ALTER TABLE sat_loss_event_crm
ADD CONSTRAINT FK_SAT_LOSS_EVENT_CRM__CRM_LOSS_EVENT_REGISTER_CSV
FOREIGN KEY (loss_event_hash_key)
REFERENCES crm_loss_event_register_csv (loss_event_identifier_source_name);
