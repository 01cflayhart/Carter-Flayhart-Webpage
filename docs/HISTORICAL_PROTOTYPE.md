# Court Current — historical prototype reference

This document describes the original June 2026 archive workflow. The public
website now uses the separate open-results ATP/WTA pipeline; see README.md.

An independent ATP singles power-ranking dashboard: opponent-adjusted ratings,
recent form, surface estimates, historical ATP/power comparisons, and an honest
data coverage ledger. WTA has a clearly marked future tab; no WTA results are
claimed yet.

## Run locally

Python 3.11+; no Python packages or API keys required.

```bash
python3 -m tennis.update
python3 -m tennis.server
```

Open **http://localhost:8765**. On Windows with WSL, localhost forwarding normally
works; run these commands from this project in WSL. The server binds to loopback,
not the public network. Keep that terminal running.

The first import downloads roughly 17 MB of raw match/ranking data and source
documentation. Allow additional disk space for the SQLite audit database and API
snapshot. Files are checksummed and cached. Subsequent deterministic replays:

```bash
python3 -m tennis.update --offline
python3 -m tennis.update --offline --as-of 2026-05-25
python3 -m tennis.backtest
python3 -m unittest discover -v
```

`--as-of` never accepts a date later than the available results. An earlier date
can lack an official ranking edition: that is displayed as unavailable. Restore
the latest snapshot by running the normal offline update without `--as-of`.
`--refresh` refetches configured files; it **does not make a pinned archive live**.

### What you can explore

- Overall, hard, clay, grass and historical carpet rankings.
- Search by player/country; sort table headings; active, tier, age-context flag and
  sample-size filters; optional full-statistics table.
- ATP vs power comparison toggle using historical event-start/pre-date snapshots.
- Trailing 12-month and three-calendar-month W–L against top 50, similar (±25),
  better, worse and unknown-ranked players; surface breakdowns and percentages.
- Player notebooks with **both periods side by side**, availability/uncertainty,
  all significant results and all-match history, with pagination and surface filters.
- Per-result immediate rating changes and pre-match probability estimates.
- Source checksums, coverage by tier/surface, quarantines, freshness and backtests.

“Better” and “worse” exclude the similar band, making categories disjoint. Top 50
overlaps them. W–L counts are unweighted, even though the rating is weighted.

## Important: historical, not live

The configured source is Jeff Sackmann / Tennis Abstract's dataset, preserved by
Aneeshers under **CC BY-NC-SA 4.0**. The verified current configuration has matches
through **2026-06-01**, with different earlier cutoffs in some tiers/surfaces.
The published official ranking edition at that cutoff is **2026-05-25**. This is not a claim of
complete results through either date. The UI shows the measured coverage.

The archive usually supplies event-start dates and rankings, **not exact match-day
rankings or match timestamps**. Power categories freeze before the date's entire
batch, avoiding invented ordering and future-result leakage. First-observation
power ranks are unknown. Current display ranks come from one official edition,
never independently selected old ranks for each player.

Conflicting official ranking identities are quarantined: affected official ranks
are unknown, with details in the audit ledger. They are not silently resolved.
There is no verified injury feed or licensed headshot collection yet. Honest
initials and “not independently verified” are intentional fallbacks.

For continuous current coverage across ATP, Challengers **and ITF men's events
awarding ATP points**, a permitted, sufficiently complete updating source remains
necessary. The ATP website is a useful reference, but section 7 of its terms
requires permission for systematic retrieval. No ATP scraper is included.

## OpenCode maintenance agent

The project includes `.opencode/agents/tennis-updater.md`. Select **tennis-updater**
in OpenCode or, using the installed CLI's supported flags:

```bash
opencode run --agent tennis-updater "Inspect freshness, run tests, replay the cached data, and report coverage gaps."
```

No model is hardcoded: use an available model configured for your Go subscription.
The Go subscription does not supply tennis data, hosting, a running computer, or
permission to reuse somebody else's data. Routine updates do not need an LLM.
No recurring schedule or paid service has been activated. See
[deployment and opt-in scheduling](docs/DEPLOYMENT.md).

## Optional browser tests

The app itself needs no Node dependencies. For automated desktop/mobile and
accessibility checks only:

```bash
npm ci
npx playwright install chromium
npm test
```

Tests start an isolated server on port 8766 and require an imported dataset.
Browser screenshots/test artifacts are ignored by Git.

## Structure

| Path | Purpose |
| --- | --- |
| `config.json` | Source revision, file families, model parameters and tour scope |
| `tennis/update.py` | Bounded fetching, checksum validation, replay, publication |
| `tennis/engine.py` | Deterministic historical ratings and statistics |
| `tennis/storage.py` | Normalized SQLite matches/rankings/provenance/snapshots |
| `tennis/server.py` | Read-only, paginated API and loopback HTTP server |
| `web/` | Responsive dependency-free dashboard |
| `data/health.json`, `data/photos.json` | Optional sourced player metadata |
| `tests/` | Python correctness/integration and browser checks |
| `reports/backtest.json` | Generated out-of-time baseline/calibration report |

Read [methodology](docs/METHODOLOGY.md), [source integration](docs/DATA_SOURCES.md),
[deployment](docs/DEPLOYMENT.md), and [verification](docs/VERIFICATION.md).

### Data and licensing

Data attribution: **Jeff Sackmann / Tennis Abstract**, via
[Aneeshers' archive](https://github.com/Aneeshers/tennis-sackmann-archive).
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) applies to that
data and relevant adaptations: attribution, noncommercial use, and share-alike
obligations apply. Cached upstream documentation is preserved under `data/raw/`.
Do not assume permission for commercial deployment, unrelated photos, ATP branding,
or arbitrary scraped data. This project is not affiliated with ATP or WTA.
