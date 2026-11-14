CREATE TABLE hub_loss_event
(
  loss_event_hash_key STRING NOT NULL,
  loss_event_id STRING,
  load_ts TIMESTAMP,
  record_source STRING
);

ALTER TABLE hub_loss_event
ADD CONSTRAINT XPKHUB_LOSS_EVENT PRIMARY KEY (loss_event_hash_key);
