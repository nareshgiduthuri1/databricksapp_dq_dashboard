CREATE TABLE sat_physical_place
(
  physical_place_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  place_id STRING,
  city STRING,
  state STRING,
  country STRING,
  applicable_jurisdiction STRING,
  census_zone STRING,
  commune_code STRING,
  geocoding_level STRING,
  latitude DOUBLE,
  longitude DOUBLE,
  municipal_district STRING,
  natcat_hazard_zone_scheme STRING,
  point_of_interest STRING,
  possible_max_business_interruption DOUBLE,
  sub_region STRING,
  surface_elevation DOUBLE
)
USING DELTA;

ALTER TABLE sat_physical_place
ADD CONSTRAINT XPKSAT_PHYSICAL_PLACE PRIMARY KEY (physical_place_hash_key, load_ts);

ALTER TABLE sat_physical_place
ADD CONSTRAINT FK_SAT_PHYSICAL_PLACE__CRM_PHYSICAL_PLACE_REGISTER_CSV
FOREIGN KEY (physical_place_hash_key)
REFERENCES crm_physical_place_register_csv (physical_place_identifier_source_name);
