import copy
from contextlib import redirect_stdout
from datetime import date, timedelta
import json
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from tennis.official import ATP_URL, WTA_API, fetch_wta, parse_atp, update, validate

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
            before = update(temp, fetcher)
            def broken_atp(url):
                if url == ATP_URL: raise OSError('Unavailable')
                return fetcher(url)
            after = update(temp, broken_atp)
            self.assertFalse(after['tours']['ATP']['ok'])
            self.assertTrue(after['tours']['WTA']['ok'])
            self.assertEqual(before['tours']['ATP']['rows'], after['tours']['ATP']['rows'])
            self.assertEqual(before['tours']['ATP']['checked_at'], after['tours']['ATP']['checked_at'])
            self.assertTrue((Path(temp)/'site/sports/tennis/official-rankings.json').exists())


if __name__ == '__main__': unittest.main()
