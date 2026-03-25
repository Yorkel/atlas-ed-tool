# AtlasED Dashboard Handoff

Everything the dashboard repo needs to know about the data, models, and Supabase tables produced by this topic modelling pipeline.

---

## Supabase Tables

### `articles_topics` (existing — written by the training pipeline)

The primary article-level data table. Already populated with 5,419 rows.

| Column | Type | Notes |
|--------|------|-------|
| url | TEXT | Article URL (unique per run_id) |
| title | TEXT | |
| article_date | DATE | |
| source | TEXT | e.g. `schoolsweek`, `gov`, `epi`, `nuffield`, `fft`, `fed` |
| country | TEXT | `England`, `Scotland`, `Ireland` |
| institution_name | TEXT | |
| type | TEXT | e.g. `media`, `think_tank`, `government` |
| topic_num | INTEGER | Dominant topic index (0-based) |
| dominant_topic | TEXT | Dominant topic name |
| dominant_topic_weight | FLOAT | Confidence in dominant topic (0–1) |
| topic_probabilities | JSONB | `{"topic_name": weight, ...}` for all topics |
| contestability_score | FLOAT | Normalised Shannon entropy (0=certain, 1=uncertain) |
| text_clean | TEXT | Preprocessed article text |
| article_text | TEXT | Original article text |
| election_period | TEXT | `pre_election` or `post_election` (split at 2024-07-04) |
| run_id | TEXT | Links to `atlased_models.run_id` |
| model_type | TEXT | Always `nmf` |
| language | TEXT | |
| dataset_type | TEXT | |
| week_number | INTEGER | |

**Indexes added for dashboard:**
- `idx_articles_topics_run_source` on `(run_id, source)`
- `idx_articles_topics_run_date` on `(run_id, article_date)`

### `atlased_models` (new — dashboard metadata)

4 rows. One per model variant.

| Column | Type | Notes |
|--------|------|-------|
| model_id | TEXT PK | `eng_k5`, `eng_k15`, `eng_k30`, `eng_k30_nm` |
| run_id | TEXT UNIQUE | Links to `articles_topics.run_id` |
| k | INTEGER | Number of topics |
| n_articles | INTEGER | Corpus size |
| stability | DECIMAL(5,4) | Topic stability score |
| mean_weight | DECIMAL(5,4) | Mean dominant topic weight |
| coherence | DECIMAL(5,4) | Topic coherence (null for now) |
| corpus_type | TEXT | `full` or `no_media` |
| trained_at | TIMESTAMPTZ | |

### `atlased_topics` (new — topic metadata per model)

80 rows (5 + 15 + 30 + 30).

| Column | Type | Notes |
|--------|------|-------|
| model_id | TEXT FK | References `atlased_models.model_id` |
| topic_num | INTEGER | 0-based topic index |
| name | TEXT | Human-curated topic name |
| top_keywords | TEXT[] | Top 10 TF-IDF keywords |
| article_count | INTEGER | Articles assigned to this topic |
| pct | DECIMAL(5,2) | Percentage of corpus |
| top_source | TEXT | Most frequent source |
| top_source_pct | DECIMAL(5,4) | Concentration of top source |
| single_source | BOOLEAN | True if top_source_pct > 0.95 |

### `atlased_topic_timeseries` (new — monthly counts for charts)

944 rows. Baseline model (eng_k30) only.

| Column | Type | Notes |
|--------|------|-------|
| model_id | TEXT | Always `eng_k30` |
| topic_num | INTEGER | |
| year | INTEGER | e.g. 2024 |
| month | INTEGER | 1–12 |
| topic_name | TEXT | |
| article_count | INTEGER | |

### `atlased_rag_contexts` (new — pre-computed RAG Q&A)

10 rows (5 questions x 2 corpora).

| Column | Type | Notes |
|--------|------|-------|
| corpus_type | TEXT | `full` or `no_media` |
| question | TEXT | The question asked |
| answer | TEXT | Markdown-formatted RAG response |
| sources_used | TEXT[] | Which sources the retrieved articles came from |
| topics_covered | TEXT[] | Which topics the retrieved articles belonged to |
| n_retrieved | INTEGER | Number of articles retrieved |

All `atlased_*` tables have RLS enabled with public read policies.

---

## Models

| model_id | k | run_id | corpus | n_articles | stability | mean_weight |
|----------|---|--------|--------|-----------|-----------|-------------|
| eng_k5 | 5 | 2026-03-24_104906 | full | 3,943 | 1.000 | 0.092 |
| eng_k15 | 15 | 2026-03-24_112503 | full | 3,943 | 1.000 | 0.122 |
| eng_k30 | 30 | eng_2026-03-24_134826 | full | 3,943 | 0.966 | 0.130 |
| eng_k30_nm | 30 | 2026-03-24_013511 | no_media | 1,198 | 0.961 | 0.195 |

