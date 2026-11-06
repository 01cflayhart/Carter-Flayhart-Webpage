"""Pure selection and evaluation functions. Inputs must be verified before calling."""
import math
from datetime import date, timedelta

VERSION = 'experimental-0.1'
BOOKS = ('draftkings', 'fanduel', 'fanatics', 'caesars')
SPORTS = ('NFL', 'NCAAF', 'NCAAB', 'Tennis')
CATEGORIES = ('Locks', 'No Sweats', 'Parlay Pieces', 'Better to Avoid', 'Storm Chasers')


def implied(odds):
    if not isinstance(odds, (int, float)) or not math.isfinite(odds) or abs(odds) < 100:
        raise ValueError('Invalid American odds')
    return -odds / (100 - odds) if odds < 0 else 100 / (odds + 100)


def category(probability):
    return next((label for floor, label in zip((.95, .85, .75, .60, 0), CATEGORIES) if probability >= floor), None)


def slate_limit(games):
    return 0 if games == 0 else 3 if games == 1 else 5 if games < 4 else 10


def prop_estimate(row):
    """Recent games carry more weight. Beta(1,1) smoothing prevents certainty.

    Values are current-season completed games in chronological order, pre-event
    only. Multipliers are sourced relative matchup/role estimates, NOT guesses.
    """
    values = row['values']
    if len(values) < 8 or row['side'] not in ('Over', 'Under'):
        raise ValueError('Insufficient current-season evidence')
    factor = row['matchup_multiplier'] * row['opportunity_multiplier']
    if not .5 <= factor <= 1.5:
        raise ValueError('Unstable context adjustment')
    line = row['line']
    sign = 1 if row['side'] == 'Over' else -1
    weights = [.92 ** (len(values) - i - 1) for i in range(len(values))]
    adjusted = [v * factor for v in values]
    # Push observations do not become losses or wins.
    pairs = [(v, w) for v, w in zip(adjusted, weights) if v != line]
    probability = (1 + sum(w for v, w in pairs if sign * (v - line) > 0)) / (2 + sum(w for _, w in pairs))
    observed = sum(sign * (v - line) > 0 for v in values) / len(values)
    return probability, observed


def select_props(rows, games):
    candidates = []
    for row in rows:
        probability, hit_rate = prop_estimate(row)
        edge = probability - implied(row['odds'])
        candidates.append({**row, 'probability': round(probability, 6), 'season_hit_rate': hit_rate, 'edge': round(edge, 6)})
    ranked = sorted(candidates, key=lambda r: (-r['probability'], -r['edge'], r['id']))
    # Avoid filling a list with multiple alternate thresholds on the same market.
    def unique(items):
        seen = set(); result = []
        for item in items:
            key = (item['event_id'], item['subject_id'], item['market'], item['side'])
            if key not in seen:
                seen.add(key); result.append(item)
        return result
    top = unique([r for r in ranked if r['odds'] >= -150 and r['edge'] >= .03 and r['probability'] >= .55])[:slate_limit(games)]
    safe = [r for r in candidates if r['probability'] >= .85 and r['season_hit_rate'] >= .90]
    # Strongest qualifying over (or lowest qualifying under), not repetitive ladders.
    safe.sort(key=lambda r: (-r['line'] if r['side'] == 'Over' else r['line'], -r['probability']))
    safe = unique(safe)
    for item in safe:
        item['alternatives'] = [{'line': r['line'], 'probability': r['probability']} for r in ranked if r['id'] != item['id'] and all(r[k] == item[k] for k in ('event_id', 'subject_id', 'market', 'side')) and (r['line'] < item['line'] if item['side'] == 'Over' else r['line'] > item['line'])]
    safe.sort(key=lambda r: (-r['probability'], r['id']))
    return {'top': [{**r, 'rank': i + 1} for i, r in enumerate(top)], 'safe': safe}


def summarize(rows):
    wins = sum(r['outcome'] == 'win' for r in rows)
    losses = sum(r['outcome'] == 'loss' for r in rows)
    settled = [r for r in rows if r['outcome'] in ('win', 'loss')]
    return {'wins': wins, 'losses': losses, 'pushes': sum(r['outcome'] == 'push' for r in rows), 'voids': sum(r['outcome'] == 'void' for r in rows), 'pending': sum(r['outcome'] == 'pending' for r in rows), 'n': len(settled), 'win_rate': wins / len(settled) if settled else None, 'brier': sum((r['probability'] - (r['outcome'] == 'win')) ** 2 for r in settled) / len(settled) if settled else None}


def performance(rows, today):
    output = {}
    for window in ('all', '30', '7'):
        selected = [r for r in rows if r['date'] <= today and (window == 'all' or r['date'] >= (date.fromisoformat(today) - timedelta(days=int(window) - 1)).isoformat())]
        groups = {'All picks': selected}
        for row in selected:
            keys = [row.get('list', 'favorites')]
            if row.get('rank'): keys.append('Top rank ' + str(row['rank']))
            if row.get('category'): keys.append(row['category'])
            if row.get('sport'): keys.append(row['sport'])
            for key in keys: groups.setdefault(key, []).append(row)
        # All picks includes each list placement; cross-list duplication is disclosed.
        output[window] = {key: summarize(group) for key, group in groups.items()}
    return output
