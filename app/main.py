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


# ── Page 2a: Explore Topics ───────────────────────────────────────────
@app.get("/topics", response_class=HTMLResponse)
async def explore_topics(request: Request):
    topics = queries.get_topics(BASELINE_MODEL)
    return templates.TemplateResponse("topics.html", {
        "request": request,
        "topics": topics,
        "source_types": list(queries.SOURCES_BY_TYPE.keys()),
    })


# ── Page 2b: Explore Trends ──────────────────────────────────────────
@app.get("/trends", response_class=HTMLResponse)
async def explore_trends(request: Request):
    topics = queries.get_topics(BASELINE_MODEL)
    return templates.TemplateResponse("trends.html", {
        "request": request,
        "topics": topics,
    })


# ── Page 3: Specification Sensitivity ────────────────────────────────
@app.get("/sensitivity", response_class=HTMLResponse)
async def sensitivity(request: Request):
    k_models = ["eng_k5", "eng_k15", "eng_k30"]
    all_topics = {}
    for mid in k_models:
        all_topics[mid] = queries.get_topics(mid)
    models = [queries.get_model(mid) for mid in k_models]
    return templates.TemplateResponse("sensitivity.html", {
        "request": request,
        "models": [m for m in models if m],
        "all_topics_json": json.dumps(all_topics),
        "baseline": BASELINE_MODEL,
    })


# ── Page 4: Ask the Data (corpus comparison + RAG) ───────────────────
@app.get("/ask", response_class=HTMLResponse)
async def ask_the_data(request: Request):
    # Corpus comparison data
    topics_full = queries.get_topics("eng_k30")
    topics_nm = queries.get_topics("eng_k30_nm")
    model_full = queries.get_model("eng_k30")
    model_nm = queries.get_model("eng_k30_nm")

    # RAG data
    rag_full = queries.get_rag_contexts("full")
    rag_nm = queries.get_rag_contexts("no_media")

    questions = {}
    for r in rag_full:
        questions[r["question"]] = {"full": r}
    for r in rag_nm:
        if r["question"] in questions:
            questions[r["question"]]["no_media"] = r

    # Convert to ordered list so dropdown and JS stay in sync
    question_list = [
        {"question": q, "full": v.get("full", {}), "no_media": v.get("no_media", {})}
        for q, v in questions.items()
    ]

    return templates.TemplateResponse("ask.html", {
        "request": request,
        "question_list": question_list,
    })


# ── Page 5a: Responsible AI Use ───────────────────────────────────────
@app.get("/responsible-ai", response_class=HTMLResponse)
async def responsible_ai(request: Request):
    return templates.TemplateResponse("implications.html", {
        "request": request,
    })


# ── Page 5b: Next Steps ──────────────────────────────────────────────
@app.get("/next-steps", response_class=HTMLResponse)
async def next_steps(request: Request):
    return templates.TemplateResponse("next_steps.html", {
        "request": request,
    })


# ── Page 6: Contact ──────────────────────────────────────────────────
@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {
        "request": request,
    })


# ── Feedback ──────────────────────────────────────────────────────────
@app.post("/api/feedback")
async def submit_feedback(request: Request):
    body = await request.json()
    message = body.get("message", "").strip()
    page = body.get("page", "")
    if not message:
        return {"error": "Message is required"}
    sb = queries.get_supabase()
    sb.table("atlased_feedback").insert({"message": message, "page": page}).execute()
    return {"ok": True}


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
