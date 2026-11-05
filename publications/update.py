"""Refresh papers through the supported ADS/SciX API; never expose its token."""
import argparse
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
QUERY = 'author:"Carter Flayhart"'
SEARCH_URL = 'https://scixplorer.org/search?' + urlencode({'q': QUERY, 'sort': 'citation_count desc'})
FIELDS = 'bibcode,title,author,author_count,pubdate,doctype,citation_count,doi,identifier,property,pub,volume,page'
START = '<!-- publications:start -->'
END = '<!-- publications:end -->'


def plain(value):
    """Render source TeX as readable plain text, never executable source HTML."""
    value = html.unescape(str(value))
    value = re.sub(r'\\(?:rm|mathrm|text|textrm)\b', '', value)
    value = value.replace('$', '').replace('{', '').replace('}', '')
    return value.replace('\\', '').replace('_', ' ')


def normalize(value):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', plain(value)).encode('ascii', 'ignore').decode().lower())


def is_carter(name):
    surname, _, given = name.partition(',')
    return surname.strip().lower() == 'flayhart' and bool(re.match(r'(carter\b|c\.?($|\s))', given.strip(), re.I))


def aliases(doc):
    result = {'bib:' + doc['bibcode'].lower()}
    for value in [*doc.get('doi', []), *doc.get('identifier', [])]:
        value = value.lower().strip()
        value = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', value)
        if value.startswith('10.'):
            result.add('doi:' + value)
        arxiv = re.search(r'(?:arxiv[:.]|arxiv\.org/abs/)(\d{4}\.\d{4,5}|[a-z-]+/\d{7})', value)
        if arxiv:
            result.add('arxiv:' + arxiv.group(1))
        if re.match(r'^\d{4}[a-z&.]+', value) and not value.startswith('10.'):
            result.add('bib:' + value)
    result.add('title:' + normalize(doc['title'][0]) + ':' + normalize(doc['author'][0]))
    return result


def select_papers(docs):
    """Merge connected DOI/arXiv/bibcode/title aliases; prefer published versions."""
    groups = []
    for doc in docs:
        if doc.get('doctype') not in {'article', 'eprint'}:
            continue
        if not doc.get('bibcode') or not doc.get('title') or not doc.get('author'):
            raise ValueError('Incomplete paper metadata')
        if len(doc['author']) != doc.get('author_count', len(doc['author'])):
            raise ValueError('Truncated author list')
        if not any(is_carter(author) for author in doc['author']):
            raise ValueError('Search returned a paper without the expected author')
        count = doc.get('citation_count')
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError('Missing or invalid citation count')
        keys = aliases(doc)
        matches = [group for group in groups if group[0] & keys]
        merged_docs = [doc]
        for group in matches:
            keys |= group[0]
            merged_docs += group[1]
            groups.remove(group)
        groups.append((keys, merged_docs))
    papers = []
    for _, versions in groups:
        versions.sort(key=lambda d: (d['doctype'] == 'article', 'REFEREED' in d.get('property', []), d.get('pubdate', ''), d['bibcode']), reverse=True)
        canonical = dict(versions[0])
        canonical['citation_count'] = max(d['citation_count'] for d in versions)
        canonical['first_author'] = is_carter(canonical['author'][0])
        canonical['doi'] = sorted({v for d in versions for v in d.get('doi', [])})
        canonical['identifier'] = sorted({v for d in versions for v in d.get('identifier', [])})
        canonical['versions'] = sorted({d['bibcode'] for d in versions})
        papers.append(canonical)
    # First-author work is newest-first; all other work is citation-ranked.
    papers.sort(key=lambda d: (d.get('pubdate', ''), d['bibcode']), reverse=True)
    papers.sort(key=lambda d: (not d['first_author'], 0 if d['first_author'] else -d['citation_count']))
    return papers


