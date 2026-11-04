"""Fetch/cache licensed CSVs, validate, replay, and publish. Safe to schedule."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

from .engine import build, integer, normalize, parse_date
from .storage import publish_database

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(str(path) + ".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    temp.replace(path)


def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else ({} if default is None else default)


def fetch(url):
    if not url.startswith("https://"):
        raise ValueError("Source URLs must use HTTPS")
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CourtCurrent/0.1 personal-research"})
            with urllib.request.urlopen(req, timeout=90) as response:
                raw = response.read(50_000_001)
            if len(raw) > 50_000_000:
                raise ValueError("Source exceeds 50 MB limit")
            return raw
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(2 ** attempt)


def load_source(config, data, offline=False, refresh=False):
    source = config["source"]
    if source.get("profile", "sackmann") != "sackmann":
        raise ValueError("Unsupported source profile; add and test an explicit adapter first")
    entries = [(pattern.format(year=y), family, "match") for y in source["years"] for family, pattern in source["families"].items()]
    entries += [(name, "Official rankings", "ranking") for name in source["rankings"]]
    entries += [(name, "Documentation", "document") for name in source.get("documents", [])]
    rows, ranking_rows, manifest = [], [], []
    for name, family, kind in entries:
        if Path(name).name != name:
            raise ValueError("Only flat source filenames are supported")
        url = source["base_url"].rstrip("/") + "/" + name
        path = data / "raw" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        meta_path = Path(str(path) + ".meta.json")
        meta = read_json(meta_path)
        if offline and (not path.exists() or meta.get("url") != url):
            raise ValueError(f"Missing cache or changed source in offline mode: {name}")
        if not offline and (refresh or not path.exists() or meta.get("url") != url):
            print(f"Fetching {name}", flush=True)
            raw = fetch(url)
            if kind != "document":
                parsed = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
                required = "ranking_date" if kind == "ranking" else "tourney_date"
                if not parsed or required not in parsed[0]:
                    raise ValueError(f"Invalid CSV schema: {name}")
            temp = Path(str(path) + ".download")
            temp.write_bytes(raw)
            temp.replace(path)
            meta = {"url": url, "retrieved_at": now(), "sha256": hashlib.sha256(raw).hexdigest(), "revision": source["revision"]}
            atomic_json(meta_path, meta)
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != meta.get("sha256"):
            raise ValueError(f"Checksum mismatch: {name}")
        parsed = [] if kind == "document" else list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        if not parsed and kind != "document":
            raise ValueError(f"Empty source: {name}")
        if kind == "match":
            rows.extend(dict(r, family=family, source_file=name) for r in parsed)
        elif kind == "ranking":
            ranking_rows.extend(parsed)
        dates = [r.get("ranking_date") or r.get("match_date") or r.get("tourney_date") for r in parsed]
        manifest.append(dict(meta, file=name, family=family, kind=kind, rows=len(parsed), parser_version="sackmann-csv-v1", latest_date=parse_date(max(dates)).isoformat() if dates else None))
    rankings, conflicts = {}, set()
    for row in ranking_rows:
        day = parse_date(row["ranking_date"])
        pid = row.get("player") or row.get("player_id")
        rank = integer(row.get("rank") or row.get("ranking"))
        points = row.get("points") if "points" in row else row.get("ranking_points")
        if not pid or not rank:
            raise ValueError("Malformed official ranking row")
        entry = {"rank": rank, "points": int(points) if points and str(points).isdigit() else None}
        if (day, pid) in conflicts:
            continue
        if pid in rankings.setdefault(day, {}) and rankings[day][pid] != entry:
            conflicts.add((day, pid))
            del rankings[day][pid]
            continue
        rankings[day][pid] = entry
    excluded_editions = []
    for raw_day, reason in source.get("excluded_ranking_editions", {}).items():
        day = parse_date(raw_day)
        if day in rankings:
            excluded_editions.append({"date": day.isoformat(), "reason": reason, "rows": len(rankings.pop(day))})
    for day, edition in rankings.items():
        ranks = {r["rank"] for r in edition.values()}
        if 1 not in ranks:
            raise ValueError(f"Ranking edition missing rank 1: {day}")
        if len(edition) < source.get("min_ranking_rows", 1000):
            raise ValueError(f"Ranking edition appears truncated: {day}, {len(edition)} rows")
    matches, audit = normalize(rows)
    audit["quarantined_official_rankings"] = [{"date": d.isoformat(), "player": p} for d, p in sorted(conflicts)]
    audit["excluded_ranking_editions"] = excluded_editions
    return matches, rankings, manifest, audit


def update(root=ROOT, offline=False, refresh=False, as_of=None):
    root = Path(root)
    config = read_json(root / "config.json")
    data = root / "data"
    data.mkdir(exist_ok=True)
    lock = data / "update.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise RuntimeError("Update locked. Investigate data/update.lock before removing a stale lock.")
    with os.fdopen(fd, "w") as f:
        f.write(json.dumps({"pid": os.getpid(), "started_at": now()}))
    try:
        matches, rankings, manifest, audit = load_source(config, data, offline, refresh)
        if not matches:
            raise ValueError("No playable matches")
        latest = max(m["day"] for m in matches)
        cutoff = parse_date(as_of) if as_of else latest
        if cutoff > latest:
            raise ValueError("Cannot publish a cutoff beyond available results")
        if any(m["day"] > datetime.now(timezone.utc).date() for m in matches):
            raise ValueError("Source contains future-dated results")
        health = read_json(data / "health.json")
        snapshot, historical, _ = build(matches, rankings, config, cutoff, health, read_json(data / "photos.json"))
        if not snapshot["players"]:
            raise ValueError("Empty ranking publication")
        coverage = {}
        for m in matches:
            key = m["tier"] + " · " + m["surface"]
            if m["day"] <= cutoff:
                c = coverage.setdefault(key, {"latest": m["day"].isoformat(), "matches": 0})
                c["latest"] = max(c["latest"], m["day"].isoformat())
                c["matches"] += int(m["day"] > parse_date(snapshot["window_start_exclusive"]))
        snapshot.update(generated_at=now(), source=config["source"], manifest=manifest, audit=audit,
                        coverage=coverage, historical=not config["source"].get("live", False),
                        date_precision="Event-start approximations; explicit match_date supported. Same-date power ranks frozen before all outcomes.",
                        warnings=["Archive is not a live feed; completeness is not guaranteed.", "ATP comparisons use event-start ranks supplied with results, not verified exact pre-match rankings.",
                                  "Age estimates come from dated match metadata. Photos and injuries require separately licensed/sourced information.",
                                  "Rating parameters are provisional; consult the walk-forward backtest before relying on predictions."],
                        rating_config=config["rating"])
        publish_database(data / "tennis.sqlite", matches, rankings, historical, manifest,
                         {"generated_at": snapshot["generated_at"], "model": snapshot["model_version"], "config": config, "audit": audit}, health)
        atomic_json(data / "snapshot.json", snapshot)
        atomic_json(data / "status.json", {"ok": True, "attempted_at": now(), "message": "Historical snapshot published"})
        print(f"Published {len(snapshot['players'])} players / {snapshot['match_count']} matches, through {cutoff}. NOT a live feed.", flush=True)
        return snapshot
    except Exception as error:
        atomic_json(data / "status.json", {"ok": False, "attempted_at": now(), "message": str(error)})
        raise
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--as-of", help="YYYY-MM-DD; defaults to actual latest source event date")
    args = parser.parse_args()
    try:
        update(offline=args.offline, refresh=args.refresh, as_of=args.as_of)
    except Exception as error:
        print(f"Update failed; last published API snapshot retained: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
