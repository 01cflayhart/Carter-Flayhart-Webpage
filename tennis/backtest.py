"""Out-of-time pre-date predictions against basic Elo and ATP-rank baselines."""
import argparse
from collections import defaultdict
import json
import math

from .engine import VERSION, parse_date, replay, shift_months
from .update import ROOT, atomic_json, load_source, read_json


def metrics(rows, name):
    pairs = [(r[name] if r["winner_first"] else 1 - r[name], int(r["winner_first"])) for r in rows if r[name] is not None]
    if not pairs:
        return {"n": 0}
    bins = defaultdict(list)
    for p, y in pairs:
        bins[min(9, int(p * 10))].append((p, y))
    return {"n": len(pairs), "log_loss": round(sum(-math.log(max(1e-12, p if y else 1 - p)) for p, y in pairs) / len(pairs), 5),
            "brier": round(sum((p - y) ** 2 for p, y in pairs) / len(pairs), 5),
            "calibration": [{"bin": f"{i / 10:.1f}–{(i + 1) / 10:.1f}", "n": len(v), "predicted": round(sum(p for p, _ in v) / len(v), 4),
                             "observed": round(sum(y for _, y in v) / len(v), 4)} for i, v in sorted(bins.items())]}


def run(start=None, end=None):
    config = read_json(ROOT / "config.json")
    matches, _, _, _ = load_source(config, ROOT / "data", offline=True)
    cutoff = parse_date(end) if end else max(m["day"] for m in matches)
    begin = parse_date(start) if start else shift_months(cutoff, -12)
    _, _, _, _, predictions, _ = replay(matches, config, cutoff, collect=False)
    rows = [r for r in predictions if begin.isoformat() < r["date"] <= cutoff.isoformat() and not r["retired"]]
    common = [r for r in rows if r["atp"] is not None]
    report = {"model_version": VERSION, "rating_config": config["rating"], "source_revision": config["source"]["revision"],
              "start_exclusive": begin.isoformat(), "end_inclusive": cutoff.isoformat(), "warmup_from": matches[0]["day"].isoformat(),
              "method": "Chronological frozen-date replay; no future ranks; event-start dates approximate. Not a tuned or independent final holdout.",
              "common_ranked_sample": {n: metrics(common, n) for n in ("model", "elo", "atp")},
              "all_played_sample": {n: metrics(rows, n) for n in ("model", "elo", "atp")},
              "by_tier": {t: {n: metrics([r for r in common if r["tier"] == t], n) for n in ("model", "elo", "atp")} for t in sorted({r["tier"] for r in common})},
              "by_surface": {s: {n: metrics([r for r in common if r["surface"] == s], n) for n in ("model", "elo", "atp")} for s in sorted({r["surface"] for r in common})}}
    atomic_json(ROOT / "reports" / "backtest.json", report)
    print(json.dumps({k: v for k, v in report.items() if k in ("start_exclusive", "end_inclusive", "common_ranked_sample")}, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start")
    parser.add_argument("--end")
    args = parser.parse_args()
    run(args.start, args.end)
