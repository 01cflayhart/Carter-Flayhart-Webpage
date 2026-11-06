import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sports.models import category, implied, performance, prop_estimate, select_props, slate_limit
from sports.update import build, validate
from sports.providers import favorite_watchlist

NOW = datetime(2026, 11, 6, 12, tzinfo=timezone.utc)


def candidate(**updates):
    row = {'id': 'test-only-prop', 'event_id': 'test-only-event', 'subject_id': 'test:player:1', 'label': 'Synthetic test fixture, not a published pick', 'source': 'test fixture', 'evidence': 'Synthetic current-season history', 'book': 'draftkings', 'sport': 'NFL', 'as_of': NOW.isoformat(), 'starts_at': (NOW + timedelta(hours=8)).isoformat(), 'identity_verified': True, 'availability_verified': True, 'season': 2026, 'game_dates': ['2026-09-01', '2026-09-08', '2026-09-15', '2026-09-22', '2026-09-29', '2026-10-06', '2026-10-13', '2026-10-20', '2026-10-27', '2026-11-03'], 'values': [7] * 10, 'line': 2.5, 'side': 'Over', 'market': 'receptions', 'odds': 110, 'matchup_multiplier': 1, 'opportunity_multiplier': 1, 'matchup_evidence': 'Synthetic defense adjustment', 'opportunity_evidence': 'Synthetic role adjustment'}
    row.update(updates); return row


