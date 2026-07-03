import os
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

try:
    from google.cloud import bigquery
except Exception:
    bigquery = None

app = FastAPI(title="PolicyPulse API", version="0.1.0")

PROJECT_ID = os.getenv("PROJECT_ID", "local-project")
BQ_DATASET = os.getenv("BQ_DATASET", "policypulse")
BQ_TABLE = os.getenv("BQ_TABLE", "sentiment_events")

class SourceRecord(BaseModel):
    source_type: str
    source_uri: Optional[str] = None
    content: str
    region: Optional[str] = None
    policy_name: Optional[str] = None

class AnalyzeRequest(BaseModel):
    query: str
    records: List[SourceRecord]

class AgentResult(BaseModel):
    summary: str
    themes: List[str]
    sentiment: str
    recommendation: str


def simple_sentiment(text: str) -> str:
    t = text.lower()
    pos = sum(w in t for w in ["good", "great", "support", "helpful", "affordable", "positive", "appreciate"])
    neg = sum(w in t for w in ["bad", "expensive", "angry", "delay", "worse", "negative", "complaint"])
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def extract_themes(text: str) -> List[str]:
    mapping = {
        "cost": ["cost", "price", "afford", "fuel", "fare"],
        "service quality": ["delay", "late", "crowded", "service"],
        "accessibility": ["access", "elderly", "disability", "accessible"],
        "communication": ["confusing", "unclear", "announcement", "communication"],
        "community benefit": ["helpful", "benefit", "support", "community"],
    }
    found = []
    tl = text.lower()
    for theme, kws in mapping.items():
        if any(k in tl for k in kws):
            found.append(theme)
    return found or ["general sentiment"]


def summarize(records: List[SourceRecord], query: str) -> AgentResult:
    sentiments = [simple_sentiment(r.content) for r in records]
    overall = max(set(sentiments), key=sentiments.count) if sentiments else "neutral"
    theme_set = []
    for r in records:
        for theme in extract_themes(r.content):
            if theme not in theme_set:
                theme_set.append(theme)
    summary = f"For '{query}', overall public sentiment appears {overall} across {len(records)} records, with recurring themes around {', '.join(theme_set[:4])}."
    recommendation = "Review the dominant concerns, validate them with stakeholders, and consider targeted communication or policy refinement for the top negative themes."
    return AgentResult(summary=summary, themes=theme_set[:5], sentiment=overall, recommendation=recommendation)


def write_bq(payload: dict):
    if bigquery is None:
        return {"status": "skipped", "reason": "google-cloud-bigquery not installed"}
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
    errors = client.insert_rows_json(table_id, [payload])
    return {"status": "ok" if not errors else "error", "errors": errors}


@app.get("/health")
def health():
    return {"status": "ok", "service": "policypulse-api"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    result = summarize(req.records, req.query)
    event = {
        "event_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "query": req.query,
        "record_count": len(req.records),
        "overall_sentiment": result.sentiment,
        "themes": result.themes,
        "summary": result.summary,
        "recommendation": result.recommendation,
        "raw_payload": json.dumps(req.model_dump()),
    }
    bq_status = write_bq(event)
    return {"result": result.model_dump(), "storage": bq_status}
