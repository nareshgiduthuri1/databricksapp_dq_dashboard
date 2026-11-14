CREATE TABLE sat_repair
(
  repair_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  number_of_spare_parts_repaired BIGINT,
  paid_spare_parts_costs DOUBLE,
  spare_part_repair_shop_price DOUBLE,
  spare_part_type STRING
);

ALTER TABLE sat_repair
ADD CONSTRAINT XPKSAT_REPAIR PRIMARY KEY (repair_hash_key, load_ts);

ALTER TABLE sat_repair
ADD CONSTRAINT FK_SAT_REPAIR__CRM_REPAIR_REGISTER_CSV
FOREIGN KEY (repair_hash_key)
REFERENCES crm_repair_register_csv (repair_identifier_source_name);
