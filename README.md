# AtlasED — Specification Transparency Dashboard

**Live demo:** [atlased-dashboard.onrender.com](https://atlased-dashboard.onrender.com)

UCL Institute of Education | 2026

Built as part of a Level 7 AI Engineering Apprenticeship. Originally developed as an independent strand of the ESRC Education Research Programme. Cross-jurisdictional expansion funded by a UCL Grand Challenges Inequality Catalyst Grant.

---

## What is this?

Every AI pipeline makes choices — how many topics, which sources to include, how to preprocess text. These choices shape outputs as much as the data itself, but they are almost never disclosed.

AtlasED makes them visible and testable.

This is a production dashboard for exploring specification sensitivity in education policy topic modelling. It analyses 3,943 articles from 6 sources across England (Jan 2023 – Sep 2025) and shows what happens when you change the model's specification choices.

## The core finding

> No specification choice preserves more than 18% of topic names. Standard diagnostics cannot detect this. The only way to know is to perturb and compare.

## What the dashboard shows

| Page | What it does |
|------|-------------|
| **Overview** | KPI cards, source distribution, topic distribution for the baseline model (k=30) |
| **Topics & Trends** | Temporal line charts with election marker (Jul 2024). Filter by topic and model. |
| **Specification Sensitivity** | 3-step interactive stepper: choose a model (k=5, 15, 30, or no-media), view results, compare to baseline side-by-side |
| **Ask the Data** | Dual-panel RAG: same question asked of full corpus vs no-media corpus. Same LLM, different retrieved context, divergent answers. |
| **Implications** | SpecCheck methodology, future vision, and technical specification |

## Key findings

### k is a volume knob for minority sources

| k | Stability | Single-source topics | Observation |
|---|-----------|---------------------|-------------|
| 5 | 1.000 | 60% | One catch-all topic holds 49% of articles. Minority sources invisible. |
| 15 | 1.000 | 40% | RAAC and breakfast clubs disappear. FFT/EPI first become visible. |
| 30 | 0.966 | 47% | Maximum granularity. Multiple plausible solutions emerge. |

### The education debate is produced by media

Removing SchoolsWeek (70% of the corpus) doesn't just reduce the dataset — it fundamentally changes what education policy "looks like":
- Teacher strikes vanish entirely
- Shared debate fragments into institutional monologues
- Full corpus: crisis-oriented (council deficits, EHCP wait times)
- No-media corpus: procedural (statutory guidance, compliance requirements)

## Architecture

```
┌─────────────────────┐
│   atlas-ed-data      │     Data pipeline (scraping, cleaning)
│   (separate repo)    │     16 sources, 3 countries, weekly automated
└──────────┬───────────┘
           │
           ▼
┌─────────────────────┐
│   Supabase           │     Shared database
│                      │
│   articles_topics    │     5,419 article-level topic assignments
│   atlased_models     │     4 model variants
│   atlased_topics     │     80 topic metadata rows
│   atlased_timeseries │     944 monthly trend rows
│   atlased_rag        │     10 pre-computed RAG Q&A pairs
│   atlased_overview   │     Pre-computed dashboard stats
└──────────┬───────────┘
           │
           ▼
┌─────────────────────┐
│   atlas-ed-tool      │     This repo — dashboard + API
│   (FastAPI + Jinja2) │
│                      │
│   Deployed on Render │
└─────────────────────┘
```

## Models

| Model ID | k | Corpus | Articles | Stability | Purpose |
|----------|---|--------|----------|-----------|---------|
| eng_k5 | 5 | full | 3,943 | 1.000 | Sensitivity comparison |
| eng_k15 | 15 | full | 3,943 | 1.000 | Sensitivity comparison |
| eng_k30 | 30 | full | 3,943 | 0.966 | **Production baseline** |
| eng_k30_nm | 30 | no_media | 1,198 | 0.961 | Media bias test |

All trained with: NMF, init=nndsvd, random_state=42, max_iter=1000, TF-IDF (min_df=3, max_df=0.85, max_features=3000, ngram_range=(1,2)).

## Tech stack

- **Backend:** FastAPI + Jinja2 templates
- **Database:** Supabase (PostgreSQL + REST API)
- **Charts:** Chart.js
- **Markdown rendering:** marked.js (for RAG answers)
- **Deployment:** Render (web service)
- **Fonts:** DM Sans + Source Serif 4

## Quick start

```bash
git clone https://github.com/Yorkel/atlas-ed-tool.git
cd atlas-ed-tool
pip install -r requirements.txt
```

Create a `.env` file:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

Run locally:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Project structure

```
atlas-ed-tool/
├── app/
│   ├── main.py          # FastAPI routes (5 pages + 1 API endpoint)
│   ├── queries.py       # Supabase query functions
│   └── database.py      # Supabase client singleton
├── templates/           # Jinja2 HTML templates (one per page)
├── static/
│   └── style.css        # Dashboard styling
├── scripts/
│   ├── build_overview_table.py   # Pre-compute overview stats
│   └── sql/
│       └── create_atlased_overview.sql  # Table schema
├── dashboard_export/    # Static data export from pipeline
├── render.yaml          # Render deployment config
├── requirements.txt
└── DASHBOARD_HANDOFF.md # Full data/schema documentation
```

## Data sources

| Source | Type | Country |
|--------|------|---------|
| SchoolsWeek | Education media | England |
| Gov.uk (DfE) | Government | England |
| EPI | Think tank | England |
| Nuffield Foundation | Funder | England |
| FFT Datalab | Research org | England |
| FED | Professional body | England |

## Related repositories

- **[atlas-ed-data](https://github.com/Yorkel/atlas-ed-data)** — Data pipeline: 16 scrapers across 3 countries, weekly automated via GitHub Actions

## Ethics

This project has full ethical approval from the UCL Institute of Education Research Ethics Committee (REC2360). All data is from publicly accessible sources. No personal data is collected. No paywalls are circumvented.

---

Licence: Code and documentation available for academic and non-commercial use. &copy; UCL Institute of Education 2026. For commercial reuse, contact l.yorke@ucl.ac.uk.
