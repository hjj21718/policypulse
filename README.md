# PolicyPulse starter deployment

This is a starter implementation for the hackathon concept: a Google Cloud multi-agent public sentiment intelligence application. It uses a FastAPI service on Cloud Run and writes analysis results into BigQuery.

## Project structure
- `app/main.py`
- `app/requirements.txt`
- `Dockerfile`
- `infra/bigquery.sql`
- `scripts/deploy.sh`

## Local run
```bash
cd output/policypulse
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## Test locally
```bash
curl http://127.0.0.1:8080/health

curl -X POST http://127.0.0.1:8080/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What do people think about the half-price public transport policy?",
    "records": [
      {"source_type":"reddit","content":"This is helpful and more affordable for families."},
      {"source_type":"news","content":"Citizens appreciate the cost relief but some complain about crowded services."}
    ]
  }'
```

## Deploy to Cloud Run
```bash
cd output/policypulse
./scripts/deploy.sh YOUR_PROJECT_ID australia-southeast1 policypulse-api
```
