# Carter Flayhart — personal website & Court Current

Academic personal website with About Me, Research, Publications, Talks & Conferences,
Sports Analysis, Hobbies, CV, and Contact, plus **completely separate ATP and
WTA singles power rankings**, designed for free GitHub Pages hosting.

- Repository: https://github.com/01cflayhart/Carter-Flayhart-Webpage
- Pages: https://01cflayhart.github.io/Carter-Flayhart-Webpage/
- Tennis: https://01cflayhart.github.io/Carter-Flayhart-Webpage/sports/tennis/
- Requested custom domain: **CarterFlayhart.com**, pending user registration/DNS.

## Build and publish

Python 3.11+; the application needs no Python packages or paid API key.

```bash
python3 -m unittest discover -q
python3 -m tennis.current
python3 -m tennis.export
```

The last command builds `_site/`, the only public deployment artifact. No Python
server is required by visitors. GitHub Actions performs the same build on pushes,
manual requests and every six hours. Deploy only after both tours validate; failed
jobs preserve the last successful website. See [deployment and domain setup](docs/PUBLIC_SITE.md).

For development preview only:

```bash
python3 -m http.server 8768 --directory _site
```

`python3 -m tennis.current --offline` replays verified cached CSVs without fetching
new results. It cannot make an old cache current; inspect the source ledger and
latest accepted match per tour. Normal scheduled builds fetch the feed afresh.

## What the rankings do

Opponent-adjusted historical strength plus a recency-weighted form overlay,
surface-specific estimates, absence adjustments, significant results, raw W–L
records over 12 and 3 calendar months, sorting/search/filtering and individual
player notebooks. Similar = ±25 inclusive. ATP and WTA use isolated player IDs,
separate matches, separate replay state and separate rank universes. Scores are
not cross-tour comparisons.

## Current data limitations — read before relying on ratings

Current open source: **Valuebetennis**, [CSV documentation](https://www.valuebetennis.com/donnees.htm),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution required.
No bookmaker odds enter the model. The site is not betting advice.

The November 4, 2026 import checks results through that date. Latest accepted ATP
result: November 4; WTA: November 3. There are 3,142 ATP and 2,551 WTA players with
15,620 / 11,268 covered trailing-year matches respectively. These counts describe
accepted coverage, **not full professional-tour coverage**. Large numbers of missing
and incomplete scores are excluded and disclosed in the ledger.

The CSV has no official ranks/points, country/age metadata, verified injuries or
licensed photos. Missing fields stay unknown. Historical power comparisons are
available; official-rank comparisons are disabled rather than filled with today's
or June's ranks. ATP's official page is a reference, not a licensed public feed:
its terms restrict republication and systematic collection without permission.

The dashboards now also show an independent, searchable published-ranking table:
ATP via ESPN (top 150 supplied), and WTA's public rankings feed (1,552 players in
the initial 2 November edition). `python3 -m tennis.official` validates and records
source dates, checksums and retrieval times. These source identities are **not**
joined to match histories by name. Today’s ranks do not rewrite historical records.
`website-data.yml` checks rankings and synchronizes the public Overleaf CV PDF
daily at 08:43 UTC; result-based ratings continue to rebuild every six hours.

On the new source's covered sample, basic Elo currently slightly outperforms this
form model. Both results are shown. The model remains provisional; no independent
final holdout or comprehensive live coverage is claimed.

## Verification

```bash
python3 -m unittest discover -v
npm ci
npx playwright install chromium
npm test
npx playwright test --config playwright.pages.config.cjs
```

Browser tests require current snapshots (`tennis.current`) and exported assets
(`tennis.export`) respectively. See [verification](docs/VERIFICATION.md).

## Structure

| Path | Purpose |
|---|---|
| `site/` | Personal homepage and Sports Analysis navigation |
| `web/` | Responsive tennis dashboard and server-free static API |
| `tennis/current.py` | Licensed current-results adapter and isolated tour replay |
| `tennis/export.py` | Explicit public-only Pages artifact |
| `tennis/engine.py` | Deterministic historical ratings and statistics |
| `current-source.json` | Open feed attribution and temporal scope |
| `.github/workflows/pages.yml` | Scheduled testing, data refresh and deployment |
| `docs/PUBLIC_SITE.md` | Hosting, domain, data license and official-rank dependencies |
| `docs/PERSONAL_SITE.md` | Verified CV/profile content, CV PDF synchronization, publication filters, and image attribution |
| `tennis/official.py` | Independent, dated ATP/ESPN and official WTA ranking snapshots |
| `scripts/refresh-cv.cjs` | Read-only Overleaf PDF synchronization |
| `publications/update.py` | Supported SciX API refresh, papers-only filtering, deduplication, and publication ordering |

The original June ATP archive tooling remains available separately for reproducible
historical research. It is **not** mixed into the public current-results pipeline.
See [historical prototype reference](docs/HISTORICAL_PROTOTYPE.md),
[rating method](docs/METHODOLOGY.md), and [legacy source schemas](docs/DATA_SOURCES.md).
