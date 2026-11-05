"""Dated published singles rankings, isolated from match/model identities.

TennisONE's public ranking-page feed. No login, challenges, proxies, or
private player-history endpoints. Its feed does not provide an edition date.
"""
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path

from .update import ROOT, atomic_json, fetch

WTA_API = 'https://api.wtatennis.com/tennis/players/ranked?metric=SINGLES&type=rankSingles&sort=asc&pageSize=100&page='
ATP_URL = 'https://www.espn.com/tennis/rankings'
WTA_URL = 'https://www.wtatennis.com/rankings/singles'
TENNISONE_URL = 'https://tennis.one/ranking'
TENNISONE_API = 'https://bleachr-web-api-prod.herokuapp.com/api/players/rankings'


def fetch_tennisone(tour, fetcher=fetch):
    gender = {'ATP': 'male', 'WTA': 'female'}[tour]
    rows, pages, total, previous = [], [], None, 0
    tour_label_conflicts = 0
    # The public page uses 100-row pagination. Limit to the first 1,000 ranking
    # positions rather than downloading thousands of unranked player profiles.
    for page in range(1, 101):
        url = f'{TENNISONE_API}?gender={gender}&sort=singles_rank=ASC&currentPage={page}&take=100'
        raw = fetcher(url); pages.append(raw)
        payload = json.loads(raw)
        if payload.get('error'):
            raise ValueError('TennisONE reported an error')
        data = payload['data']; pagination = data['pagination']; batch = data['players']
        if pagination['currentPage'] != page or pagination['perPage'] != 100:
            raise ValueError('Unexpected TennisONE pagination')
        if total is not None and total != pagination['totalItems']:
            raise ValueError('TennisONE player count changed during pagination')
        total = pagination['totalItems']
        finished = False
        for player in batch:
            rank = player.get('singles_rank')
            if rank is None or (type(rank) is int and rank > 1000):
                finished = True
                continue
            if finished or type(rank) is not int or rank < previous or rank < 1:
                raise ValueError('Unordered TennisONE ranking page')
            if player['gender'] != gender:
                raise ValueError('Wrong tour in TennisONE response')
            if (player.get('tour') or tour).upper() != tour:
                # Some female profiles have an erroneous free-text "ATP" label.
                # The requested ranking list AND explicit gender must agree.
                tour_label_conflicts += 1
            previous = rank
            details = player.get('details') or {}
            dob = (details.get('birth_date') or '')[:10]
            if dob:
                date.fromisoformat(dob)
            rows.append(dict(id=f'tennisone:{tour}:'+player['id'],
                name=(player['first_name']+' '+player['last_name']).strip(),
                rank=rank, points=player['singles_points'], country=player.get('country', ''),
                birth_date=dob or None, gender=gender, url=TENNISONE_URL))
        if finished or page == pagination['totalPages']:
            if not finished and len(batch) != total-(page-1)*100:
                raise ValueError('Truncated final TennisONE page')
            break
        if len(batch) != 100:
            raise ValueError('Truncated TennisONE page')
    else:
        raise ValueError('TennisONE pagination did not finish')
    if len(rows) < 100 or rows[0]['rank'] != 1 or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Empty, truncated, or duplicate TennisONE ranking identities')
    for row in rows:
        if not row['name'] or type(row['points']) is not int or row['points'] < 0:
            raise ValueError('Invalid TennisONE ranking fields')
    inconsistencies = sum(a['points'] < b['points'] for a,b in zip(rows,rows[1:]))
    return dict(tour=tour, edition=None, source_name=f'{tour} rankings via TennisONE',
        source_url=TENNISONE_URL, coverage=f'{len(rows)} players in the first 1,000 singles-ranking positions; provider does not supply an edition date',
        sha256=hashlib.sha256(b''.join(pages)).hexdigest(), rows=rows,
        point_order_inconsistencies=inconsistencies,
        warnings=([f'{inconsistencies} adjacent points totals disagree with rank order in the source; source ranks are preserved, not recalculated.'] if inconsistencies else [])+
                 ([f'{tour_label_conflicts} profile tour labels conflict with the requested list; explicit player gender matches the list.'] if tour_label_conflicts else []))


