"""Daily fail-closed builder: python -m sports.update [--inputs private.json]."""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from zoneinfo import ZoneInfo

from tennis.update import atomic_json
from .models import BOOKS, SPORTS, VERSION, category, implied, performance, select_props, summarize

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'site/sports/analysis'


def stamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None: raise ValueError('Timezone required')
    return parsed


def validate(row, now, tool):
    """Only stable IDs with explicit dated provenance are eligible."""
    if row['book'] not in BOOKS or row['sport'] not in SPORTS: raise ValueError('Unsupported book/sport')
    implied(row['odds'])
    start = stamp(row['starts_at'])
    as_of = stamp(row['as_of'])
    if not as_of <= now < start or (now - as_of).total_seconds() > 21600: raise ValueError('Stale or in-play input')
    if start.astimezone(ZoneInfo('America/New_York')).date() != now.astimezone(ZoneInfo('America/New_York')).date(): raise ValueError('Not today’s slate')
    for key in ('id', 'event_id', 'subject_id', 'label', 'source', 'evidence'):
        if not isinstance(row.get(key), str) or not row[key].strip(): raise ValueError('Missing identity/provenance')
    if row.get('identity_verified') is not True or row.get('availability_verified') is not True: raise ValueError('Unverified identity/availability')
    if tool == 'prop-hunt':
        if row['sport'] != 'NFL': raise ValueError('NFL only')
        if not row.get('matchup_evidence') or not row.get('opportunity_evidence'): raise ValueError('Missing context evidence')
        if len(row['values']) < 8 or len(row['values']) != len(row['game_dates']): raise ValueError('Insufficient/undated observations')
        if row.get('side') not in ('Over', 'Under') or not row.get('market'): raise ValueError('Unsupported side or missing market')
        if row['game_dates'] != sorted(set(row['game_dates'])): raise ValueError('Duplicate/out-of-order observations')
        eastern = now.astimezone(ZoneInfo('America/New_York'))
        season = eastern.year if eastern.month >= 8 else eastern.year - 1
        if row.get('season') != season or any(not f'{season}-08-01' <= d < eastern.date().isoformat() for d in row['game_dates']): raise ValueError('Season or time leakage')
        nums = [*row['values'], row['line'], row['matchup_multiplier'], row['opportunity_multiplier']]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in nums): raise ValueError('Invalid numeric input')
        if not .5 <= row['matchup_multiplier'] * row['opportunity_multiplier'] <= 1.5: raise ValueError('Unstable context adjustment')
    else:
        p = row['probability']
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 < p < 1: raise ValueError('Invalid probability')
        if not row.get('projection_model') or row.get('independent_projection') is not True: raise ValueError('Missing independent model')
    return row


def build(inputs=None, public=PUBLIC, now=None):
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(ZoneInfo('America/New_York')).date().isoformat()
    public = Path(public); inputs = inputs or {}
    # Settlement ledger separate from forecasts; never silently change settled outcomes.
    ledger_path = public / 'settlements.json'
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    for result in inputs.get('results', []):
        if result.get('verified_final') is not True or result['outcome'] not in ('win', 'loss', 'push', 'void') or not result.get('source') or stamp(result['final_at']) > now: raise ValueError('Unverified final result')
        key = result['prediction_id']
        # Only known, already frozen forecasts may settle; a pre-start "final" is invalid.
        known = None
        for archive in public.glob('archive/*/*/*.json'):
            data = json.loads(archive.read_text())
            known = next((r for r in data['predictions'] if r['prediction_id'] == key), None)
            if known: break
        if not known or stamp(result['final_at']) <= stamp(known['starts_at']): raise ValueError('Unknown prediction or impossible final')
        if key in ledger and ledger[key] != result: raise ValueError('Settlement correction requires explicit review')
        ledger[key] = result
    atomic_json(ledger_path, ledger)
    status = {}
    for tool in ('prop-hunt', 'upset-alert'):
        valid, rejected = [], 0
        seen = set()
        for row in inputs.get(tool, []):
            try:
                validate(row, now, tool)
                if tool == 'prop-hunt' and not any(s['event_id'] == row['event_id'] and stamp(s['starts_at']) == stamp(row['starts_at']) for s in inputs.get('nfl_schedule', [])): raise ValueError('Event absent from verified schedule')
                identity = (row['book'], row['id'])
                if identity in seen: raise ValueError('Duplicate candidate')
                seen.add(identity); valid.append(row)
            except (KeyError, ValueError, TypeError): rejected += 1
        books = {}
        for book in BOOKS:
            path = public / 'archive' / tool / book / (today + '.json')
            if path.exists():
                snapshot = json.loads(path.read_text())
            else:
                rows = [r for r in valid if r['book'] == book]
                if tool == 'prop-hunt':
                    # Authoritative schedule count, not number of games with accepted props.
                    schedule = inputs.get('nfl_schedule', [])
                    games = len({r['event_id'] for r in schedule if stamp(r['starts_at']).astimezone(ZoneInfo('America/New_York')).date().isoformat() == today})
                    lists = select_props(rows, games) if games else {'top': [], 'safe': []}
                    predictions = [{**r, 'list': name} for name, group in lists.items() for r in group]
                else:
                    predictions = [{**r, 'category': category(r['probability']), 'list': 'favorites'} for r in rows if r['odds'] <= -200]
                for row in predictions:
                    row['prediction_id'] = hashlib.sha256(f"{tool}:{book}:{today}:{row['list']}:{row['id']}".encode()).hexdigest()[:24]
                    row['date'] = today; row['model_version'] = VERSION
                snapshot = {'date': today, 'generated_at': now.isoformat(), 'model_version': VERSION, 'predictions': predictions}
                # Do not freeze an empty/unconnected slate: allow later pregame connection.
                if predictions: atomic_json(path, snapshot)
            history = []
            for archive in sorted(path.parent.glob('*.json')):
                history.extend(json.loads(archive.read_text())['predictions'])
            history = [{**r, 'outcome': ledger.get(r['prediction_id'], {}).get('outcome', 'pending')} for r in history]
            books[book] = {'current': snapshot, 'history': history, 'performance': performance(history, today)}
            if tool == 'upset-alert':
                books[book]['market_watchlist'] = [r for r in inputs.get('market_watchlist', []) if r['book'] == book]
        snapshot = {'tool': tool, 'date': today, 'checked_at': now.isoformat(), 'rejected_inputs': rejected, 'status': 'Verified forecasts available' if any(b['current']['predictions'] for b in books.values()) else 'Awaiting verified odds, projections and settlement feeds. No picks have been invented.', 'books': books, 'review': 'Daily review computes win rates and Brier scores from frozen pregame forecasts. No automatic parameter changes: chronological holdout validation is required before a new model version.'}
        atomic_json(public / (tool + '.json'), snapshot)
        # Daily review history is versioned separately and does not alter predictions.
        yesterday = (date.fromisoformat(today) - timedelta(days=1)).isoformat()
        atomic_json(public / 'reviews' / tool / (today + '.json'), {'date': today, 'model_version': VERSION, 'previous_day': yesterday, 'previous_day_results': {b: summarize([r for r in v['history'] if r['date'] == yesterday]) for b, v in books.items()}, 'books': {b: v['performance'] for b, v in books.items()}, 'recommendation': 'Collect more independently settled outcomes before proposing parameter changes.'})
        status[tool] = snapshot['status']
    return status


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--inputs', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(json.loads(args.inputs.read_text()) if args.inputs else None), indent=2))
