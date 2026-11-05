from io import BytesIO
import json
import tempfile
from pathlib import Path
import unittest

from publications.update import START, END, fetch_records, render, select_papers, update


def paper(code='2026paper', **kwargs):
    return dict(bibcode=code, title=['A galaxy paper'], author=['Other, Ann', 'Flayhart, Carter B.'],
                author_count=2, doctype='article', citation_count=4, pubdate='2026-01-01',
                property=['REFEREED'], identifier=[], doi=[], pub='Journal', **kwargs)


class PublicationsTests(unittest.TestCase):
    def test_only_papers(self):
        docs = [paper()]
        for kind in ['dataset', 'proposal', 'mastersthesis', 'phdthesis', 'abstract', 'inproceedings']:
            doc = paper(kind); doc['doctype'] = kind; docs.append(doc)
        preprint = paper('preprint'); preprint.update(doctype='eprint', title=['Another paper'])
        self.assertEqual(len(select_papers(docs + [preprint])), 2)

    def test_sort_first_author_then_citations(self):
        first = paper('first'); first.update(author=['Flayhart, Carter', 'Other, Ann'], citation_count=0)
        high = paper('high'); high.update(citation_count=100, title=['High citations'])
        low = paper('low'); low.update(citation_count=3, title=['Low citations'])
        self.assertEqual([d['bibcode'] for d in select_papers([low, high, first])], ['first', 'high', 'low'])

    def test_dedup_prefers_journal_and_does_not_sum_citations(self):
        journal = paper('journal'); journal.update(doi=['10.1/example'], identifier=['arXiv:2601.12345'])
        preprint = paper('preprint'); preprint.update(doctype='eprint', citation_count=2, identifier=['arXiv:2601.12345v2'])
        papers = select_papers([preprint, journal])
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]['bibcode'], 'journal')
        self.assertEqual(papers[0]['citation_count'], 4)

    def test_title_alias_and_transitive_merge(self):
        a = paper('a'); a.update(doi=['10.1/a'])
        b = paper('b'); b.update(title=['A different title'], identifier=['arXiv:2601.12345'])
        c = paper('c'); c.update(title=['Third title'], doi=['10.1/a'], identifier=['arXiv:2601.12345'])
        self.assertEqual(len(select_papers([a, b, c])), 1)
        title_copy = paper('copy'); title_copy.update(title=['A GALAXY PAPER!'])
        self.assertEqual(len(select_papers([a, title_copy])), 1)

    def test_bad_author_and_citations_rejected(self):
        for changes in [dict(author=['Other, Ann'], author_count=1), dict(author_count=3), dict(citation_count=-1), dict(citation_count=None)]:
            doc = paper(); doc.update(changes)
            with self.assertRaises(ValueError): select_papers([doc])

    def test_html_escaped_and_preprints_labelled(self):
        doc = paper(); doc.update(title=['<script>alert(1)</script> $z &gt; 2$'], doctype='eprint')
        result = render({'records': [doc], 'checked_at': '2026-11-04T00:00:00+00:00'})
        self.assertNotIn('<script>', result)
        self.assertIn('&lt;script&gt;', result)
        self.assertIn('z &gt; 2', result)
        self.assertIn('not peer reviewed', result)
        self.assertIn('<strong>Flayhart, Carter B.</strong>', result)

    def test_render_omits_removed_explanatory_notes(self):
        result = render({'records': [paper()], 'checked_at': '2026-11-05T00:00:00+00:00'})
        self.assertNotIn('Articles and preprints, with each paper listed once.', result)
        self.assertNotIn('Citation counts are a dated SciX snapshot', result)
        self.assertIn('SciX / NASA ADS', result)
        self.assertNotIn('<h3>Co-authored papers', result)
        self.assertNotIn('<h3>First-author papers', result)
        self.assertIn('data-publication-filter="first"', result)
        self.assertIn('data-publication-filter="refereed"', result)
        self.assertIn('data-publication-filter="non-refereed"', result)
        self.assertEqual(result.count('class="publication-list"'), 1)
        self.assertIn('data-refereed="true"', result)

    def test_pagination_and_api_auth(self):
        requests = []
        def opener(request, timeout):
            requests.append(request)
            doc = paper(str(len(requests))); doc['title'] = [str(len(requests))]
            return BytesIO(json.dumps({'response': {'numFound': 2, 'docs': [doc]}}).encode())
        result = fetch_records('private-test-token', opener)
        self.assertEqual(len(result['records']), 2)
        self.assertIn('start=1', requests[1].full_url)
        self.assertEqual(requests[0].get_header('Authorization'), 'Bearer private-test-token')
        self.assertNotIn('private-test-token', json.dumps(result))

    def test_empty_response_rejected(self):
        with self.assertRaises(ValueError):
            fetch_records('token', lambda *a, **k: BytesIO(b'{"response":{"numFound":0,"docs":[]}}'))

    def test_offline_render_and_no_token_preserve_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp) / 'site'; site.mkdir()
            snapshot = {'checked_at': '2026-11-04T00:00:00+00:00', 'records': [paper()]}
            (site / 'publications.json').write_text(json.dumps(snapshot))
            (site / 'index.html').write_text('<h2>Publications</h2>' + START + END)
            update(temp, offline=True)
            before = (site / 'index.html').read_text()
            self.assertIn('A galaxy paper', before)
            with self.assertRaises(ValueError): update(temp)
            self.assertEqual((site / 'index.html').read_text(), before)
            self.assertEqual(json.loads((site / 'publications.json').read_text()), snapshot)

    def test_real_snapshot_has_only_unique_papers(self):
        snapshot = json.loads((Path(__file__).resolve().parents[1] / 'site/publications.json').read_text())
        papers = select_papers(snapshot['records'])
        self.assertEqual(len(papers), len({d['bibcode'] for d in papers}))
        self.assertTrue(all(d['doctype'] in {'article', 'eprint'} for d in papers))


if __name__ == '__main__':
    unittest.main()
