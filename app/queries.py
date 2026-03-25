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


def get_overview_stats(model_id: str = "eng_k30") -> dict:
    """Return pre-computed overview stats from atlased_overview (single row query)."""
    sb = get_supabase()
    result = sb.table("atlased_overview").select("*").eq("model_id", model_id).execute()
    return result.data[0] if result.data else {}
