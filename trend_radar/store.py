"""SQLite history of hashtag counts per run, so each run can compare with the last."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .trends import TagStats, Trend

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, niche TEXT NOT NULL, ran_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tag_counts (run_id INTEGER NOT NULL, tag TEXT NOT NULL, posts INTEGER NOT NULL, engagement INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS alerts_sent (niche TEXT NOT NULL, tag TEXT NOT NULL, sent_at TEXT NOT NULL);
"""


class Store:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.executescript(SCHEMA)

    def previous_counts(self, niche: str) -> dict[str, int]:
        row = self.conn.execute("SELECT id FROM runs WHERE niche=? ORDER BY id DESC LIMIT 1", (niche,)).fetchone()
        if not row:
            return {}
        return dict(self.conn.execute("SELECT tag, posts FROM tag_counts WHERE run_id=?", (row[0],)).fetchall())

    def save_run(self, niche: str, stats: dict[str, TagStats]) -> int:
        cur = self.conn.execute("INSERT INTO runs (niche, ran_at) VALUES (?, ?)",
                                (niche, datetime.now(timezone.utc).isoformat()))
        run_id = cur.lastrowid
        self.conn.executemany("INSERT INTO tag_counts VALUES (?, ?, ?, ?)",
                              [(run_id, s.tag, s.posts, s.engagement) for s in stats.values()])
        self.conn.commit()
        return run_id

    def recently_alerted(self, niche: str, tag: str, hours: int = 24) -> bool:
        row = self.conn.execute(
            "SELECT sent_at FROM alerts_sent WHERE niche=? AND tag=? ORDER BY sent_at DESC LIMIT 1", (niche, tag)
        ).fetchone()
        if not row:
            return False
        age = datetime.now(timezone.utc) - datetime.fromisoformat(row[0])
        return age.total_seconds() < hours * 3600

    def mark_alerted(self, niche: str, trends: list[Trend]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.executemany("INSERT INTO alerts_sent VALUES (?, ?, ?)", [(niche, t.tag, now) for t in trends])
        self.conn.commit()
