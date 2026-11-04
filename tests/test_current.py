import copy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from tennis.current import adapt
from tennis.engine import build, normalize
from tennis.server import Application
from tennis.update import ROOT, atomic_json


def row(**kwargs):
    r=dict(match_id='5',date='2026-11-04 10:00:00',tournoi_id='1',tournoi='Example Open',categorie='Main tour',
           genre='atp',surface='dur',tour='12',joueur1='Player One',joueur1_id='1',joueur2='Player Two',joueur2_id='2',vainqueur_id='1',score='6-4 6-3')
    r.update(kwargs);return r


class CurrentSourceTests(unittest.TestCase):
    def test_tours_have_separate_namespaces_with_identical_provider_ids(self):
        a,_=adapt([row()], 'ATP',date(2026,11,4))
        w,_=adapt([row(genre='wta')], 'WTA',date(2026,11,4))
        self.assertNotEqual(a[0]['winner_id'],w[0]['winner_id'])
        self.assertEqual(adapt([row()], 'WTA',date(2026,11,4))[0],[])

    def test_loser_side_scores_are_inverted_without_losing_tiebreak(self):
        r,_=adapt([row(vainqueur_id='2',score='4-6 6-7(3)')],'ATP',date(2026,11,4))
        self.assertEqual(r[0]['score'],'6-4 7-6(3)')
        self.assertTrue(r[0]['winner_id'].endswith(':2'))

    def test_missing_incomplete_and_unplayed_scores_are_not_invented(self):
        for score in ('','6-3 4-2','W/O','0-0','4-6 3-6'):
            self.assertFalse(adapt([row(score=score)],'ATP',date(2026,11,4))[0])

    def test_explicit_retirement_is_retained(self):
        r,_=adapt([row(score='6-3 2-1 RET')],'ATP',date(2026,11,4))
        self.assertTrue(normalize(r)[0][0]['retired'])

    def test_mens_slam_requires_three_won_sets(self):
        self.assertFalse(adapt([row(categorie='Grand Chelem')],'ATP',date(2026,11,4))[0])
        self.assertTrue(adapt([row(categorie='Grand Chelem',score='6-4 6-3 6-1')],'ATP',date(2026,11,4))[0])
        self.assertTrue(adapt([row(genre='wta',categorie='Grand Chelem')],'WTA',date(2026,11,4))[0])

    def test_future_results_are_not_used(self):
        self.assertFalse(adapt([row(date='2026-11-05 12:00:00')],'ATP',date(2026,11,4))[0])

    def test_ambiguous_competitions_are_omitted(self):
        self.assertFalse(adapt([row(categorie='')],'ATP',date(2026,11,4))[0])

    def test_womens_itf_is_not_mislabeled_challenger(self):
        r,_=adapt([row(genre='wta',categorie='Challenger',tournoi='W35 Example')],'WTA',date(2026,11,4))
        self.assertEqual(normalize(r)[0][0]['tier'],'ITF')

    def test_conflicting_provider_ids_fail(self):
        with self.assertRaises(ValueError):
            adapt([row(),row(score='6-0 6-1')],'ATP',date(2026,11,4))

    def test_match_ids_allow_same_pair_in_different_source_matches(self):
        r,_=adapt([row(),row(match_id='6',score='6-0 6-1')],'ATP',date(2026,11,4))
        self.assertEqual(len(normalize(r)[0]),2)

    def test_current_api_cannot_return_a_player_from_the_other_tour(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);rating=json.loads((ROOT/'config.json').read_text())['rating']
            for tour in ('ATP','WTA'):
                r,_=adapt([row(genre=tour.lower(),joueur1=tour+' Player')],tour,date(2026,11,4))
                snapshot,_,_=build(normalize(r)[0],{}, {'rating':rating},date(2026,11,4))
                atomic_json(root/'data'/'current'/tour/'snapshot.json',snapshot)
            app=Application(root)
            for tour in ('ATP','WTA'):
                r=app.api('/api/rankings',{'tour':[tour]})
                self.assertTrue(all(p['id'].startswith('valuebetennis:'+tour+':') for p in r['players']))
            with self.assertRaises(KeyError):
                app.api('/api/players/valuebetennis%3AATP%3A1',{'tour':['WTA']})
            with self.assertRaises(ValueError):
                app.api('/api/rankings',{'tour':['Combined']})
