-- Create the atlased_overview table for pre-computed dashboard stats
-- Run this in Supabase SQL Editor before running build_overview_table.py

CREATE TABLE IF NOT EXISTS atlased_overview (
    model_id          TEXT PRIMARY KEY REFERENCES atlased_models(model_id),
    n_articles        INTEGER,
    n_topics          INTEGER,
    sources           TEXT[],
    n_sources         INTEGER,
    date_min          DATE,
    date_max          DATE,
    stability         DECIMAL(5,4),
    mean_weight       DECIMAL(5,4),
    source_counts     JSONB,
    articles_by_month JSONB
);

-- Enable RLS with public read (same as other atlased_* tables)
ALTER TABLE atlased_overview ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access"
    ON atlased_overview
    FOR SELECT
    USING (true);