def render_entry(doc):
    esc = lambda value: html.escape(plain(value), quote=True)
    authors = doc['author']
    # Show first authors and always Carter, without implying Carter led the paper.
    shown = list(authors[:3])
    carter = next(author for author in authors if is_carter(author))
    if carter not in shown:
        shown.append(carter)
    author_html = '; '.join('<strong>' + esc(a) + '</strong>' if is_carter(a) else esc(a) for a in shown)
    if len(authors) > len(shown):
        author_html += '; et al.'
    bibcode = quote(doc['bibcode'], safe='')
    links = [f'<a href="https://scixplorer.org/abs/{bibcode}/abstract">SciX</a>']
    doi = next((d for d in doc.get('doi', []) if not d.lower().startswith('10.48550/')), None)
    if doi:
        links.append(f'<a href="https://doi.org/{quote(doi, safe="/")}">Paper</a>')
    arxiv = next((v.split(':', 1)[1] for v in doc.get('identifier', []) if v.lower().startswith('arxiv:')), None)
    if arxiv:
        links.append(f'<a href="https://arxiv.org/abs/{quote(arxiv, safe="/")}">arXiv</a>')
    date = doc.get('pubdate', '')[:7]
    venue = doc.get('pub', 'Preprint')
    if doc['doctype'] == 'eprint':
        venue = 'arXiv preprint · not peer reviewed'
    count = doc['citation_count']
    return (f'<li class="publication" data-bibcode="{html.escape(doc["bibcode"], quote=True)}" data-citations="{count}">'
            f'<h4>{esc(doc["title"][0])}</h4><p class="publication-authors">{author_html}</p>'
            f'<p class="publication-venue">{esc(venue)} · {esc(date)}</p>'
            f'<div class="publication-links">{" ".join(links)}'
            f'<a class="citation-link" href="https://scixplorer.org/abs/{bibcode}/citations">{count} {"citation" if count == 1 else "citations"}</a></div></li>')


def render(snapshot):
    papers = select_papers(snapshot['records'])
    first = [d for d in papers if d['first_author']]
    rest = [d for d in papers if not d['first_author']]
    date = snapshot['checked_at'][:10]
    return (f'\n<p class="publication-updated">Source: <a href="{html.escape(SEARCH_URL, quote=True)}">SciX / NASA ADS</a> · Checked <time datetime="{date}">{date}</time> · {len(papers)} papers</p>\n'
            '<h3>First-author papers</h3>\n' +
            ('<ol class="publication-list">' + '\n'.join(render_entry(d) for d in first) + '</ol>' if first else '<p class="editorial-note">No first-author articles or preprints are currently indexed in this selection.</p>') +
            '\n<h3>Co-authored papers</h3>\n<ol class="publication-list">' + '\n'.join(render_entry(d) for d in rest) + '</ol>\n')


def fetch_records(token, opener=urlopen):
    docs = []
    total = None
    while total is None or len(docs) < total:
        params = urlencode({'q': QUERY, 'fl': FIELDS, 'rows': 200, 'start': len(docs), 'sort': 'bibcode asc'})
        request = Request('https://api.adsabs.harvard.edu/v1/search/query?' + params,
                          headers={'Authorization': 'Bearer ' + token, 'User-Agent': 'Carter-Flayhart-Publications/1.0'})
        with opener(request, timeout=45) as response:
            payload = json.load(response)['response']
        if total is not None and total != payload['numFound']:
            raise ValueError('Search changed during pagination; retry later')
        total = payload['numFound']
        batch = payload['docs']
        if not batch and len(docs) < total:
            raise ValueError('Incomplete SciX pagination')
        docs.extend(batch)
    if not docs or len(docs) != total or len({d['bibcode'] for d in docs}) != total:
        raise ValueError('Empty, duplicate, or truncated SciX response')
    select_papers(docs)  # Validate before replacing the last valid snapshot.
    return {'query': QUERY, 'source': SEARCH_URL, 'checked_at': datetime.now(timezone.utc).isoformat(), 'records': docs}


def atomic_write(path, text):
    with tempfile.NamedTemporaryFile('w', dir=path.parent, encoding='utf-8', delete=False) as stream:
        stream.write(text)
        tmp = stream.name
    os.replace(tmp, path)


def update(root=ROOT, token=None, offline=False):
    root = Path(root)
    target = root / 'site' / 'publications.json'
    page = root / 'site' / 'index.html'
    if offline:
        snapshot = json.loads(target.read_text())
    else:
        if not token:
            raise ValueError('ADS_API_TOKEN is required; the existing publication list is unchanged')
        snapshot = fetch_records(token)
    body = render(snapshot)
    markup = page.read_text()
    if markup.count(START) != 1 or markup.count(END) != 1:
        raise ValueError('Missing or duplicate publication markers')
    updated = markup.split(START)[0] + START + body + END + markup.split(END)[1]
    atomic_write(target, json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')
    atomic_write(page, updated)
    print(f'Updated {len(select_papers(snapshot["records"]))} papers from {len(snapshot["records"])} SciX records')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='Render the checked-in snapshot without changing its timestamp')
    args = parser.parse_args()
    update(token=os.environ.get('ADS_API_TOKEN'), offline=args.offline)
