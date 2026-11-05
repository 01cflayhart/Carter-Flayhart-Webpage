from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import unittest

from tennis.engine import (State, build, category, expected, normalize, parse_date,
                           replay, seed, shift_months, significant, statistics, tier)

CONFIG = json.loads((Path(__file__).resolve().parents[1] / "config.json").read_text())


def match(day="20260105", w="1", l="2", wr=10, lr=100, surface="Outdoor hard", score="6-3 6-4", event=None, **kwargs):
    return dict(tourney_id=event or day + "-event", tourney_name="Test Open", tourney_date=day,
                winner_id=w, loser_id=l, winner_name="Player " + w, loser_name="Player " + l,
                winner_rank=str(wr) if wr else "", loser_rank=str(lr) if lr else "", winner_age="20.0", loser_age="36.0",
                winner_ioc="USA", loser_ioc="GBR", tourney_level="A", surface=surface,
                score=score, round="F", **kwargs)


class EngineTests(unittest.TestCase):
    def test_date_arithmetic_calendar_months_and_leap_year(self):
        self.assertEqual(shift_months(date(2024, 5, 31), -3), date(2024, 2, 29))
        self.assertEqual(shift_months(date(2024, 2, 29), -12), date(2023, 2, 28))
        self.assertEqual(parse_date("20260105"), date(2026, 1, 5))

    def test_categories_boundaries_unknown(self):
        for opponent in (75, 100, 125):
            self.assertEqual(category(100, opponent), "similar")
        self.assertEqual(category(100, 74), "better")
        self.assertEqual(category(100, 126), "worse")
        self.assertEqual(category(None, 1), "unknown")
        self.assertEqual(category(1, None), "unknown")

    def test_significance(self):
        self.assertTrue(significant(100, 1, True))
        self.assertFalse(significant(100, 1, False))
        self.assertTrue(significant(1, 1000, False))
        self.assertFalse(significant(1, 1000, True))
        self.assertTrue(significant(100, 125, False))
        self.assertFalse(significant(100, None, True))

    def test_expected_opposition_and_upsets(self):
        self.assertAlmostEqual(expected(1500, 1500), .5)
        self.assertLess(expected(1200, 1800), .1)
        upset_gain = 40 * (1 - expected(1200, 1800))
        routine_gain = 40 * (1 - expected(1800, 1200))
        self.assertGreater(upset_gain, routine_gain * 10)
        self.assertGreater(abs(40 * (0 - expected(1800, 1200))), abs(40 * (0 - expected(1200, 1800))))

    def test_seed_never_uses_points(self):
        rows, _ = normalize([match()])
        changed = deepcopy(rows)
        changed[0]["winner_rank_points"] = "99999999"
        a = replay(rows, CONFIG, date(2026, 1, 6))[0]
        b = replay(changed, CONFIG, date(2026, 1, 6))[0]
        self.assertEqual(a["1"].strength(), b["1"].strength())
        self.assertEqual(seed(None), 1250)

    def test_duplicates_and_conflicts(self):
        row = match()
        matches, audit = normalize([row, row])
        self.assertEqual(len(matches), 1)
        self.assertEqual(audit["duplicates"], 1)
        reverse = match(w="2", l="1")
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
            normalize([row, reverse])

    def test_nonplayed_and_retirements(self):
        rows = [match(score=s, event=s) for s in ("W/O", "BYE", "DEF", "ABN", "", "6-3 2-1 RET")]
        matches, audit = normalize(rows)
        self.assertEqual(len(matches), 1)
        self.assertTrue(matches[0]["retired"])
        self.assertEqual(audit["not_played_or_unusable"], 5)
        normal, _ = normalize([match()])
        a = replay(matches, CONFIG, date(2026, 1, 5))[2]["1"][0]["delta"]
        b = replay(normal, CONFIG, date(2026, 1, 5))[2]["1"][0]["delta"]
        self.assertAlmostEqual(a * 2, b, places=2)

    def test_tiers(self):
        self.assertEqual(tier({"tourney_level":"F"}), "Tour")
        self.assertEqual(tier({"tourney_level":"C", "round":"QF"}), "Challenger")
        self.assertEqual(tier({"tourney_level":"A", "round":"Q1"}), "Qualifying")
        self.assertEqual(tier({"tourney_level":"25"}), "ITF")
        self.assertEqual(tier({"tourney_level":"??"}), "Unknown")

    def test_same_date_freeze_and_determinism(self):
        rows = [match(event="a"), match(w="2", l="3", event="b")]
        matches, _ = normalize(rows)
        a = replay(matches, CONFIG, date(2026, 1, 5))
        b = replay(normalize(rows[::-1])[0], CONFIG, date(2026, 1, 5))
        self.assertEqual(a[2], b[2])
        self.assertIsNone(a[2]["1"][0]["own_power"])
        self.assertIsNone(a[2]["2"][1]["own_power"])

    def test_future_results_do_not_rewrite_past(self):
        first = match()
        second = match(day="20260112", w="2", l="1", wr=100, lr=10)
        later = match(day="20260119", w="3", l="1", wr=1, lr=1000)
        small = replay(normalize([first, second])[0], CONFIG, date(2026,1,12))
        big = replay(normalize([first, second, later])[0], CONFIG, date(2026,1,12))
        self.assertEqual(small[2], big[2])
        complete = replay(normalize([first, second, later])[0], CONFIG, date(2026,1,19))
        self.assertEqual(small[2]["1"][1], complete[2]["1"][1])

    def test_historical_rank_modes_actually_differ(self):
        matches, _ = normalize([match(wr=1, lr=1000), match(day="20260112", w="2", l="1", wr=1000, lr=1)])
        publication, _, _ = build(matches, {}, CONFIG, date(2026,1,12))
        p = next(p for p in publication["players"] if p["id"]=="2")
        self.assertEqual(p["stats"]["atp"]["year"]["better"], [1,1])
        self.assertEqual(p["stats"]["power"]["year"]["similar"], [1,0])
        self.assertEqual(p["stats"]["power"]["year"]["unknown"], [0,1])

    def test_official_edition_not_future_or_per_player_latest(self):
        rows, _ = normalize([match()])
        rankings = {date(2026,1,1):{"1":{"rank":5,"points":500}}, date(2026,1,12):{"2":{"rank":1,"points":9000}}}
        snap, _, _ = build(rows, rankings, CONFIG, date(2026,1,5))
        p = {p["id"]:p for p in snap["players"]}
        self.assertEqual(p["1"]["atp_rank"], 5)
        self.assertIsNone(p["2"]["atp_rank"])

    def test_strength_decay_expiry_sparse_surface(self):
        rc = CONFIG["rating"]
        st = State(1250, date(2025,1,1), rc)
        st.add(date(2025,1,1), "Hard", 100, 100)
        st.last_strength=st.strength()
        st.advance(date(2025,5,1), rc)
        self.assertAlmostEqual(st.strength(),1250 + 50 * rc["form_weight"],places=4)
        self.assertAlmostEqual(st.strength("Grass",rc),st.strength())
        st.advance(date(2026,1,1),rc)
        self.assertEqual(st.total,0)
        self.assertAlmostEqual(st.strength(),1250)

    def test_inactivity_cannot_boost_weak_player(self):
        rc=CONFIG["rating"]
        st=State(1250,date(2026,1,1),rc)
        st.add(date(2026,1,1),"Hard",-100,-100)
        st.last_strength=st.strength()
        before=st.score(config=rc)
        st.advance(date(2026,4,1),rc)
        self.assertLessEqual(st.score(config=rc),before)
        self.assertGreater(st.strength(),st.score(config=rc))

    def test_age_neutral(self):
        rows,_=normalize([match()])
        older=deepcopy(rows)
        older[0]["winner_age"]="45"
        self.assertEqual(replay(rows,CONFIG,date(2026,1,5))[0]["1"].strength(),replay(older,CONFIG,date(2026,1,5))[0]["1"].strength())

    def test_records_reconcile_calendar_windows_and_surface(self):
        rows,_=normalize([match(day="20260228",surface="Clay"), match(day="20260301",surface="Grass"),match(day="20260531",surface="Hard",score="6-0 RET")])
        pub,_,_=build(rows,{},CONFIG,date(2026,5,31))
        p=next(p for p in pub["players"] if p["id"]=="1")
        self.assertEqual(p["stats"]["atp"]["recent"]["overall"],[2,0])
        self.assertEqual(statistics(p["history"],date(2026,2,28),"atp",True)["overall"],[1,0])
        stats=p["stats"]["atp"]["year"]
        self.assertEqual(sum(sum(stats[k]) for k in ("similar","better","worse","unknown")),sum(stats["overall"]))
        self.assertEqual(sum(sum(stats[k]) for k in ("Outdoor hard","Indoor hard","Clay","Grass","Unknown")),sum(stats["overall"]))

    def test_carpet_excluded_and_unspecified_hard_not_inferred(self):
        rows,audit=normalize([match(surface='Carpet'),match(surface='Hard',event='unspecified')])
        self.assertEqual(audit['carpet_excluded'],1)
        self.assertEqual(rows[0]['surface'],'Unknown')
        self.assertEqual(normalize([match(surface='Hard',indoor=True)])[0][0]['surface'],'Indoor hard')
        self.assertEqual(normalize([match(surface='Hard',indoor=False)])[0][0]['surface'],'Outdoor hard')

    def test_indoor_and_outdoor_hard_have_independent_evidence(self):
        rows,_=normalize([match(surface='Indoor hard'),match(day='20260112',surface='Outdoor hard')])
        publication,_,_=build(rows,{},CONFIG,date(2026,1,12))
        p=publication['players'][0]
        self.assertEqual(set(p['surfaces']),{'Indoor hard','Outdoor hard','Clay','Grass'})
        for surface in ('Indoor hard','Outdoor hard'):
            self.assertEqual(p['surfaces'][surface]['matches'],1)
            self.assertEqual(p['stats']['power']['year'][surface],[1,0])

    def test_event_weights_scale_both_anchor_and_form_but_not_wl(self):
        main=None
        for level,round_name,weight in [('A','F',1),('A','Q1',.4),('C','F',.3),('C','Q1',.15),('15','F',.08),('15','Q1',.04)]:
            row=match();row.update(tourney_level=level,round=round_name)
            states,_,history,*_=replay(normalize([row])[0],CONFIG,date(2026,1,5))
            changes=(states['1'].anchor-seed(10),states['1'].sums['Overall'])
            if main is None:main=changes
            for actual,baseline in zip(changes,main):self.assertAlmostEqual(actual,baseline*weight)
            self.assertEqual(statistics(history['1'],date(2025,1,5),'power')['overall'],[1,0])
            self.assertAlmostEqual(history['1'][0]['event_weight'],weight)

    def test_current_rank_prior_changes_current_order_not_historical_evidence(self):
        rows,_=normalize([match(wr=None,lr=None)])
        baseline,snapshots,predictions=build(rows,{},CONFIG,date(2026,1,5))
        ranks={'1':{'rank':1000,'points':1,'observed_at':'2026-01-05T00:00:00Z'},
               '2':{'rank':1,'points':10000,'observed_at':'2026-01-05T00:00:00Z'}}
        changed,after_snapshots,after_predictions=build(rows,{},CONFIG,date(2026,1,5),current_rankings=ranks)
        self.assertEqual(baseline['players'][0]['id'],'1')
        self.assertEqual(changed['players'][0]['id'],'2')
        self.assertEqual(snapshots,after_snapshots);self.assertEqual(predictions,after_predictions)
        original={p['id']:p for p in baseline['players']}
        for p in changed['players']:
            self.assertEqual(p['history'],original[p['id']]['history'])
            self.assertEqual(p['stats'],original[p['id']]['stats'])
            self.assertIsNone(p['movement'])
            self.assertLessEqual(abs(p['official_adjustment']),200)
            for surface in p['surfaces']:
                self.assertAlmostEqual(p['surfaces'][surface]['rating']-original[p['id']]['surfaces'][surface]['rating'],p['official_adjustment'],places=1)
        ranks['1']['observed_at']='2026-01-06T00:00:00Z';ranks['2']['observed_at']='2026-01-06T00:00:00Z'
        future=build(rows,{},CONFIG,date(2026,1,5),current_rankings=ranks)[0]
        self.assertEqual(future['players'],baseline['players'])

    def test_sourced_health_and_missing_photo_validation(self):
        rows,_=normalize([match()])
        with self.assertRaisesRegex(ValueError,"Unsourced"):
            build(rows,{},CONFIG,date(2026,1,5),health={"1":{"status":"injured"}})
        with self.assertRaisesRegex(ValueError,"Photo"):
            build(rows,{},CONFIG,date(2026,1,5),photos={"1":{"url":"http://example.com/a.jpg"}})

    def test_team_policy(self):
        row=match();row["tourney_level"]="D"
        matches,_=normalize([row])
        cfg=deepcopy(CONFIG);cfg["rating"]["include_team"]=False
        self.assertEqual(build(matches,{},cfg,date(2026,1,5))[0]["players"],[])

    def test_top50_uses_the_historical_opponent_not_current_display_rank(self):
        rows,_=normalize([match(lr=50),match(day='20260112',lr=51)])
        ranks={date(2026,1,12):{'2':{'rank':1,'points':9999}}}
        pub,_,_=build(rows,ranks,CONFIG,date(2026,1,12))
        p=next(p for p in pub['players'] if p['id']=='1')
        self.assertEqual(p['stats']['atp']['year']['top50'],[1,0])

    def test_expired_health_and_future_reports_are_not_shown(self):
        rows,_=normalize([match()])
        report={'status':'Reported return','reported_at':'2025-12-01','review_after':'2026-01-01',
                'confidence':'Source-reported','source_url':'https://example.org/return'}
        pub,_,_=build(rows,{},CONFIG,date(2026,1,5),health={'1':report})
        self.assertIsNone(next(p for p in pub['players'] if p['id']=='1')['health'])

    def test_recent_evidence_matters_more_and_rank_ties_are_stable(self):
        rc=CONFIG['rating'];old=State(1250,date(2026,1,1),rc);new=State(1250,date(2026,4,1),rc)
        old.add(date(2026,1,1),'Hard',100,100);old.last_strength=old.strength()
        new.add(date(2026,4,1),'Hard',100,100);new.last_strength=new.strength()
        old.advance(date(2026,4,1),rc)
        self.assertLess(old.strength(),new.strength())
        matches,_=normalize([match(),match(day='20260112',w='2',l='1',wr=100,lr=10)])
        a=build(matches,{},CONFIG,date(2026,1,12))[0]
        b=build(matches,{},CONFIG,date(2026,1,12))[0]
        self.assertEqual(a['players'],b['players'])


if __name__=="__main__":
    unittest.main()
