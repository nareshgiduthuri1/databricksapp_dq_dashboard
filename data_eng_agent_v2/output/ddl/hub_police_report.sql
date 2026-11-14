CREATE TABLE hub_police_report
(
  police_report_hash_key STRING NOT NULL,
  police_report_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_police_report
ADD CONSTRAINT XPKHUB_POLICE_REPORT PRIMARY KEY (police_report_hash_key);
