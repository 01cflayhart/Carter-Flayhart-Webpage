import copy
from contextlib import redirect_stdout
from datetime import date, timedelta
import json
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from urllib.parse import parse_qs, urlparse

from tennis.official import ATP_URL, WTA_API, fetch_wta, fetch_tennisone, parse_atp, update, validate

EDITION = '2026-01-05'


def atp_raw():
    rows = [dict(rank=dict(current=i, points=2000-i, athlete=dict(id=str(i), displayName='Player '+str(i))), athlete=dict(link='https://www.espn.com/tennis/player/_/id/'+str(i))) for i in range(1, 151)]
    data = dict(selectedView='men', updatedNote='Last Updated: January 05, 2026', parsedRanks=rows)
    return ("<script>window['__espnfitt__']=" + json.dumps(dict(page=dict(content=dict(rankings=data)))) + ';</script>').encode()


def wta_row(i, edition=EDITION):
    return dict(player=dict(id=i, fullName='Player '+str(i), countryCode='USA'), ranking=i, points=2000-i, rankedAt=edition+'T00:00:00Z')


def fetcher(url):
    if url == ATP_URL:
        return atp_raw()
    page = int(url.removeprefix(WTA_API))
    return json.dumps([wta_row(i) for i in range(1, 101)] if page == 0 else [wta_row(101)] if page == 1 else []).encode()


def tennisone_fetcher(url, total=150):
    query = parse_qs(urlparse(url).query)
    gender = query['gender'][0]; page = int(query['currentPage'][0])
    rows = [dict(id=str(i),first_name='Player',last_name=str(i),singles_rank=i,
                 singles_points=5000-i,gender=gender,country='US',details={},tour='ATP' if gender=='male' else 'WTA')
            for i in range((page-1)*100+1,min(page*100,total)+1)]
    return json.dumps(dict(data=dict(players=rows,pagination=dict(currentPage=page,perPage=100,totalItems=total,totalPages=(total+99)//100)),error=None)).encode()


class OfficialRankingTests(unittest.TestCase):
    def test_atp_dated_and_namespaced(self):
        item = parse_atp(atp_raw())
        self.assertEqual(item['edition'], EDITION)
        self.assertEqual(len(item['rows']), 150)
        self.assertEqual(item['rows'][0]['id'], 'espn:ATP:1')
        self.assertIn('not the full ATP list', item['coverage'])

    def test_wta_pagination(self):
        item = fetch_wta(fetcher)
        self.assertEqual(len(item['rows']), 101)
        self.assertEqual(item['rows'][0]['id'], 'wta:WTA:1')
        self.assertEqual(item['edition'], EDITION)

    def test_duplicate_or_ignored_pages_fail(self):
        with self.assertRaises(ValueError):
            fetch_wta(lambda url: json.dumps([wta_row(i) for i in range(1, 101)] if url.endswith('=0') else [wta_row(1)]).encode())

    def test_changed_edition_fails(self):
        with self.assertRaises(ValueError):
            fetch_wta(lambda url: json.dumps([wta_row(i) for i in range(1, 101)] if url.endswith('=0') else [wta_row(101, '2026-01-12')]).encode())

    def test_empty_truncated_future_and_invalid_points_fail(self):
        rows = parse_atp(atp_raw())['rows']
        for changed, day in [(rows[:20], EDITION), (rows, (date.today()+timedelta(days=1)).isoformat()), ([], EDITION)]:
            with self.assertRaises(ValueError): validate(changed, day)
        broken = copy.deepcopy(rows); broken[0]['points'] = -1
        with self.assertRaises(ValueError): validate(broken, EDITION)
        broken = copy.deepcopy(rows); broken[0]['points'] = 0
        with self.assertRaises(ValueError): validate(broken, EDITION)

    def test_independent_failure_preserves_last_valid_edition(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(StringIO()):
            before = update(temp, tennisone_fetcher)
            def broken_atp(url):
                if 'gender=male' in url: raise OSError('Unavailable')
                return tennisone_fetcher(url)
            after = update(temp, broken_atp)
            self.assertFalse(after['tours']['ATP']['ok'])
            self.assertTrue(after['tours']['WTA']['ok'])
            self.assertEqual(before['tours']['ATP']['rows'], after['tours']['ATP']['rows'])
            self.assertEqual(before['tours']['ATP']['checked_at'], after['tours']['ATP']['checked_at'])
            self.assertTrue((Path(temp)/'site/sports/tennis/official-rankings.json').exists())

    def test_tennisone_paginated_tour_isolation_and_no_invented_edition(self):
        for tour in ('ATP','WTA'):
            result=fetch_tennisone(tour,tennisone_fetcher)
            self.assertEqual(len(result['rows']),150)
            self.assertIsNone(result['edition'])
            self.assertTrue(all(r['id'].startswith('tennisone:'+tour+':') for r in result['rows']))

    def test_tennisone_rejects_wrong_gender_duplicate_and_truncated_pages(self):
        for kind in ('gender','duplicate','truncated','points'):
            def broken(url):
                data=json.loads(tennisone_fetcher(url)); rows=data['data']['players']
                if kind=='gender':rows[0]['gender']='female'
                if kind=='duplicate':rows[1]['id']=rows[0]['id']
                if kind=='truncated':rows.pop()
                if kind=='points':rows[0]['singles_points']=-1
                return json.dumps(data).encode()
            with self.subTest(kind=kind),self.assertRaises(ValueError):fetch_tennisone('ATP',broken)

    def test_tennisone_stops_after_first_thousand_positions(self):
        result=fetch_tennisone('ATP',lambda url:tennisone_fetcher(url,1100))
        self.assertEqual(len(result['rows']),1000)

    def test_tennisone_source_inconsistencies_are_visible_not_silently_repaired(self):
        def inconsistent(url):
            data=json.loads(tennisone_fetcher(url));data['data']['players'][0]['singles_points']=0
            data['data']['players'][0]['tour']='WTA'
            return json.dumps(data).encode()
        result=fetch_tennisone('ATP',inconsistent)
        self.assertEqual(result['rows'][0]['rank'],1)
        self.assertEqual(result['rows'][0]['points'],0)
        self.assertTrue(result['warnings'])


if __name__ == '__main__': unittest.main()
