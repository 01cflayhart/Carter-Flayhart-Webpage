"""Dated published singles rankings, isolated from match/model identities.

WTA: the unauthenticated feed used by its public rankings page.
ATP: ESPN's public page (ATP itself blocks automation here). No challenges,
proxies, private endpoints, or name-only joins to result-provider IDs.
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
            if tour == 'ATP':
                raw = fetcher(ATP_URL); item = parse_atp(raw)
                item['sha256'] = hashlib.sha256(raw).hexdigest()
            else:
                item = fetch_wta(fetcher)
            old = result['tours'].get(tour, {})
            if old.get('edition', '') > item['edition']:
                raise ValueError('Source attempted to roll back the edition')
            item.update(checked_at=checked, last_attempt=checked, ok=True)
            result['tours'][tour] = item
            print(f'{tour}: {len(item["rows"])} published ranks, edition {item["edition"]}', flush=True)
        except Exception:
            old = result['tours'].get(tour, {'tour': tour, 'rows': []})
            old.update(last_attempt=checked, ok=False, error='Refresh failed; showing the last validated edition, if available.')
            result['tours'][tour] = old
            print(f'::warning::{tour} ranking refresh failed; last valid edition preserved', flush=True)
    atomic_json(path, result)
    return result


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    update()
