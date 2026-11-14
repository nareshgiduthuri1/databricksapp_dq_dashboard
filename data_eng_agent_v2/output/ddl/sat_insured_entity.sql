CREATE TABLE sat_insured_entity
(
  insured_entity_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  entity_type STRING,
  insured_person_identifier STRING,
  insured_object_owner_identifier STRING,
  insured_object_address_flag STRING,
  insured_object_sum_insured DOUBLE,
  exposure_base STRING,
  grouped_location_flag STRING,
  replacement_value DOUBLE,
  type_of_insured_entity STRING,
  value_of_content DOUBLE,
  value_of_goods_carried DOUBLE,
  actual_pre_event_entity_value DOUBLE,
  damaged_entity STRING,
  insured_object_desc STRING,
  insured_object_current_status STRING,
  insured_object_start_date STRING,
  insured_object_end_date STRING,
  wall_construction_material_type STRING,
  home_risk_address STRING,
  home_type STRING,
  home_state STRING,
  vehicle_body_type STRING,
  vehicle_fuel_type STRING,
  vehicle_risk_address STRING,
  vehicle_risk_class_code STRING,
  vehicle_variant STRING,
  vehicle_reg_state STRING,
  vehicle_class STRING,
  vehicle_model STRING
)
USING DELTA;

ALTER TABLE sat_insured_entity
ADD CONSTRAINT XPKSAT_INSURED_ENTITY PRIMARY KEY (insured_entity_hash_key, load_ts);

ALTER TABLE sat_insured_entity
ADD CONSTRAINT FK_SAT_INSURED_ENTITY__CRM_INSURED_ENTITY_REGISTER_CSV
FOREIGN KEY (insured_entity_hash_key)
REFERENCES crm_insured_entity_register_csv (insured_entity_identifier_source_name);
