"""
Build the atlased_overview table in Supabase.

Pre-computes per-model summary stats so the dashboard overview page
needs only a single lightweight query instead of scanning articles_topics.

Usage:
    PYTHONPATH=. python scripts/build_overview_table.py

Table schema (atlased_overview):
    model_id        TEXT PK
    n_articles      INTEGER
    n_topics        INTEGER
    sources         TEXT[]        -- distinct source names
    n_sources       INTEGER
    date_min        DATE
    date_max        DATE
    stability       DECIMAL(5,4)
    mean_weight     DECIMAL(5,4)
    source_counts   JSONB         -- {"schoolsweek": 2745, "gov": 612, ...}
    articles_by_month JSONB       -- [{"year":2024,"month":1,"count":85}, ...]
"""

import json
from collections import Counter
from app.database import get_supabase


def fetch_all_articles(sb, run_id):
    """Fetch all articles for a run_id, handling Supabase pagination."""
    all_rows = []
    page_size = 1000
    offset = 0
    while True:
        batch = (
            sb.table("articles_topics")
            .select("source,article_date")
            .eq("run_id", run_id)
            .range(offset, offset + page_size - 1)
            .execute()
            .data
        )
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return all_rows


def build_overview_row(sb, model):
    """Build one overview row for a model."""
    model_id = model["model_id"]
    run_id = model["run_id"]
    print(f"  Processing {model_id} (run_id={run_id})...")

    # Get topic count
    topics = (
        sb.table("atlased_topics")
        .select("topic_num")
        .eq("model_id", model_id)
        .execute()
        .data
    )

    # Get all articles (paginated)
    articles = fetch_all_articles(sb, run_id)
    print(f"    Fetched {len(articles)} articles")

    # Compute source counts
    source_counter = Counter(a["source"] for a in articles if a.get("source"))

    # Compute articles by month
    month_counter = Counter()
    dates = []
    for a in articles:
        d = a.get("article_date")
        if d:
            dates.append(d)
            # date format is "YYYY-MM-DD"
            year, month = d[:4], d[5:7]
            month_counter[(int(year), int(month))] += 1

    articles_by_month = sorted(
        [{"year": y, "month": m, "count": c} for (y, m), c in month_counter.items()],
        key=lambda x: (x["year"], x["month"]),
    )

    return {
        "model_id": model_id,
        "n_articles": model["n_articles"],
        "n_topics": len(topics),
        "sources": sorted(source_counter.keys()),
        "n_sources": len(source_counter),
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "stability": float(model["stability"]) if model.get("stability") else None,
        "mean_weight": float(model["mean_weight"]) if model.get("mean_weight") else None,
        "source_counts": dict(source_counter.most_common()),
        "articles_by_month": articles_by_month,
    }


def main():
    sb = get_supabase()

    print("Fetching models...")
    models = sb.table("atlased_models").select("*").execute().data
    print(f"Found {len(models)} models\n")

    rows = []
    for model in models:
        row = build_overview_row(sb, model)
        rows.append(row)
        print(f"    -> {row['n_sources']} sources, {row['date_min']} to {row['date_max']}\n")

    # Upsert into atlased_overview
    print("Upserting into atlased_overview...")
    for row in rows:
        sb.table("atlased_overview").upsert(row).execute()
        print(f"  Upserted {row['model_id']}")

    print(f"\nDone. {len(rows)} rows in atlased_overview.")


if __name__ == "__main__":
    main()