def validate(rows, edition, minimum=100):
    day = date.fromisoformat(edition)
    if day > datetime.now(timezone.utc).date():
        raise ValueError('Future ranking edition')
    if len(rows) < minimum or min(r['rank'] for r in rows) != 1:
        raise ValueError('Empty or truncated ranking edition')
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate ranking identity')
    for r in rows:
        if not r['name'].strip() or type(r['rank']) is not int or r['rank'] < 1 or type(r['points']) is not int or r['points'] < 0:
            raise ValueError('Invalid ranking fields')
    rows.sort(key=lambda r: (r['rank'], r['id']))
    if any(a['points'] < b['points'] for a, b in zip(rows, rows[1:])):
        raise ValueError('Ranking points are not ordered')
    # Tied positions are allowed, but unexpectedly skipped rows are not.
    if max(r['rank'] for r in rows) > len(rows):
        raise ValueError('Ranking positions imply missing rows')
    return rows


def parse_atp(raw):
    text = raw.decode('utf-8')
    marker = "window['__espnfitt__']="
    # JSON decoder only: never execute remote JavaScript.
    payload = json.JSONDecoder().raw_decode(text.split(marker, 1)[1])[0]['page']['content']['rankings']
    if payload['selectedView'] != 'men':
        raise ValueError('Wrong tour in ESPN response')
    edition = datetime.strptime(payload['updatedNote'].removeprefix('Last Updated: ').strip(), '%B %d, %Y').date().isoformat()
    rows = []
    for item in payload['parsedRanks']:
        rank = item['rank']; player = rank['athlete']
        rows.append(dict(id='espn:ATP:' + player['id'], name=player['displayName'],
                         rank=rank['current'], points=rank['points'], country=player.get('citizenshipCountry', ''),
                         url=item['athlete']['link']))
    return dict(tour='ATP', edition=edition, source_name='ATP rankings via ESPN', source_url=ATP_URL,
                coverage=f'Top {len(rows)} supplied by ESPN; not the full ATP list',
                rows=validate(rows, edition, minimum=150))


def fetch_wta(fetcher=fetch):
    records, raw_pages = [], []
    edition = None
    for page in range(30):
        raw = fetcher(WTA_API + str(page)); raw_pages.append(raw)
        batch = json.loads(raw)
        if not isinstance(batch, list):
            raise ValueError('Invalid WTA response')
        for item in batch:
            day = item['rankedAt'][:10]
            if edition and day != edition:
                raise ValueError('WTA edition changed during pagination')
            edition = day
            p = item['player']
            records.append(dict(id='wta:WTA:' + str(p['id']), name=p['fullName'], rank=item['ranking'],
                                points=item['points'], country=p.get('countryCode', ''),
                                url='https://www.wtatennis.com/players/' + str(p['id'])))
        if len(batch) < 100:
            break
    else:
        raise ValueError('WTA pagination did not finish')
    return dict(tour='WTA', edition=edition, source_name='WTA official rankings', source_url=WTA_URL,
                coverage=f'{len(records)} ranked singles players supplied by WTA',
                sha256=hashlib.sha256(b''.join(raw_pages)).hexdigest(), rows=validate(records, edition))


def update(root=ROOT, fetcher=fetch):
    path = Path(root) / 'site/sports/tennis/official-rankings.json'
    result = json.loads(path.read_text()) if path.exists() else {'tours': {}}
    for tour in ('ATP', 'WTA'):
        checked = datetime.now(timezone.utc).isoformat()
        try:
            item = fetch_tennisone(tour, fetcher)
            old = result['tours'].get(tour, {})
            if old.get('edition') and item.get('edition') and old['edition'] > item['edition']:
                raise ValueError('Source attempted to roll back the edition')
            item.update(checked_at=checked, last_attempt=checked, ok=True)
            result['tours'][tour] = item
            print(f'{tour}: {len(item["rows"])} TennisONE ranks; observed {checked}, edition not supplied', flush=True)
        except Exception as error:
            old = result['tours'].get(tour, {'tour': tour, 'rows': []})
            old.update(last_attempt=checked, ok=False, error='Refresh failed; showing the last validated edition, if available.')
            result['tours'][tour] = old
            reason = str(error).replace('\n', ' ')[:180]
            print(f'::warning::{tour} ranking refresh failed ({type(error).__name__}: {reason}); last valid snapshot preserved', flush=True)
    atomic_json(path, result)
    return result


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    update()
