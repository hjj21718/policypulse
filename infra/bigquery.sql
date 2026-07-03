CREATE SCHEMA IF NOT EXISTS `PROJECT_ID.policypulse`;

CREATE TABLE IF NOT EXISTS `PROJECT_ID.policypulse.sentiment_events` (
  event_id STRING,
  created_at TIMESTAMP,
  query STRING,
  record_count INT64,
  overall_sentiment STRING,
  themes ARRAY<STRING>,
  summary STRING,
  recommendation STRING,
  raw_payload JSON
);
