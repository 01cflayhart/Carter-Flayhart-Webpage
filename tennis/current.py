"""Current, independently replayed ATP/WTA publications from licensed open CSVs.

No identity joins with the historical Sackmann archive are attempted. A result
without a completed score (or explicit retirement) is not assumed to be played.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import os
from pathlib import Path
import re

from .engine import build, normalize, parse_date
from .update import ROOT, atomic_json, fetch, now, read_json
from .backtest import metrics

SURFACE = {"dur": "Outdoor hard", "dur intérieur": "Indoor hard", "terre battue": "Clay",
           "gazon": "Grass", "moquette intérieur": "Carpet"}
LEVEL = {"Challenger": "C", "Main tour": "A", "Masters": "M", "Grand Chelem": "G",
         "Coupe Davis / BJK Cup": "D", "ITF": "15"}


def adapt(rows, tour, through):
    result, audit, ids = [], Counter(), {}
    for r in rows:
        if r.get("genre", "").upper() != tour:
            continue
        day = parse_date(r["date"][:10])
        if day > through:
            audit["after_cutoff"] += 1
            continue
        if r.get('surface') == 'moquette intérieur':
            audit['carpet_excluded'] += 1
            continue
        mid = r["match_id"]
        if not mid or not r["tournoi_id"]:
            raise ValueError("Source match/event ID missing")
        if mid in ids:
            if ids[mid] != r:
                raise ValueError(f"Conflicting source match ID {mid}")
            audit["duplicates"] += 1
            continue
        ids[mid] = r
        a, b, w = r["joueur1_id"], r["joueur2_id"], r["vainqueur_id"]
        if not a or not b or a == b or w not in (a, b):
            audit["no_valid_winner"] += 1
            continue
        if r["categorie"] not in LEVEL:
            audit["unknown_competition_type"] += 1
            continue
        score = r["score"].strip()
        sets = re.findall(r"(\d+)-(\d+)(?:\(\d+\))?", score)
        retired = "RET" in score.upper()
        if not sets or any(t in score.upper() for t in ("W/O", "WALKOVER", "DEF", "ABN")):
            audit["missing_or_unplayed_score"] += 1
            continue
        wins = [0, 0]
        for x, y in sets:
            x, y = int(x), int(y)
            if (max(x, y) >= 6 and abs(x-y) >= 2) or (max(x, y) == 7 and min(x, y) == 6):
                wins[0 if x > y else 1] += 1
        # The CSV gives no reliable qualifying-round map. Conservatively omit
        # two-set men's Slam qualifying rather than mislabel incomplete main draws.
        qualifying = r['categorie'] != 'Coupe Davis / BJK Cup' and r['tour'] in ('0','1','2','3')
        needed = 3 if tour == "ATP" and r["categorie"] == "Grand Chelem" and not qualifying else 2
        winner_side = 0 if w == a else 1
        if not retired and (wins[winner_side] != needed or wins[1-winner_side] >= needed):
            audit["incomplete_or_ambiguous_score"] += 1
            continue
        # Scores in this source are player-1 oriented, not winner oriented.
        if w == b:
            score = re.sub(r"(\d+)-(\d+)(\(\d+\))?", lambda m: f"{m[2]}-{m[1]}{m[3] or ''}", score)
        prefix = f"valuebetennis:{tour}:"
        level = "15" if re.match(r"^[MW]\d+\b", r["tournoi"]) else LEVEL[r["categorie"]]
        result.append({"tourney_id": prefix+r["tournoi_id"], "tourney_name": r["tournoi"],
                       "tourney_date": day.isoformat(), "match_date": day.isoformat(),
                       "source_match_id": prefix+mid, "round": ('Q' if qualifying else 'Source round ')+r["tour"],
                       "winner_id": prefix+w, "loser_id": prefix+(b if w == a else a),
                       "winner_name": r["joueur1"] if w == a else r["joueur2"],
                       "loser_name": r["joueur2"] if w == a else r["joueur1"],
                       "score": score, "surface": SURFACE.get(r["surface"], "Unknown"),
                       "tourney_level": level, "source_file": r.get("source_file", ""),
                       "family": "ITF" if level == "15" else "Tour"})
    return result, dict(audit)


def download(root, source, through, offline=False):
    data = root/"data"/"current"/"raw"
    data.mkdir(parents=True, exist_ok=True)
    rows, manifest = [], []
    for year in range(source["first_year"], through.year+1):
        name = f"valuebetennis-matchs-{year}.csv"
        url = source["base_url"]+"/"+name
        path, meta_path = data/f"{year}.csv", data/f"{year}.meta.json"
        if not offline:
            raw = fetch(url)
            parsed = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), delimiter=";"))
            if not parsed or not {"match_id", "genre", "score", "date", "vainqueur_id"} <= parsed[0].keys():
                raise ValueError(f"Invalid open results CSV: {name}")
            temp = path.with_suffix(".download"); temp.write_bytes(raw); temp.replace(path)
            atomic_json(meta_path, {"url": url, "sha256": hashlib.sha256(raw).hexdigest(), "retrieved_at": now()})
        meta = read_json(meta_path)
        raw = path.read_bytes()
        if meta.get("url") != url or hashlib.sha256(raw).hexdigest() != meta.get("sha256"):
            raise ValueError(f"Cache provenance mismatch for {year}")
        parsed = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), delimiter=";"))
        for row in parsed:
            row["source_file"] = name
        rows.extend(parsed)
        manifest.append(dict(meta, file=name, rows=len(parsed), latest_date=max(r["date"][:10] for r in parsed)))
    return rows, manifest


def update(root=ROOT, offline=False, through=None):
    root = Path(root)
    source = read_json(root/"current-source.json")
    rating = read_json(root/"config.json")["rating"]
    through = parse_date(through) if through else datetime.now(timezone.utc).date()
    if through > datetime.now(timezone.utc).date():
        raise ValueError("Cannot publish a future cutoff")
    data = root/"data"/"current"; data.mkdir(parents=True, exist_ok=True)
    lock = data/"update.lock"
    fd = os.open(lock, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(str(os.getpid()))
    try:
        rows, manifest = download(root, source, through, offline)
        publications = {}
        from .identities import linked_rankings
        for tour in ("ATP", "WTA"):
            adapted, audit = adapt(rows, tour, through)
            matches, normalized = normalize(adapted)
            if not matches:
                raise ValueError(f"No usable {tour} matches")
            current_ranks, identity_coverage = linked_rankings(root, tour, through)
            snapshot, _, predictions = build(matches, {}, {"rating": rating}, through, current_rankings=current_ranks)
            latest = max(m["day"] for m in matches)
            coverage = {}
            for m in matches:
                if m["day"].isoformat() <= snapshot["window_start_exclusive"]:
                    continue
                c = coverage.setdefault(m["tier"]+" · "+m["surface"], {"latest": m["day"].isoformat(), "matches": 0})
                c["latest"] = max(c["latest"], m["day"].isoformat()); c["matches"] += 1
            revision = hashlib.sha256("".join(m["sha256"] for m in manifest).encode()).hexdigest()
            snapshot.update(tour=tour, generated_at=now(), source=dict(source, revision=revision),
                historical=False, latest_result=latest.isoformat(), manifest=manifest,
                audit=dict(audit, **normalized), coverage=coverage, rating_config=rating,
                official_rankings_available=bool(current_ranks), historical_official_rankings_available=False,
                official_power_prior=bool(current_ranks), official_identity_coverage=identity_coverage,
                official_observed_at=identity_coverage.get('observed_at'),
                date_precision="Source-reported UTC match dates; same-date ratings frozen before all outcomes.",
                warnings=["Open results feed checked through "+through.isoformat()+"; latest accepted "+tour+" result "+latest.isoformat()+". Coverage is not certified exhaustive.",
                    f"Current TennisONE ranks/points are linked for {len(current_ranks)} players via independently checked profile metadata. Unverified players remain unknown. No old archive identities are mixed in.",
                    "TennisONE provides no ranking edition date. Observations up to 14 days old can supply a bounded current-rank prior, never historical match ranks or a historical backtest feature.",
                    "Unfinished, missing and ambiguous scores are excluded. Source rounds 0–3 are qualifying; tour qualifying carries 40% weight, Challenger qualifying 15%, and ITF qualifying 4%.",
                    "Tour main draws carry 100% rating influence, Challengers 30%, ITF 8%, and team events 50%. Both long-term anchor and recent-form changes are weighted. Raw W–L counts are not weighted.",
                    "Outdoor hard and indoor hard are separate. Carpet is excluded entirely; hard courts without a verified setting are unknown, not guessed.",
                    "Sources classify some women's ITF events as Challenger; events explicitly named M/W followed by a prize tier are classified as ITF.",
                    "Scheduled UTC starts are not verified completion timestamps. No result from later today is inferred. Provisional model; not an independent final holdout."])
            evaluation = [p for p in predictions if p["date"] > snapshot["window_start_exclusive"] and not p["retired"]]
            snapshot["backtest"] = {"start_exclusive": snapshot["window_start_exclusive"], "end_inclusive": through.isoformat(),
                "all_played_sample": {n: metrics(evaluation, n) for n in ("model", "elo")},
                "method": "Walk-forward frozen-date replay of result-based scores only, excluding the current TennisONE prior. No historical official-rank baseline available; provisional, not an untouched holdout."}
            publications[tour] = snapshot
        # Both tours must validate before either is offered to the exporter.
        for tour, snapshot in publications.items():
            atomic_json(data/tour/"snapshot.json", snapshot)
            atomic_json(data/tour/"status.json", {"ok": True, "attempted_at": now(), "message": "Open results feed replayed through "+through.isoformat()})
            print(f"{tour}: {len(snapshot['players'])} players, {snapshot['match_count']} matches; checked through {through}, latest accepted result {snapshot['latest_result']}", flush=True)
        return publications
    except Exception as error:
        for tour in ("ATP", "WTA"):
            atomic_json(data/tour/"status.json", {"ok": False, "attempted_at": now(), "message": str(error)})
        raise
    finally:
        lock.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--through")
    args = parser.parse_args()
    update(offline=args.offline, through=args.through)
