"""Public nflverse connection and optional authenticated Odds API adapter.

No name-only player join; raw feeds never automatically become model evidence.
"""
import csv
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import math
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tennis.update import atomic_json

ROOT = Path(__file__).resolve().parents[1]
def season_year():
    now = datetime.now(timezone.utc)
    return now.year if now.month >= 8 else now.year - 1


NFLVERSE = f'https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season_year()}.csv'
SCHEDULE = 'https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'
BOOK_KEYS = {'draftkings': 'draftkings', 'fanduel': 'fanduel', 'fanatics': 'fanatics', 'williamhill_us': 'caesars'}
MARKETS = 'player_rush_yds,player_rush_reception_yds,player_reception_yds,player_receptions,player_pass_yds,player_anytime_td,team_totals'


def favorite_watchlist(cache, now=None):
    """Fresh source-native moneylines, NOT projections or identity crosswalks."""
    now = now or datetime.now(timezone.utc)
    eastern = ZoneInfo('America/New_York')
    def fresh(value):
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None or not 0 <= (now - parsed).total_seconds() <= 21600:
            raise ValueError('Stale observation')
        return parsed.astimezone(timezone.utc)
    try:
        fresh(cache['checked_at'])
    except (KeyError, ValueError, TypeError, AttributeError):
        return []
    rows = {}
    for key, events in cache.get('feeds', {}).items():
        sport = {'americanfootball_nfl': 'NFL', 'americanfootball_ncaaf': 'NCAAF', 'basketball_ncaab': 'NCAAB'}.get(key)
        if not sport and key.startswith(('tennis_atp_', 'tennis_wta_')):
            sport = 'Tennis'
        if not sport or not isinstance(events, list):
            continue
        for event in events:
            try:
                start = datetime.fromisoformat(event['commence_time'].replace('Z', '+00:00'))
                if start.tzinfo is None or start <= now or start.astimezone(eastern).date() != now.astimezone(eastern).date():
                    continue
                if not all(isinstance(event[k], str) and event[k].strip() for k in ('id', 'home_team', 'away_team')):
                    continue
                for bookmaker in event.get('bookmakers', []):
                    book = BOOK_KEYS.get(bookmaker.get('key'))
                    if not book:
                        continue
                    for market in bookmaker.get('markets', []):
                        if market.get('key') != 'h2h':
                            continue
                        try:
                            observed = fresh(market.get('last_update') or bookmaker.get('last_update'))
                        except (ValueError, TypeError, AttributeError):
                            continue
                        for outcome in market.get('outcomes', []):
                            odds = outcome.get('price')
                            name = outcome.get('name')
                            if name not in (event['home_team'], event['away_team']) or isinstance(odds, bool) or not isinstance(odds, (int, float)) or not math.isfinite(odds) or odds > -200:
                                continue
                            identity = (book, event['id'], name)
                            row = {'event_id': event['id'], 'book': book, 'sport': sport, 'favorite': name, 'label': event['away_team'] + ' at ' + event['home_team'], 'odds': odds, 'starts_at': start.isoformat(), 'as_of': observed.isoformat(), 'source': 'The Odds API', 'status': 'Market observation only; no independent win estimate'}
                            if identity not in rows or row['as_of'] > rows[identity]['as_of']:
                                rows[identity] = row
            except (KeyError, ValueError, TypeError, AttributeError):
                continue
    return sorted(rows.values(), key=lambda r: (r['starts_at'], r['book'], r['favorite']))


def download(url):
    with urlopen(Request(url, headers={'User-Agent': 'CarterFlayhartSportsResearch/0.1'}), timeout=60) as response:
        data = response.read(40_000_001)
        if len(data) > 40_000_000: raise ValueError('Feed exceeds size budget')
        return data


def refresh():
    now = datetime.now(timezone.utc).isoformat()
    private = ROOT / 'data/sports'; private.mkdir(parents=True, exist_ok=True)
    report = {'checked_at': now, 'providers': {}}
    for name, url in (('nflverse_player_stats', NFLVERSE), ('nflverse_schedule', SCHEDULE)):
        try:
            content = download(url).decode('utf-8-sig')
            rows = list(csv.DictReader(io.StringIO(content)))
            if not rows or 'season' not in rows[0]: raise ValueError('Invalid CSV')
            current = max(int(r['season']) for r in rows)
            selected = [r for r in rows if int(r['season']) == current]
            atomic_json(private / (name + '.json'), {'source': url, 'checked_at': now, 'season': current, 'rows': selected})
            report['providers'][name] = {'status': 'connected' if current == season_year() else 'historical only; not current-season evidence', 'source': url, 'latest_season': current, 'rows': len(selected)}
        except Exception as error:
            # Do not stringify network exceptions: authenticated URLs can contain keys.
            report['providers'][name] = {'status': 'refresh failed; prior cache preserved', 'error_type': type(error).__name__}
    key = os.environ.get('ODDS_API_KEY')
    if key:
        try:
            # Free plan: never request paid-only Fanatics/Caesars without explicit opt-in.
            books = 'draftkings,fanduel' + (',fanatics,williamhill_us' if os.environ.get('ODDS_PAID_BOOKS') == '1' else '')
            sports = json.loads(download('https://api.the-odds-api.com/v4/sports/?' + urlencode({'apiKey': key})))
            allowed = [s['key'] for s in sports if not s.get('has_outrights') and (s['key'] in ('americanfootball_nfl', 'americanfootball_ncaaf', 'basketball_ncaab') or s['key'].startswith(('tennis_atp_', 'tennis_wta_')))]
            feeds = {}; calls = 0
            budget = min(12, max(0, int(os.environ.get('ODDS_DAILY_CREDITS', '6'))))
            for sport in allowed:
                if calls >= budget: break
                url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds/?' + urlencode({'apiKey': key, 'bookmakers': books, 'markets': 'h2h', 'oddsFormat': 'american'})
                feeds[sport] = json.loads(download(url)); calls += 1
            # Props opt-in: seven markets per event quickly consume a free quota.
            if os.environ.get('ODDS_FETCH_PROPS') == '1':
                for event in feeds.get('americanfootball_nfl', []):
                    if calls + 7 > budget: break
                    url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/events/{event['id']}/odds?" + urlencode({'apiKey': key, 'bookmakers': books, 'markets': MARKETS, 'oddsFormat': 'american'})
                    feeds.setdefault('nfl_props', []).append(json.loads(download(url))); calls += 7
            atomic_json(private / 'odds.json', {'checked_at': now, 'source': 'The Odds API', 'feeds': feeds})
            report['providers']['odds'] = {'status': 'connected; raw odds only, not model forecasts', 'estimated_credits': calls, 'sports_returned': list(feeds), 'paid_books_enabled': os.environ.get('ODDS_PAID_BOOKS') == '1'}
        except Exception as error:
            report['providers']['odds'] = {'status': 'connection failed; no model picks generated', 'error_type': type(error).__name__}
    else:
        report['providers']['odds'] = {'status': 'signup and ODDS_API_KEY required', 'free_tier_missing_books': ['Fanatics', 'Caesars']}
    report['providers']['projections'] = {'status': 'verified pregame context, identity crosswalk and independent favorite projections required'}
    atomic_json(ROOT / 'site/sports/analysis/connections.json', report)
    return report


if __name__ == '__main__':
    print(json.dumps(refresh(), indent=2))
