"""Prepare unambiguous candidates; apply only independently verified ID links."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import re
import unicodedata

from .current import download
from .update import ROOT, atomic_json, read_json


def name_key(value):
    text = unicodedata.normalize('NFKD', value).encode('ascii','ignore').decode().lower()
    return ' '.join(re.findall('[a-z0-9]+', text))


def candidates(rows, published, existing):
    aliases = read_json(ROOT/'tennis/identity-aliases.json',[])
    names = defaultdict(lambda: defaultdict(set))
    labels = {}
    for row in rows:
        tour = row.get('genre','').upper()
        if tour not in ('ATP','WTA'):
            continue
        for side in ('1','2'):
            pid = f'valuebetennis:{tour}:'+row['joueur'+side+'_id']
            label = row['joueur'+side]
            if not label or not row['joueur'+side+'_id']:
                continue
            names[tour][name_key(label)].add(pid); labels[pid] = label
    result = []
    for tour, data in published.get('tours',{}).items():
        if not data.get('source_url') == 'https://tennis.one/ranking':
            continue
        official_names = defaultdict(list)
        for row in data['rows']:
            official_names[name_key(row['name'])].append(row)
        for key, matches in official_names.items():
            ids = names[tour].get(key,set())
            alias = next((a for a in aliases if a['tour']==tour and name_key(a['official_name'])==key),None)
            if not ids and alias:
                ids = names[tour].get(name_key(alias['result_name']),set())
            if len(ids) != 1 or len(matches) != 1:
                continue
            row = matches[0]; pid = next(iter(ids))
            proof = existing.get(pid,{})
            fields_agree = (proof.get('method') in ('name_birth_date_tour','documented_alias_birth_date_country_tour') and proof.get('birth_date') == row.get('birth_date')) or (proof.get('method') == 'name_country_tour' and proof.get('country') == row.get('country'))
            if row['rank'] > 1000 or (proof.get('official_id') == row['id'] and name_key(proof.get('official_name','')) == key and fields_agree):
                continue
            result.append(dict(row, result_id=pid, result_name=labels[pid], tour=tour))
    return sorted(result,key=lambda x:(x['rank'],x['tour']))


def linked_rankings(root, tour, as_of):
    root = Path(root)
    published = read_json(root/'site/sports/tennis/official-rankings.json').get('tours',{}).get(tour,{})
    identities = read_json(root/'site/sports/tennis/identities.json').get('links',{})
    # Old or failed observations must not silently influence today's model.
    observed = published.get('checked_at','')
    if not published.get('source_url') == 'https://tennis.one/ranking' or not observed:
        return {}, {'linked':0,'reason':'No TennisONE observation'}
    age = (as_of-datetime.fromisoformat(observed).date()).days
    if age < 0 or age > 14:
        return {}, {'linked':0,'reason':'TennisONE observation is future-dated or older than 14 days'}
    by_id = {r['id']:r for r in published['rows']}
    links, used = {}, set()
    for pid, proof in identities.items():
        official = by_id.get(proof.get('official_id'))
        if not pid.startswith('valuebetennis:'+tour+':') or not official:
            continue
        if proof.get('method') not in ('name_birth_date_tour','name_country_tour','documented_alias_birth_date_country_tour') or not proof.get('profile_sha256') or not proof.get('profile_url'):
            continue
        if name_key(proof.get('official_name','')) != name_key(official['name']):
            continue
        if proof['method'] == 'name_birth_date_tour' and proof.get('birth_date') != official.get('birth_date'):
            continue
        if proof['method'] == 'name_country_tour' and proof.get('country') != official.get('country'):
            continue
        if proof['method'] == 'documented_alias_birth_date_country_tour':
            aliases = read_json(ROOT/'tennis/identity-aliases.json',[])
            alias = next((a for a in aliases if a['tour']==tour and name_key(a['result_name'])==name_key(proof.get('result_name','')) and name_key(a['official_name'])==name_key(official['name'])),None)
            if not alias or proof.get('alias_source_url') != alias['source_url'] or proof.get('birth_date') != official.get('birth_date') or official.get('birth_date') != alias['birth_date'] or proof.get('country') != official.get('country') or official.get('country') != alias['country']:
                continue
        if official['id'] in used:
            raise ValueError('Multiple results identities mapped to one ranking identity')
        used.add(official['id'])
        links[pid] = dict(official,observed_at=observed,source_url=published['source_url'])
    return links, {'linked':len(links),'observed_at':observed,'source_url':published['source_url'],
                   'refresh_ok':published.get('ok',False),'reason':'Verified namespaced identities; no name-only joins'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true')
    args = parser.parse_args()
    rows,_ = download(ROOT,read_json(ROOT/'current-source.json'),datetime.now(timezone.utc).date(),args.offline)
    published = read_json(ROOT/'site/sports/tennis/official-rankings.json')
    existing = read_json(ROOT/'site/sports/tennis/identities.json').get('links',{})
    todo = candidates(rows,published,existing)
    atomic_json(ROOT/'data/current/identity-candidates.json',todo)
    print(f'{len(todo)} unambiguous identity candidates; none are joined until profile verification')