- **eng_k30** is the production baseline
- **eng_k30_nm** removes SchoolsWeek (tests media bias)
- **eng_k5 / eng_k15** are for specification sensitivity comparison
- All trained with: NMF, init=nndsvd, random_state=42, max_iter=1000
- TF-IDF: min_df=3, max_df=0.85, max_features=3000, ngram_range=(1,2)

### Cross-jurisdiction (not in Supabase, available in dashboard_export)

| model_id | k | run_id |
|----------|---|--------|
| sco_k15 | 15 | sco_2026-03-24_135938 |
| irl_k15 | 15 | irl_2026-03-24_140040 |

---

## Topic Names (k=30 baseline)

| # | Name | % | Top Source | Concentration |
|---|------|---|-----------|---------------|
| 0 | child_and_family_welfare | 1.5 | gov | 0.47 |
| 1 | academy_finance_and_oversight | 3.8 | gov | 0.99 |
| 2 | academy_trust_governance | 6.5 | schoolsweek | 0.88 |
| 3 | teacher_pay | 2.7 | schoolsweek | 0.97 |
| 4 | ofsted_inspection_reform | 6.0 | schoolsweek | 0.80 |
| 5 | gcse_grades_and_results | 1.9 | schoolsweek | 0.52 |
| 6 | pupil_disadvantage_and_attainment | 3.0 | schoolsweek | 0.52 |
| 7 | dfe_warning_notices | 2.1 | gov | 0.96 |
| 8 | send_and_council_deficits | 3.6 | schoolsweek | 0.95 |
| 9 | teacher_strikes_and_unions | 3.2 | schoolsweek | 0.96 |
| 10 | apprenticeships_and_skills | 2.5 | gov | 0.61 |
| 11 | ofqual_exam_regulation | 3.0 | schoolsweek | 0.59 |
| 12 | raac_building_crisis | 3.0 | schoolsweek | 0.88 |
| 13 | school_absence_and_attendance | 2.2 | schoolsweek | 0.47 |
| 14 | free_school_meals_and_poverty | 2.1 | schoolsweek | 0.82 |
| 15 | education_politics | 4.3 | schoolsweek | 0.96 |
| 16 | research_and_social_justice | 5.0 | nuffield | 0.44 |
| 17 | leadership_appointments | 3.6 | schoolsweek | 0.80 |
| 18 | mental_health_and_wellbeing | 1.7 | schoolsweek | 0.77 |
| 19 | post16_qualifications | 3.9 | schoolsweek | 0.56 |
| 20 | primary_assessment_and_sats | 3.0 | schoolsweek | 0.57 |
| 21 | safeguarding_and_complaints | 6.0 | schoolsweek | 0.88 |
| 22 | teacher_recruitment_and_retention | 6.3 | schoolsweek | 0.89 |
| 23 | school_funding | 4.6 | schoolsweek | 0.90 |
| 24 | curriculum_and_subjects | 3.5 | schoolsweek | 0.70 |
| 25 | ofsted_report_cards | 3.2 | schoolsweek | 0.75 |
| 26 | breakfast_clubs | 1.1 | schoolsweek | 0.65 |
| 27 | edtech_and_ai | 2.4 | schoolsweek | 0.61 |
| 28 | school_places_and_capacity | 3.1 | schoolsweek | 0.87 |
| 29 | exclusions_and_suspensions | 1.3 | schoolsweek | 0.62 |

---

## Specification Sensitivity Findings

The core argument the dashboard demonstrates: **model specification choices shape outputs as much as the data itself**.

### What changes when k changes

| k | Stability | Single-source topics | Key observation |
|---|-----------|---------------------|-----------------|
| 5 | 1.000 | 60% | One catch-all topic holds 49% of articles. Minority sources invisible. |
| 15 | 1.000 | 40% | RAAC building crisis and breakfast clubs disappear (merged into broader topics). FFT/EPI first become visible. |
| 30 | 0.966 | 47% | Maximum granularity. Multiple plausible solutions emerge. Nuffield gets its own topic. |

**k is a volume knob for minority sources** — as k increases, smaller voices (FFT, EPI, Nuffield) become audible in topics shaped for them.

### What changes when SchoolsWeek is removed (k30 vs k30_nm)

- Corpus drops from 3,943 to 1,198 articles (70% was SchoolsWeek)
- 18 of 30 topic names change
- Teacher strikes vanish entirely
- "Shared debate" fragments into institutional monologues
- Full corpus: crisis-oriented (council deficits, EHCP wait times)
- No-media corpus: procedural (statutory guidance, compliance requirements)
- **Key finding: the education policy debate is produced by media, not by the institutions**

### Contestability score

Normalised Shannon entropy per article (0 = certain assignment, 1 = uncertain).
Available in `articles_topics.contestability_score`. Use as an article-level uncertainty indicator in the UI.

---

## Key Dates

