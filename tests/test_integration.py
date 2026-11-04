from copy import deepcopy
import csv
from datetime import date
import hashlib
from http.server import ThreadingHTTPServer
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

from tennis.server import Application, handler_for
from tennis.update import atomic_json, update
from tests.test_engine import CONFIG, match


def fixture(root):
    config=deepcopy(CONFIG)
    config["source"].update(years=[2026],families={"Tour":"matches.csv"},rankings=["rankings.csv"],documents=[])
    config["source"]["min_ranking_rows"]=1
    (root/"config.json").write_text(json.dumps(config))
    data=root/"data"; (data/"raw").mkdir(parents=True)
    for name,rows in (("matches.csv",[match(),match(day="20260112",w="2",l="1",wr=100,lr=10)]),
                      ("rankings.csv",[{"ranking_date":"20260105","rank":"1","player":"1","points":"500"},
                                       {"ranking_date":"20260105","rank":"100","player":"2","points":"100"}])):
        buffer=io.StringIO();writer=csv.DictWriter(buffer,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        raw=buffer.getvalue().encode();path=data/"raw"/name;path.write_bytes(raw)
        atomic_json(Path(str(path)+".meta.json"),{"url":config["source"]["base_url"]+"/"+name,"retrieved_at":"2026-01-12T00:00:00Z","sha256":hashlib.sha256(raw).hexdigest()})
    return config


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.config=fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_repeated_ingest_idempotent_database_and_rating(self):
        first=update(self.root,offline=True)
        second=update(self.root,offline=True)
        self.assertEqual(first["players"],second["players"])
        db=sqlite3.connect(self.root/"data"/"tennis.sqlite")
        self.assertEqual(db.execute('SELECT count(*) FROM matches').fetchone()[0],2)
        self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        stored=db.execute('SELECT rank,rating FROM power_snapshots WHERE date=? AND player_id=?',('2026-01-05','1')).fetchone()
        self.assertEqual(stored,(None,None))
        self.assertEqual(db.execute('SELECT count(*) FROM sources').fetchone()[0],2)
        db.close()

    def test_network_failure_keeps_last_publication(self):
        update(self.root,offline=True)
        old=(self.root/"data"/"snapshot.json").read_bytes()
        with patch('tennis.update.fetch',side_effect=OSError('network unavailable')):
            with self.assertRaises(OSError):update(self.root,refresh=True)
        self.assertEqual(old,(self.root/"data"/"snapshot.json").read_bytes())
        self.assertFalse(json.loads((self.root/"data"/"status.json").read_text())["ok"])
        self.assertFalse((self.root/"data"/"update.lock").exists())

    def test_lock_and_corrupt_cache(self):
        (self.root/"data"/"update.lock").write_text('someone else')
        with self.assertRaisesRegex(RuntimeError,'locked'):update(self.root,offline=True)
        (self.root/"data"/"update.lock").unlink()
        (self.root/"data"/"raw"/"matches.csv").write_text('broken')
        with self.assertRaisesRegex(ValueError,'Checksum'):update(self.root,offline=True)

    def test_changed_source_rejects_old_cache(self):
        cfg=self.config;cfg["source"]["base_url"]='https://example.org/new'
        (self.root/'config.json').write_text(json.dumps(cfg))
        with self.assertRaisesRegex(ValueError,'changed source'):update(self.root,offline=True)

    def test_outcome_correction_replaces_same_identity(self):
        update(self.root,offline=True)
        changed=match(day='20260112',w='1',l='2',wr=10,lr=100)
        buf=io.StringIO();rows=[match(),changed];w=csv.DictWriter(buf,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        path=self.root/'data'/'raw'/'matches.csv';raw=buf.getvalue().encode();path.write_bytes(raw)
        metapath=Path(str(path)+'.meta.json');meta=json.loads(metapath.read_text());meta['sha256']=hashlib.sha256(raw).hexdigest();atomic_json(metapath,meta)
        new=update(self.root,offline=True)
        p=next(p for p in new['players'] if p['id']=='1')
        self.assertEqual(p['stats']['atp']['year']['overall'],[2,0])
        db=sqlite3.connect(self.root/'data'/'tennis.sqlite')
        self.assertEqual(db.execute('SELECT count(*) FROM matches').fetchone()[0],2);db.close()

    def test_api_filters_sort_stats_results_and_pagination(self):
        update(self.root,offline=True)
        app=Application(self.root)
        result=app.api('/api/rankings',{'q':['player 1'],'limit':['1']})
        self.assertEqual(result['total'],1);self.assertEqual(result['players'][0]['id'],'1')
        self.assertNotIn('history',result['players'][0])
        self.assertEqual(app.api('/api/rankings',{'offset':['1'],'limit':['1']})['offset'],1)
        self.assertEqual(app.api('/api/rankings',{'sample':['30']})['total'],0)
        a=app.api('/api/players/2',{'basis':['atp']})
        b=app.api('/api/players/2',{'basis':['power']})
        self.assertNotEqual(a['selected_stats'],b['selected_stats'])
        results=app.api('/api/players/1/results',{'significant':['0']})
        self.assertEqual(results['total'],2)
        self.assertEqual(app.api('/api/players/1/results',{'surface':['Clay']})['total'],0)
        for q in ({'sort':['wat']},{'surface':['Moon']},{'limit':['oops']},{'basis':['bad']}):
            with self.assertRaises(ValueError):app.api('/api/rankings',q)
        with self.assertRaises(KeyError):app.api('/api/players/absent',{})

    def test_truncated_rankings_and_malformed_schema_preserve_publication(self):
        update(self.root,offline=True)
        original=(self.root/'data'/'snapshot.json').read_bytes()
        config=deepcopy(self.config);config['source']['min_ranking_rows']=1000
        (self.root/'config.json').write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError,'truncated'):update(self.root,offline=True)
        self.assertEqual(original,(self.root/'data'/'snapshot.json').read_bytes())
        (self.root/'config.json').write_text(json.dumps(self.config))
        with patch('tennis.update.fetch',return_value=b'wrong,columns\na,b\n'):
            with self.assertRaisesRegex(ValueError,'schema'):update(self.root,refresh=True)
        self.assertEqual(original,(self.root/'data'/'snapshot.json').read_bytes())

    def test_quarantine_does_not_choose_a_convenient_official_rank(self):
        path=self.root/'data'/'raw'/'rankings.csv'
        raw=path.read_bytes()+b'20260105,1000,2,1\n'
        path.write_bytes(raw)
        mp=Path(str(path)+'.meta.json');m=json.loads(mp.read_text());m['sha256']=hashlib.sha256(raw).hexdigest();atomic_json(mp,m)
        publication=update(self.root,offline=True)
        p=next(p for p in publication['players'] if p['id']=='2')
        self.assertIsNone(p['atp_rank'])
        self.assertEqual(len(publication['audit']['quarantined_official_rankings']),1)

    def test_health_history_survives_corrections_and_expiry(self):
        report={'status':'Source-reported return','source_url':'https://example.org/report','reported_at':'2026-01-01',
                'review_after':'2026-01-20','confidence':'Unverified report','correction_history':[]}
        hp=self.root/'data'/'health.json';hp.write_text(json.dumps({'1':report}))
        first=update(self.root,offline=True)
        self.assertIsNotNone(next(p for p in first['players'] if p['id']=='1')['health'])
        report['status']='Corrected report';report['correction_history']=['Status corrected after source clarification']
        hp.write_text(json.dumps({'1':report}));update(self.root,offline=True)
        db=sqlite3.connect(self.root/'data'/'tennis.sqlite')
        # Unique report contents, not just the current status, remain auditable.
        self.assertGreaterEqual(db.execute('SELECT count(*) FROM health_report_history').fetchone()[0],2);db.close()

    def test_future_cutoff_cannot_be_labeled_live(self):
        update(self.root,offline=True)
        original=(self.root/'data'/'snapshot.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'beyond'):update(self.root,offline=True,as_of='2026-12-01')
        self.assertEqual(original,(self.root/'data'/'snapshot.json').read_bytes())

    def test_backtest_must_match_publication_config_cutoff_and_source(self):
        publication=update(self.root,offline=True)
        app=Application(self.root)
        report={'model_version':publication['model_version'],'end_inclusive':publication['as_of'],
                'rating_config':publication['rating_config'],'source_revision':publication['source']['revision'],
                'common_ranked_sample':{'model':{'n':1}}}
        path=self.root/'reports'/'backtest.json';atomic_json(path,report)
        self.assertEqual(app.api('/api/meta',{})['backtest'],report)
        report['source_revision']='another-unrelated-archive';atomic_json(path,report)
        self.assertEqual(app.api('/api/meta',{})['backtest'],{})

    def test_http_security_and_missing_data_states(self):
        app=Application(self.root)
        server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(app))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            for path,status in (('/api/meta',503),('/config.json',404),('/data/raw/matches.csv',404)):
                with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(base+path)
                self.assertEqual(caught.exception.code,status)
                caught.exception.close()
            update(self.root,offline=True)
            with urllib.request.urlopen(base+'/api/meta') as response:
                self.assertIn("frame-ancestors 'none'",response.headers['Content-Security-Policy'])
                self.assertEqual(json.load(response)['player_count'],2)
        finally:
            server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
