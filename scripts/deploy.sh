#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${1:-}"
REGION="${2:-australia-southeast1}"
SERVICE="${3:-policypulse-api}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Usage: ./deploy.sh <PROJECT_ID> [REGION] [SERVICE]"
  exit 1
fi

gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com bigquery.googleapis.com

sed "s/PROJECT_ID/$PROJECT_ID/g" infra/bigquery.sql | bq query --use_legacy_sql=false

gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID="$PROJECT_ID",BQ_DATASET="policypulse",BQ_TABLE="sentiment_events"
