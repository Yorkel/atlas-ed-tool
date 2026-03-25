"""AtlasED Dashboard — FastAPI application."""

import json
from pathlib import Path
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import queries

app = FastAPI(title="AtlasED Dashboard")

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

BASELINE_MODEL = "eng_k30"
ELECTION_DATE = "2024-07-04"


# ── Page 1: Overview ──────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def overview(request: Request):
    stats = queries.get_overview_stats(BASELINE_MODEL)
    topics = queries.get_topics(BASELINE_MODEL)
    return templates.TemplateResponse("overview.html", {
        "request": request,
        "stats": stats,
        "topics": topics,
        "model_id": BASELINE_MODEL,
    })


# ── Page 2: Topics & Trends ──────────────────────────────────────────
@app.get("/topics", response_class=HTMLResponse)
async def topics_and_trends(request: Request):
    topics = queries.get_topics(BASELINE_MODEL)
    return templates.TemplateResponse("topics.html", {
        "request": request,
        "topics": topics,
        "election_date": ELECTION_DATE,
        "source_types": list(queries.SOURCES_BY_TYPE.keys()),
    })


# ── Page 3: Specification Sensitivity ────────────────────────────────
@app.get("/sensitivity", response_class=HTMLResponse)
async def sensitivity(request: Request):
    models = queries.get_models()
    all_topics = {}
    for m in models:
        all_topics[m["model_id"]] = queries.get_topics(m["model_id"])
    model_labels = {
        "eng_k30": "Main Model (30 topics)",
        "eng_k30_nm": "No Media",
        "eng_k5": "5 Topics",
        "eng_k15": "15 Topics",
    }
    return templates.TemplateResponse("sensitivity.html", {
        "request": request,
        "models": models,
        "all_topics_json": json.dumps(all_topics),
        "model_labels": model_labels,
        "baseline": BASELINE_MODEL,
    })


# ── Page 4: Ask the Data (RAG) ───────────────────────────────────────
@app.get("/ask", response_class=HTMLResponse)
async def ask_the_data(request: Request):
    rag_full = queries.get_rag_contexts("full")
    rag_nm = queries.get_rag_contexts("no_media")

    # Pair up questions: full vs no-media side by side
    questions = {}
    for r in rag_full:
        questions[r["question"]] = {"full": r}
    for r in rag_nm:
        if r["question"] in questions:
            questions[r["question"]]["no_media"] = r

    return templates.TemplateResponse("ask.html", {
        "request": request,
        "questions": questions,
    })


# ── Page 5: Implications ─────────────────────────────────────────────
@app.get("/implications", response_class=HTMLResponse)
async def implications(request: Request):
    return templates.TemplateResponse("implications.html", {
        "request": request,
    })


# ── API endpoints ─────────────────────────────────────────────────────
@app.get("/api/timeseries")
async def api_timeseries(
    model_id: str = BASELINE_MODEL,
    topic_nums: str = Query(default=""),
):
    nums = [int(n) for n in topic_nums.split(",") if n.strip().isdigit()] or None
    data = queries.get_timeseries(model_id, nums)
    return data


@app.get("/api/top_topics")
async def api_top_topics(
    source_type: str = Query(default=""),
    year: str = Query(default=""),
):
    model = queries.get_model(BASELINE_MODEL)
    run_id = model["run_id"]

    sources = None
    if source_type and source_type in queries.SOURCES_BY_TYPE:
        sources = queries.SOURCES_BY_TYPE[source_type]

    date_from = f"{year}-01-01" if year else None
    date_to = f"{year}-12-31" if year else None

    return queries.get_top_topics_filtered(run_id, sources, date_from, date_to)


@app.get("/api/trends")
async def api_trends(
    source_type: str = Query(default=""),
    year: str = Query(default=""),
    topic_nums: str = Query(default=""),
):
    model = queries.get_model(BASELINE_MODEL)
    run_id = model["run_id"]

    sources = None
    if source_type and source_type in queries.SOURCES_BY_TYPE:
        sources = queries.SOURCES_BY_TYPE[source_type]

    date_from = f"{year}-01-01" if year else None
    date_to = f"{year}-12-31" if year else None

    nums = [int(n) for n in topic_nums.split(",") if n.strip().isdigit()] or None

    return queries.get_trend_data_filtered(run_id, sources, date_from, date_to, nums)
