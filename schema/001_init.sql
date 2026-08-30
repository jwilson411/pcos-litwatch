-- PCOS literature-watch schema.
-- Idempotent. Safe to re-run. No secrets.

CREATE SCHEMA IF NOT EXISTS pcos;

CREATE TABLE IF NOT EXISTS pcos.sources (
    id              BIGSERIAL PRIMARY KEY,
    source_type     TEXT NOT NULL CHECK (source_type IN (
                        'pubmed', 'preprint', 'trial', 'guideline', 'review', 'other'
                    )),
    external_id     TEXT NOT NULL,
    doi             TEXT,
    title           TEXT NOT NULL,
    abstract        TEXT,
    authors         TEXT,
    journal         TEXT,
    published_on    DATE,
    url             TEXT NOT NULL,
    raw             JSONB NOT NULL DEFAULT '{}'::jsonb,
    content_hash    TEXT NOT NULL,
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_type, external_id)
);

CREATE INDEX IF NOT EXISTS sources_published_idx ON pcos.sources (published_on DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS sources_doi_idx ON pcos.sources (doi) WHERE doi IS NOT NULL;
CREATE INDEX IF NOT EXISTS sources_hash_idx ON pcos.sources (content_hash);

CREATE TABLE IF NOT EXISTS pcos.source_tags (
    id              BIGSERIAL PRIMARY KEY,
    source_id       BIGINT NOT NULL REFERENCES pcos.sources(id) ON DELETE CASCADE,
    tagger          TEXT NOT NULL,
    novelty         NUMERIC(3,2) CHECK (novelty BETWEEN 0 AND 1),
    mechanism_area  TEXT,
    is_primary      BOOLEAN,
    is_human        BOOLEAN,
    claims_json     JSONB NOT NULL DEFAULT '[]'::jsonb,
    skip_reason     TEXT,
    tagged_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_id, tagger)
);

CREATE TABLE IF NOT EXISTS pcos.claims (
    id              BIGSERIAL PRIMARY KEY,
    claim_key       TEXT NOT NULL UNIQUE,
    statement       TEXT NOT NULL,
    polarity        TEXT NOT NULL CHECK (polarity IN (
                        'supports_cure', 'supports_treatment', 'mechanism',
                        'refutes', 'nomenclature', 'epidemiology', 'unknown'
                    )),
    evidence_grade  TEXT NOT NULL CHECK (evidence_grade IN (
                        'guideline', 'rct', 'meta', 'review', 'observational',
                        'preclinical', 'preprint', 'expert', 'unverified'
                    )),
    status          TEXT NOT NULL DEFAULT 'open' CHECK (status IN (
                        'open', 'supported', 'weak', 'refuted', 'retired'
                    )),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pcos.claim_sources (
    claim_id        BIGINT NOT NULL REFERENCES pcos.claims(id) ON DELETE CASCADE,
    source_id       BIGINT NOT NULL REFERENCES pcos.sources(id) ON DELETE CASCADE,
    PRIMARY KEY (claim_id, source_id)
);

CREATE TABLE IF NOT EXISTS pcos.findings (
    id              BIGSERIAL PRIMARY KEY,
    run_id          BIGINT,
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    hypothesis_area TEXT,
    novelty         NUMERIC(3,2),
    analyst         TEXT NOT NULL,
    source_ids      BIGINT[] NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pcos.runs (
    id              BIGSERIAL PRIMARY KEY,
    kind            TEXT NOT NULL CHECK (kind IN ('collect', 'tag', 'analyze', 'seed', 'stress')),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ,
    ok              BOOLEAN,
    stats           JSONB NOT NULL DEFAULT '{}'::jsonb,
    error           TEXT
);

CREATE TABLE IF NOT EXISTS pcos.hypotheses (
    id              BIGSERIAL PRIMARY KEY,
    area            TEXT NOT NULL UNIQUE,
    summary         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'watch' CHECK (status IN (
                        'watch', 'promote', 'kill', 'parked'
                    )),
    last_reviewed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
