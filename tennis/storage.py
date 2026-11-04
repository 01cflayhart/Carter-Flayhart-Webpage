"""Normalized SQLite publication, rebuilt transactionally from immutable inputs."""
import json
import hashlib
from contextlib import closing
from pathlib import Path
import sqlite3

SCHEMA = """
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE players (id TEXT PRIMARY KEY, name TEXT NOT NULL, country TEXT, bio_json TEXT NOT NULL);
CREATE TABLE matches (id TEXT PRIMARY KEY, played_date TEXT NOT NULL, date_precision TEXT NOT NULL,
 event_id TEXT NOT NULL, tier TEXT NOT NULL, surface TEXT NOT NULL,
 winner_id TEXT NOT NULL REFERENCES players(id), loser_id TEXT NOT NULL REFERENCES players(id),
 score TEXT NOT NULL, retired INTEGER NOT NULL, source_file TEXT, raw_json TEXT NOT NULL);
CREATE INDEX match_dates ON matches(played_date);
CREATE TABLE ranking_editions (date TEXT PRIMARY KEY, row_count INTEGER NOT NULL);
CREATE TABLE official_rankings (edition TEXT REFERENCES ranking_editions(date), player_id TEXT,
 rank INTEGER NOT NULL, points INTEGER, PRIMARY KEY(edition, player_id));
CREATE TABLE power_snapshots (date TEXT, player_id TEXT, rank INTEGER, rating REAL, universe_count INTEGER,
 PRIMARY KEY(date, player_id));
CREATE TABLE sources (file TEXT PRIMARY KEY, url TEXT NOT NULL, sha256 TEXT NOT NULL,
 retrieved_at TEXT NOT NULL, row_count INTEGER NOT NULL, latest_date TEXT, provenance_json TEXT NOT NULL);
CREATE TABLE identity_mappings (provider TEXT, external_id TEXT, player_id TEXT REFERENCES players(id),
 PRIMARY KEY(provider, external_id));
CREATE TABLE health_reports (player_id TEXT PRIMARY KEY, report_json TEXT NOT NULL);
CREATE TABLE health_report_history (player_id TEXT, sha256 TEXT, report_json TEXT NOT NULL,
 PRIMARY KEY(player_id, sha256));
"""


def publish_database(path, matches, rankings, snapshots, manifest, metadata, health):
    temp = Path(str(path) + ".tmp")
    if temp.exists():
        temp.unlink()
    db = sqlite3.connect(temp)
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(SCHEMA)
        with db:
            people = {}
            for m in matches:
                for side, pid in (("winner", m["w"]), ("loser", m["l"])):
                    people[pid] = (pid, m[side + "_name"], m.get(side + "_ioc", ""), json.dumps({k: v for k, v in m.items() if k.startswith(side + "_")}))
            db.executemany("INSERT INTO players VALUES (?,?,?,?)", people.values())
            db.executemany("INSERT INTO identity_mappings VALUES (?,?,?)", (("sackmann", p, p) for p in people))
            db.executemany("INSERT INTO matches VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
                (m["identity"], m["day"].isoformat(), m["precision"], m["event"], m["tier"], m["surface"], m["w"], m["l"], m["score"], int(m["retired"]), m.get("source_file"),
                 json.dumps({k: v for k, v in m.items() if k != "day"})) for m in matches))
            for day, rows in rankings.items():
                db.execute("INSERT INTO ranking_editions VALUES (?,?)", (day.isoformat(), len(rows)))
                db.executemany("INSERT INTO official_rankings VALUES (?,?,?,?)", ((day.isoformat(), pid, p["rank"], p["points"]) for pid, p in rows.items()))
            db.executemany("INSERT INTO power_snapshots VALUES (?,?,?,?,?)", snapshots)
            db.executemany("INSERT INTO sources VALUES (?,?,?,?,?,?,?)", ((m["file"], m["url"], m["sha256"], m["retrieved_at"], m["rows"], m.get("latest_date"), json.dumps(m)) for m in manifest))
            db.executemany("INSERT INTO metadata VALUES (?,?)", ((k, json.dumps(v)) for k, v in metadata.items()))
            db.executemany("INSERT INTO health_reports VALUES (?,?)", ((pid, json.dumps(report)) for pid, report in health.items()))
            if path.exists():
                with closing(sqlite3.connect(path)) as previous:
                    tables = {row[0] for row in previous.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    if "health_report_history" in tables:
                        db.executemany("INSERT OR IGNORE INTO health_report_history VALUES (?,?,?)", previous.execute("SELECT * FROM health_report_history"))
                    if "health_reports" in tables:
                        for pid, raw in previous.execute("SELECT * FROM health_reports"):
                            db.execute("INSERT OR IGNORE INTO health_report_history VALUES (?,?,?)", (pid, hashlib.sha256(raw.encode()).hexdigest(), raw))
            for pid, report in health.items():
                raw = json.dumps(report, sort_keys=True)
                db.execute("INSERT OR IGNORE INTO health_report_history VALUES (?,?,?)", (pid, hashlib.sha256(raw.encode()).hexdigest(), raw))
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite integrity check failed")
    finally:
        db.close()
    temp.replace(path)