- **UK General Election:** 2024-07-04 (hard-coded in pipeline, splits `election_period`)
- **Data period:** Jan 2023 – Sep 2025
- **Sources:** SchoolsWeek (media), Gov.uk (government), EPI, Nuffield, FFT (think tanks), FED (federation)

---

## Data Sources for the Dashboard

### Option A: Supabase queries (recommended for production)

```python
from app.database import get_supabase

# Get all topics for a model
supabase.table("atlased_topics").select("*").eq("model_id", "eng_k30").execute()

# Get timeseries for specific topics
supabase.table("atlased_topic_timeseries").select("*").eq("model_id", "eng_k30").in_("topic_num", [8, 22, 4]).execute()

# Get RAG responses for both corpora
supabase.table("atlased_rag_contexts").select("*").eq("question", "What are the main issues in SEND provision?").execute()

# Get articles for a specific model run
run_id = supabase.table("atlased_models").select("run_id").eq("model_id", "eng_k30").single().execute().data["run_id"]
supabase.table("articles_topics").select("*").eq("run_id", run_id).execute()
```

### Option B: Static JSON/CSV (for demo or offline mode)

Copy `dashboard_export/` contents into the dashboard repo's `data/` directory:

```
data/
├── models/           # 4 enriched model JSONs with keywords
├── articles/         # Analysis-ready CSVs + timeseries
├── rag/              # RAG comparison JSON + FAISS indexes
├── evaluation/       # Coherence + stability CSVs
├── visualisations/   # Pre-rendered PNGs
└── llm_reviews/      # LLM topic name validations
```

---

## RAG Data Structure

The `rag_comparison.json` contains 5 questions, each with full-corpus and no-media answers:

```json
{
  "questions": [
    {
      "question": "What are the main issues in English education policy?",
      "full": {
        "answer": "## School Funding Crisis\n...",
        "sources_used": ["epi", "schoolsweek", ...],
        "topics_covered": ["research_and_social_justice", ...],
        "n_retrieved": 10,
        "corpus": "full England corpus (including Schools Week)"
      },
      "nm": {
        "answer": "## Achievement Gaps and Disadvantage\n...",
        "sources_used": ["epi", "fed", "gov", ...],
        "topics_covered": ["apprenticeships_and_skills", ...],
        "n_retrieved": 10
      }
    }
  ],
  "embedding_model": "...",
  "llm_model": "...",
  "retrieval_k": 10,
  "full_corpus_size": 3939,
  "nm_corpus_size": 1198
}
```

The dual-panel RAG is the visual punchline: same question, different retrieved documents, divergent answers. The specification sensitivity is at the infrastructure level.

---

## Dashboard Pages (recommended)

1. **Overview** — KPI cards (articles, topics, sources, date range) + source distribution chart
2. **Topics & Trends** — Temporal line chart with 2024-07-04 election marker, topic selector
3. **Specification Sensitivity** — 3-step stepper: configure model (k + corpus) → view results → compare to baseline
4. **Ask the Data** — Dual-panel RAG: same question, full vs no-media corpus side by side
5. **Implications** — Static content about SpecCheck methodology and future vision

---

## Scripts in This Repo

| Script | Purpose | Command |
|--------|---------|---------|
| `scripts/export_for_dashboard.py` | Package all data into `dashboard_export/` | `PYTHONPATH=. python scripts/export_for_dashboard.py` |
| `scripts/retrain_k5_k15.py` | Retrain k=5/k=15 models to save joblib files (for keyword extraction) | `PYTHONPATH=. python scripts/retrain_k5_k15.py` |
| `scripts/load_atlased_to_supabase.py` | Load exported data into Supabase `atlased_*` tables | `PYTHONPATH=. python scripts/load_atlased_to_supabase.py` |

To re-export and reload after retraining:
```bash
PYTHONPATH=. python scripts/retrain_k5_k15.py        # ~2 min (spaCy processing)
PYTHONPATH=. python scripts/export_for_dashboard.py   # ~5 sec
PYTHONPATH=. python scripts/load_atlased_to_supabase.py  # ~10 sec
```

---

## Important Implementation Notes

1. **Use `model_id` everywhere** (`eng_k5`, `eng_k15`, `eng_k30`, `eng_k30_nm`). Never display `run_id` — it's for backend lineage only.

2. **Topic name consistency:** The 30 topic names in the CSV column headers must match exactly to names in `atlased_topics`. The pipeline's [preflight check](../../project/project_preflight_check.md) verifies this.

3. **Corpus size mismatch:** k30_nm has 1,198 articles vs k30's 3,943. Show raw counts AND percentages in comparisons so the difference is legible.

4. **Election date is a specification choice:** 2024-07-04 is hard-coded. Changing it requires a pipeline re-run, not a config change.

5. **Supabase env var:** This repo uses `SUPABASE_SERVICE_KEY` (not `SUPABASE_KEY`). The dashboard repo can use either — both work with the anon key for read-only queries.