class SportsTests(unittest.TestCase):
    def test_market_watchlist_is_fresh_book_isolated_and_not_a_forecast(self):
        market = {'key': 'h2h', 'last_update': NOW.isoformat(), 'outcomes': [{'name': 'Home', 'price': -200}, {'name': 'Away', 'price': 170}]}
        event = {'id': 'source-native:1', 'commence_time': (NOW + timedelta(hours=8)).isoformat(), 'home_team': 'Home', 'away_team': 'Away', 'bookmakers': [{'key': 'draftkings', 'markets': [market]}, {'key': 'williamhill_us', 'markets': [market]}]}
        cache = {'checked_at': NOW.isoformat(), 'feeds': {'americanfootball_nfl': [event], 'baseball_mlb': [event], 'basketball_nba': [event]}}
        rows = favorite_watchlist(cache, NOW)
        self.assertEqual({r['book'] for r in rows}, {'draftkings', 'caesars'})
        self.assertEqual(len(rows), 2)
        self.assertTrue(all('probability' not in r and 'category' not in r for r in rows))
        self.assertEqual(favorite_watchlist(cache, NOW + timedelta(hours=7)), [])
        stale = copy.deepcopy(cache); stale['feeds']['americanfootball_nfl'][0]['bookmakers'][0]['markets'][0]['last_update'] = (NOW - timedelta(hours=7)).isoformat()
        self.assertEqual(favorite_watchlist(stale, NOW), [])
        self.assertEqual(favorite_watchlist(cache, NOW + timedelta(hours=9)), [])
        with tempfile.TemporaryDirectory() as directory:
            build({'market_watchlist': rows}, directory, NOW)
            data = json.loads((Path(directory) / 'upset-alert.json').read_text())
            self.assertEqual(len(data['books']['draftkings']['market_watchlist']), 1)
            self.assertEqual(data['books']['fanduel']['market_watchlist'], [])
            self.assertEqual(data['books']['draftkings']['current']['predictions'], [])
            self.assertEqual(data['books']['draftkings']['performance']['all']['All picks']['n'], 0)

    def test_boundaries(self):
        self.assertEqual([slate_limit(n) for n in range(6)], [0, 3, 5, 5, 10, 10])
        self.assertEqual([category(p) for p in [.95, .9499, .85, .8499, .75, .7499, .60, .5999]], ['Locks', 'No Sweats', 'No Sweats', 'Parlay Pieces', 'Parlay Pieces', 'Better to Avoid', 'Better to Avoid', 'Storm Chasers'])
        self.assertAlmostEqual(implied(-150), .6)
        self.assertAlmostEqual(implied(100), .5)
        for bad in (0, 99, float('nan')):
            with self.assertRaises(ValueError): implied(bad)

    def test_top_caps_price_edge_and_no_forced_fill(self):
        rows = [candidate(id=str(i), subject_id='p:' + str(i)) for i in range(15)]
        for games, count in [(0, 0), (1, 3), (2, 5), (3, 5), (4, 10)]:
            self.assertEqual(len(select_props(rows, games)['top']), count)
        self.assertEqual(select_props([candidate(odds=-151)], 1)['top'], [])
        self.assertEqual(len(select_props([candidate(odds=-150)], 4)['top']), 1)

    def test_safe_dedup_keeps_strongest_threshold(self):
        rows = [candidate(id='two', line=1.5), candidate(id='three', line=2.5)]
        selected = select_props(rows, 1)
        self.assertEqual(len(selected['safe']), 1)
        self.assertEqual(selected['safe'][0]['id'], 'three')
        self.assertEqual(selected['safe'][0]['alternatives'][0]['line'], 1.5)
        p, _ = prop_estimate(rows[0]); self.assertLess(p, 1)

    def test_context_affects_estimate(self):
        row = candidate(line=6.5)
        normal = prop_estimate(row)[0]
        hard = prop_estimate({**row, 'matchup_multiplier': .8})[0]
        self.assertLess(hard, normal)

    def test_fail_closed_input_checks(self):
        validate(candidate(), NOW, 'prop-hunt')
        for changes in ({'sport': 'MLB'}, {'identity_verified': False}, {'availability_verified': False}, {'as_of': (NOW-timedelta(days=1)).isoformat()}, {'starts_at': NOW.isoformat()}, {'season': 2025}, {'values': [1]}, {'values': [float('nan')]*10}, {'game_dates': ['2026-11-06']*10}, {'side': 'Other'}, {'matchup_multiplier': 20}):
            with self.subTest(changes=changes):
                with self.assertRaises((ValueError, KeyError)): validate(candidate(**changes), NOW, 'prop-hunt')

    def test_book_isolation_immutable_archives_and_settlements(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            data = {'prop-hunt': [candidate()], 'nfl_schedule': [{'event_id': 'test-only-event', 'starts_at': candidate()['starts_at']}]}
            build(data, path, NOW)
            archive = path / 'archive/prop-hunt/draftkings/2026-11-06.json'
            first = archive.read_bytes()
            changed = copy.deepcopy(data); changed['prop-hunt'][0]['odds'] = 500
            build(changed, path, NOW + timedelta(minutes=1)); self.assertEqual(first, archive.read_bytes())
            board = json.loads((path / 'prop-hunt.json').read_text())
            self.assertEqual(board['books']['fanduel']['current']['predictions'], [])
            self.assertIsNone(board['books']['draftkings']['performance']['all']['All picks']['win_rate'])
            prediction = json.loads(first)['predictions'][0]
            final = {'prediction_id': prediction['prediction_id'], 'outcome': 'win', 'final_at': (NOW+timedelta(hours=12)).isoformat(), 'source': 'Synthetic final', 'verified_final': True}
            build({'results': [final]}, path, NOW + timedelta(days=1))
            self.assertEqual(archive.read_bytes(), first)
            stats = json.loads((path / 'prop-hunt.json').read_text())['books']['draftkings']['performance']['all']['top']
            self.assertEqual(stats['wins'], 1)
            with self.assertRaises(ValueError): build({'results': [{**final, 'outcome': 'loss'}]}, path, NOW+timedelta(days=1))

    def test_rolling_stats_pending_void_push(self):
        rows = [{'date': '2026-11-06', 'outcome': v, 'probability': .9, 'list': 'top', 'rank': 1, 'sport': 'NFL'} for v in ('win', 'loss', 'pending', 'push', 'void')]
        rows.append({**rows[0], 'date': '2026-10-01'})
        stats = performance(rows, '2026-11-06')
        self.assertEqual(stats['7']['Top rank 1']['win_rate'], .5)
        self.assertEqual(stats['all']['All picks']['n'], 3)
        self.assertEqual(stats['7']['All picks']['pending'], 1)
        self.assertEqual(stats['7']['All picks']['voids'], 1)

    def test_no_data_is_not_perfect_accuracy(self):
        with tempfile.TemporaryDirectory() as directory:
            build(public=directory, now=NOW)
            data = json.loads((Path(directory) / 'upset-alert.json').read_text())
            self.assertEqual(data['books']['draftkings']['history'], [])
            self.assertIsNone(data['books']['draftkings']['performance']['all']['All picks']['win_rate'])


if __name__ == '__main__': unittest.main()
