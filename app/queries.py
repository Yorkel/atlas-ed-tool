"""Supabase query functions for the AtlasED dashboard."""

from app.database import get_supabase


def get_models() -> list[dict]:
    """Return all model metadata rows."""
    sb = get_supabase()
    return sb.table("atlased_models").select("*").execute().data


def get_model(model_id: str) -> dict | None:
    """Return a single model by model_id."""
    sb = get_supabase()
    result = sb.table("atlased_models").select("*").eq("model_id", model_id).execute()
    return result.data[0] if result.data else None


def get_topics(model_id: str) -> list[dict]:
    """Return all topics for a given model, sorted by topic_num."""
    sb = get_supabase()
    return (
        sb.table("atlased_topics")
        .select("*")
        .eq("model_id", model_id)
        .order("topic_num")
        .execute()
        .data
    )


def get_timeseries(model_id: str = "eng_k30", topic_nums: list[int] | None = None) -> list[dict]:
    """Return monthly topic counts for trend charts."""
    sb = get_supabase()
    query = sb.table("atlased_topic_timeseries").select("*").eq("model_id", model_id)
    if topic_nums is not None:
        query = query.in_("topic_num", topic_nums)
    return query.order("year").order("month").execute().data


def get_rag_contexts(corpus_type: str | None = None) -> list[dict]:
    """Return pre-computed RAG Q&A rows, optionally filtered by corpus."""
    sb = get_supabase()
    query = sb.table("atlased_rag_contexts").select("*")
    if corpus_type:
        query = query.eq("corpus_type", corpus_type)
    return query.execute().data


def get_articles(
    run_id: str,
    source: str | None = None,
    topic_num: int | None = None,
    limit: int = 100,
) -> list[dict]:
    """Return articles for a given run, with optional filters."""
    sb = get_supabase()
    query = (
        sb.table("articles_topics")
        .select("url,title,article_date,source,dominant_topic,dominant_topic_weight,contestability_score")
        .eq("run_id", run_id)
    )
    if source:
        query = query.eq("source", source)
    if topic_num is not None:
        query = query.eq("topic_num", topic_num)
    return query.limit(limit).execute().data


SOURCE_TYPE_MAP = {
    "schoolsweek": "Media",
    "gov": "Government",
    "epi": "Think tank",
    "nuffield": "Think tank",
    "fft": "Think tank",
    "fed": "Professional body",
}

SOURCES_BY_TYPE = {
    "Media": ["schoolsweek"],
    "Government": ["gov"],
    "Think tank": ["epi", "nuffield", "fft"],
    "Professional body": ["fed"],
}


def get_top_topics_filtered(
    run_id: str,
    sources: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Return top topics by article count, with optional source and date filters."""
    from collections import Counter

    sb = get_supabase()
    query = (
        sb.table("articles_topics")
        .select("topic_num,dominant_topic,source,article_date")
        .eq("run_id", run_id)
    )
    if sources:
        query = query.in_("source", sources)
    if date_from:
        query = query.gte("article_date", date_from)
    if date_to:
        query = query.lte("article_date", date_to)

    # Paginate
    all_rows = []
    offset = 0
    page_size = 1000
    while True:
        batch = query.range(offset, offset + page_size - 1).execute().data
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    # Count by topic
    topic_counts = Counter()
    topic_names = {}
    for row in all_rows:
        tn = row["topic_num"]
        topic_counts[tn] += 1
        if tn not in topic_names:
            topic_names[tn] = row["dominant_topic"]

    top = topic_counts.most_common(limit)
    total = len(all_rows)
    return [
        {
            "topic_num": tn,
            "name": topic_names.get(tn, f"topic_{tn}"),
            "article_count": count,
            "pct": round(count / total * 100, 1) if total else 0,
        }
        for tn, count in top
    ]


def get_trend_data_filtered(
    run_id: str,
    sources: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    topic_nums: list[int] | None = None,
) -> list[dict]:
    """Return monthly article counts per topic, with optional filters."""
    from collections import Counter

    sb = get_supabase()
    query = (
        sb.table("articles_topics")
        .select("topic_num,dominant_topic,article_date,source")
        .eq("run_id", run_id)
    )
    if sources:
        query = query.in_("source", sources)
    if date_from:
        query = query.gte("article_date", date_from)
    if date_to:
        query = query.lte("article_date", date_to)
    if topic_nums:
        query = query.in_("topic_num", topic_nums)

    all_rows = []
    offset = 0
    page_size = 1000
    while True:
        batch = query.range(offset, offset + page_size - 1).execute().data
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    # Group by topic + year-month
    counts = Counter()
    topic_names = {}
    for row in all_rows:
        tn = row["topic_num"]
        d = row.get("article_date", "")
        if not d:
            continue
        ym = d[:7]  # "YYYY-MM"
        counts[(tn, ym)] += 1
        if tn not in topic_names:
            topic_names[tn] = row["dominant_topic"]

    result = []
    for (tn, ym), count in sorted(counts.items(), key=lambda x: (x[0][1], x[0][0])):
        result.append({
            "topic_num": tn,
            "topic_name": topic_names.get(tn, f"topic_{tn}"),
            "year_month": ym,
            "article_count": count,
        })
    return result


def get_overview_stats(model_id: str = "eng_k30") -> dict:
    """Return pre-computed overview stats from atlased_overview (single row query)."""
    sb = get_supabase()
    result = sb.table("atlased_overview").select("*").eq("model_id", model_id).execute()
    return result.data[0] if result.data else {}
