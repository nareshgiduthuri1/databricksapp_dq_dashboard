CREATE TABLE link_injury_diagnosis
(
  injury_diagnosis_hash_key STRING NOT NULL,
  injury_hash_key STRING,
  diagnosis_hash_key STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE link_injury_diagnosis
ADD CONSTRAINT XPKLINK_INJURY_DIAGNOSIS PRIMARY KEY (injury_diagnosis_hash_key);

ALTER TABLE link_injury_diagnosis
ADD CONSTRAINT FK_LINK_INJURY_DIAGNOSIS__CRM_INJURY_REGISTER_CSV
FOREIGN KEY (injury_hash_key)
REFERENCES crm_injury_register_csv (injury_identifier_source_name);

ALTER TABLE link_injury_diagnosis
ADD CONSTRAINT FK_LINK_INJURY_DIAGNOSIS__CRM_DIAGNOSIS_REGISTER_CSV
FOREIGN KEY (diagnosis_hash_key)
REFERENCES crm_diagnosis_register_csv (diagnosis_identifier_source_name);
