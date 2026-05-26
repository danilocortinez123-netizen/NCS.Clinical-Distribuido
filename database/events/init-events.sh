#!/bin/sh
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE events_db WITH OWNER admin;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "events_db" <<-EOSQL
    CREATE TABLE IF NOT EXISTS event_idempotency (
        event_id VARCHAR(64) PRIMARY KEY,
        event_type VARCHAR(64) NOT NULL,
        status VARCHAR(16) NOT NULL DEFAULT 'processed',
        created_at TIMESTAMP DEFAULT NOW(),
        expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '7 days')
    );
    CREATE INDEX IF NOT EXISTS idx_idempotency_expires
        ON event_idempotency (expires_at);

    CREATE TABLE IF NOT EXISTS event_outbox (
        id SERIAL PRIMARY KEY,
        event_id VARCHAR(64) NOT NULL UNIQUE,
        event_type VARCHAR(64) NOT NULL,
        source VARCHAR(64) NOT NULL,
        correlation_id VARCHAR(64),
        data JSONB NOT NULL,
        status VARCHAR(16) NOT NULL DEFAULT 'pending',
        retry_count INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW(),
        published_at TIMESTAMP,
        last_error TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_outbox_status
        ON event_outbox (status, created_at);
EOSQL
