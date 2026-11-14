CREATE TABLE sat_claim_event
(
  claim_event_hash_key STRING NOT NULL,
  load_ts TIMESTAMP NOT NULL,
  record_source STRING,
  event_type STRING,
  event_date DATE,
  event_description STRING
);

ALTER TABLE sat_claim_event
ADD CONSTRAINT XPKSAT_CLAIM_EVENT PRIMARY KEY (claim_event_hash_key, load_ts);

ALTER TABLE sat_claim_event
ADD CONSTRAINT FK_SAT_CLAIM_EVENT__CRM_CLAIM_EVENT_LOG_CSV
FOREIGN KEY (claim_event_hash_key)
REFERENCES crm_claim_event_log_csv (claim_event_identifier);
