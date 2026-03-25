-- Create feedback table for anonymous dashboard feedback
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS atlased_feedback (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    page        TEXT,
    message     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Allow anonymous inserts (no auth required) but no reads
ALTER TABLE atlased_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous inserts"
    ON atlased_feedback
    FOR INSERT
    WITH CHECK (true);
