-- Needs queue (professor → undergrads) and corpus backfill cursor.
-- Idempotent.

ALTER TABLE pcos.runs DROP CONSTRAINT IF EXISTS runs_kind_check;
ALTER TABLE pcos.runs ADD CONSTRAINT runs_kind_check
    CHECK (kind IN ('collect', 'tag', 'analyze', 'seed', 'stress', 'backfill', 'gapfill'));

CREATE TABLE IF NOT EXISTS pcos.needs (
    id              BIGSERIAL PRIMARY KEY,
    need_key        TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    why             TEXT NOT NULL,
    pubmed_term     TEXT NOT NULL,
    hypothesis_area TEXT,
    priority        INTEGER NOT NULL DEFAULT 50,
    status          TEXT NOT NULL DEFAULT 'open' CHECK (status IN (
                        'open', 'filling', 'filled', 'parked', 'dropped'
                    )),
    filed_by        TEXT NOT NULL DEFAULT 'grok-4.6',
    evidence_wanted TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_filled_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS needs_status_priority_idx
    ON pcos.needs (status, priority DESC, id);

CREATE TABLE IF NOT EXISTS pcos.need_sources (
    need_id         BIGINT NOT NULL REFERENCES pcos.needs(id) ON DELETE CASCADE,
    source_id       BIGINT NOT NULL REFERENCES pcos.sources(id) ON DELETE CASCADE,
    PRIMARY KEY (need_id, source_id)
);

CREATE TABLE IF NOT EXISTS pcos.backfill_cursors (
    query_key       TEXT PRIMARY KEY,
    term            TEXT NOT NULL,
    retstart        INTEGER NOT NULL DEFAULT 0,
    page_size       INTEGER NOT NULL DEFAULT 200,
    total_reported  INTEGER,
    exhausted       BOOLEAN NOT NULL DEFAULT false,
    last_run_at     TIMESTAMPTZ
);
