from datetime import date
from pathlib import Path
import tempfile
import unittest

from tennis.identities import candidates, linked_rankings, name_key
from tennis.update import ROOT, atomic_json, read_json


class IdentityTests(unittest.TestCase):
    def fixtures(self, root, observed='2026-01-05T00:00:00Z'):
        row={'id':'tennisone:ATP:abc','name':'Player One','rank':1,'points':10000,'country':'US','birth_date':'2000-01-01'}
        atomic_json(root/'site/sports/tennis/official-rankings.json',{'tours':{'ATP':{'rows':[row],
            'source_url':'https://tennis.one/ranking','checked_at':observed,'ok':True}}})
        proof={'official_id':row['id'],'official_name':row['name'],'method':'name_birth_date_tour',
            'birth_date':'2000-01-01','profile_sha256':'checked-profile-hash',
            'profile_url':'https://www.valuebetennis.com/players/player-one-1.htm','country':'US'}
        return row,proof

    def test_exact_normalized_full_names_not_fuzzy_surnames(self):
        self.assertEqual(name_key('Félix Auger-Aliassime'),name_key('Felix Auger Aliassime'))
        self.assertNotEqual(name_key('Player One'),name_key('One'))

    def test_name_candidates_do_not_resolve_ambiguous_provider_ids(self):
        rows=[{'genre':'atp','joueur1':'Player One','joueur1_id':'1','joueur2':'Other','joueur2_id':'2'}]
        published={'tours':{'ATP':{'source_url':'https://tennis.one/ranking','rows':[{'id':'t1','name':'Player One','rank':1}]}}}
        self.assertEqual(len(candidates(rows,published,{})),1)
        rows.append(dict(rows[0],joueur1_id='3'))
        self.assertEqual(candidates(rows,published,{}),[])

    def test_only_verified_birth_date_or_country_proofs_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_,proof=self.fixtures(root)
            path=root/'site/sports/tennis/identities.json'
            for method,expected in [('name_only',0),('name_birth_date_tour',1),('name_country_tour',1)]:
                proof['method']=method;atomic_json(path,{'links':{'valuebetennis:ATP:1':proof}})
                linked,_=linked_rankings(root,'ATP',date(2026,1,5));self.assertEqual(len(linked),expected)
            proof['method']='name_birth_date_tour';proof['birth_date']='1999-01-01'
            atomic_json(path,{'links':{'valuebetennis:ATP:1':proof}})
            self.assertEqual(linked_rankings(root,'ATP',date(2026,1,5))[0],{})

    def test_stale_future_and_cross_tour_observations_do_not_enter_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for observed in ['2025-12-01T00:00:00Z','2026-01-06T00:00:00Z']:
                _,proof=self.fixtures(root,observed)
                atomic_json(root/'site/sports/tennis/identities.json',{'links':{'valuebetennis:ATP:1':proof}})
                self.assertEqual(linked_rankings(root,'ATP',date(2026,1,5))[0],{})
            _,proof=self.fixtures(root)
            atomic_json(root/'site/sports/tennis/identities.json',{'links':{'valuebetennis:WTA:1':proof}})
            self.assertEqual(linked_rankings(root,'ATP',date(2026,1,5))[0],{})

    def test_duplicate_identity_crosswalk_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_,proof=self.fixtures(root)
            atomic_json(root/'site/sports/tennis/identities.json',{'links':{'valuebetennis:ATP:1':proof,'valuebetennis:ATP:2':proof}})
            with self.assertRaises(ValueError):linked_rankings(root,'ATP',date(2026,1,5))

    def test_documented_alias_requires_birth_date_country_and_citation(self):
        alias=next(a for a in read_json(ROOT/'tennis/identity-aliases.json') if a['result_name']=='Cori Gauff')
        rows=[{'genre':'wta','joueur1':'Cori Gauff','joueur1_id':'1','joueur2':'Other','joueur2_id':'2'}]
        published={'tours':{'WTA':{'source_url':'https://tennis.one/ranking',
            'checked_at':'2026-01-05T00:00:00Z','rows':[{'id':'tennisone:WTA:gauff','name':'Coco Gauff',
                'rank':4,'points':6000,'birth_date':alias['birth_date'],'country':'US'}]}}}
        proposed=candidates(rows,published,{})
        self.assertEqual(proposed[0]['result_name'],'Cori Gauff')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            atomic_json(root/'site/sports/tennis/official-rankings.json',published)
            proof={'official_id':'tennisone:WTA:gauff','official_name':'Coco Gauff','result_name':'Cori Gauff',
                'method':'documented_alias_birth_date_country_tour','profile_sha256':'checked',
                'profile_url':'https://www.valuebetennis.com/players/cori-gauff-1.htm',
                'birth_date':alias['birth_date'],'country':'US'}
            path=root/'site/sports/tennis/identities.json'
            atomic_json(path,{'links':{'valuebetennis:WTA:1':proof}})
            self.assertFalse(linked_rankings(root,'WTA',date(2026,1,5))[0])
            proof['alias_source_url']=alias['source_url']
            atomic_json(path,{'links':{'valuebetennis:WTA:1':proof}})
            self.assertEqual(len(linked_rankings(root,'WTA',date(2026,1,5))[0]),1)
            proof['country']='GB'
            atomic_json(path,{'links':{'valuebetennis:WTA:1':proof}})
            self.assertFalse(linked_rankings(root,'WTA',date(2026,1,5))[0])
