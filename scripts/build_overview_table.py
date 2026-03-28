"""
Build pre-computed dashboard tables in Supabase.

Recomputes atlased_overview, atlased_topics (article_count, pct),
and atlased_topic_timeseries from the live articles_topics table,
so all dashboard pages reflect training + inference data.

Usage:
    PYTHONPATH=. python scripts/build_overview_table.py
"""

from collections import Counter
from app.database import get_supabase


def fetch_all_articles(sb, run_id, fields="source,article_date"):
    """Fetch all articles for a run_id, handling Supabase pagination."""
    all_rows = []
    page_size = 1000
    offset = 0
    while True:
        batch = (
            sb.table("articles_topics")
            .select(fields)
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


def build_overview_row(sb, model, articles):
    """Build one overview row for a model."""
    model_id = model["model_id"]

    # Get topic count
    topics = (
        sb.table("atlased_topics")
        .select("topic_num")
        .eq("model_id", model_id)
        .execute()
        .data
    )

    # Compute source counts
    source_counter = Counter(a["source"] for a in articles if a.get("source"))

    # Compute articles by month
    month_counter = Counter()
    dates = []
    for a in articles:
        d = a.get("article_date")
        if d:
            dates.append(d)
            year, month = d[:4], d[5:7]
            month_counter[(int(year), int(month))] += 1

    articles_by_month = sorted(
        [{"year": y, "month": m, "count": c} for (y, m), c in month_counter.items()],
        key=lambda x: (x["year"], x["month"]),
    )

    return {
        "model_id": model_id,
        "n_articles": len(articles),
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


def rebuild_topics(sb, model_id, run_id):
    """Recompute article_count and pct in atlased_topics from articles_topics."""
    print(f"  Rebuilding atlased_topics for {model_id}...")

    articles = fetch_all_articles(sb, run_id, "topic_num,dominant_topic,source")
    total = len(articles)
    if total == 0:
        return

    # Count by topic
    topic_counts = Counter(a["topic_num"] for a in articles)

    # Source concentration per topic
    topic_sources = {}
    for a in articles:
        tn = a["topic_num"]
        if tn not in topic_sources:
            topic_sources[tn] = Counter()
        if a.get("source"):
            topic_sources[tn][a["source"]] += 1

    # Get existing topic rows
    existing = (
        sb.table("atlased_topics")
        .select("topic_num")
        .eq("model_id", model_id)
        .execute()
        .data
    )

    updated = 0
    for row in existing:
        tn = row["topic_num"]
        count = topic_counts.get(tn, 0)
        pct = round(count / total * 100, 1) if total else 0
        sources = topic_sources.get(tn, Counter())
        top_source, top_count = sources.most_common(1)[0] if sources else ("", 0)
        top_source_pct = round(top_count / count, 4) if count else 0

        sb.table("atlased_topics").update({
            "article_count": count,
            "pct": pct,
            "top_source": top_source,
            "top_source_pct": top_source_pct,
            "single_source": top_source_pct > 0.95,
        }).eq("model_id", model_id).eq("topic_num", tn).execute()
        updated += 1

    print(f"    Updated {updated} topics ({total} articles)")


def rebuild_timeseries(sb, model_id, run_id):
    """Recompute atlased_topic_timeseries from articles_topics."""
    print(f"  Rebuilding atlased_topic_timeseries for {model_id}...")

    articles = fetch_all_articles(sb, run_id, "topic_num,dominant_topic,article_date")

    # Group by topic + year + month
    counts = Counter()
    topic_names = {}
    for a in articles:
        tn = a["topic_num"]
        d = a.get("article_date", "")
        if not d:
            continue
        year, month = int(d[:4]), int(d[5:7])
        counts[(tn, year, month)] += 1
        if tn not in topic_names:
            topic_names[tn] = a.get("dominant_topic", f"topic_{tn}")

    # Delete existing rows for this model
    sb.table("atlased_topic_timeseries").delete().eq("model_id", model_id).execute()

    # Insert new rows in batches
    rows = [
        {
            "model_id": model_id,
            "topic_num": tn,
            "topic_name": topic_names.get(tn, f"topic_{tn}"),
            "year": year,
            "month": month,
            "article_count": count,
        }
        for (tn, year, month), count in sorted(counts.items())
    ]

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        sb.table("atlased_topic_timeseries").insert(rows[i:i + batch_size]).execute()

    print(f"    Inserted {len(rows)} timeseries rows")


def main():
    sb = get_supabase()

    print("Fetching models...")
    models = sb.table("atlased_models").select("*").execute().data
    print(f"Found {len(models)} models\n")

    for model in models:
        model_id = model["model_id"]
        run_id = model["run_id"]
        print(f"Processing {model_id} (run_id={run_id})...")

        # Fetch articles once for overview
        articles = fetch_all_articles(sb, run_id)
        print(f"  Fetched {len(articles)} articles")

        # 1. Rebuild overview
        row = build_overview_row(sb, model, articles)
        sb.table("atlased_overview").upsert(row).execute()
        print(f"  Upserted overview: {row['n_articles']} articles, {row['date_min']} to {row['date_max']}")

        # 2. Rebuild topic counts
        rebuild_topics(sb, model_id, run_id)

        # 3. Rebuild timeseries
        rebuild_timeseries(sb, model_id, run_id)

        print()

    print("Done.")


if __name__ == "__main__":
    main()
