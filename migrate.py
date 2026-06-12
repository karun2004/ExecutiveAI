#!/usr/bin/env python3
"""
Migration: Remove CHECK constraints from content and projects tables.
Run once: cd ~/mach-1 && source venv/bin/activate && python3 migrate.py
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "mach1.db"

if not DB_PATH.exists():
    print(f"Database not found at {DB_PATH}")
    sys.exit(1)

print(f"Migrating {DB_PATH}...")
conn = sqlite3.connect(str(DB_PATH))
conn.execute("PRAGMA foreign_keys=OFF")

try:
    # ── Migrate content table ──────────────
    print("  Rebuilding content table...")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS content_new (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id    INTEGER REFERENCES topics(id),
            team        TEXT NOT NULL DEFAULT 'content',
            content_type TEXT NOT NULL,
            title       TEXT,
            body        TEXT NOT NULL,
            platform    TEXT,
            status      TEXT DEFAULT 'draft' CHECK(status IN (
                'draft','pending_review','approved','rejected','published','failed'
            )),
            model_used  TEXT,
            tokens_used INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now')),
            published_at TEXT
        );

        INSERT INTO content_new SELECT * FROM content;
        DROP TABLE content;
        ALTER TABLE content_new RENAME TO content;
        CREATE INDEX IF NOT EXISTS idx_content_status ON content(status);
    """)

    # ── Migrate projects table ─────────────
    print("  Rebuilding projects table...")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects_new (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            description TEXT,
            template    TEXT,
            status      TEXT DEFAULT 'pending' CHECK(status IN (
                'pending','building','testing','fix_attempt_1','fix_attempt_2',
                'fix_attempt_3','escalated','complete','failed'
            )),
            repo_url    TEXT,
            local_path  TEXT,
            fix_attempts INTEGER DEFAULT 0,
            model_used  TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            completed_at TEXT
        );

        INSERT INTO projects_new SELECT * FROM projects;
        DROP TABLE projects;
        ALTER TABLE projects_new RENAME TO projects;
        CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
    """)

    conn.execute("PRAGMA foreign_keys=ON")
    conn.commit()
    print("Migration complete! Constraints removed.")

except Exception as e:
    conn.rollback()
    print(f"Migration FAILED: {e}")
    sys.exit(1)
finally:
    conn.close()
