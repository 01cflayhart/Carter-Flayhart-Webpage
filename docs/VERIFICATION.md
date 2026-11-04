# Verification

The new public website uses `python3 -m tennis.current` and `python3 -m tennis.export`.
The commands and counts below originally documented the historical ATP prototype.
For the public two-tour pipeline: 44 Python tests pass; 12 desktop/mobile API
dashboard tests and 4 server-free Pages tests pass, including axe overview/profile
scans, independent WTA switching, filters, result history and publication polling.
Run `npx playwright test --config playwright.pages.config.cjs` after exporting.
The two browser suites use separate output directories and can run independently.
Current source baselines are generated inside each tour snapshot, never reused
from the old June archive report. See docs/PUBLIC_SITE.md for limitations.

## Repeatable commands

```bash
python3 -m unittest discover -v
node --check web/app.js
python3 -m tennis.update --offline
python3 -m tennis.backtest
npm test
```

Python tests use synthetic fixtures for exact known behavior; browser tests use
the imported real archive. No fixture is displayed as actual professional results.

Engine tests cover rank bands, unknowns, historical category modes, pre-date
freezing, future-result leakage, age neutrality, calendar windows/leap days, surface
pooling, recency expiration, inactivity caps, team/retirement treatment, duplicates,
and metadata validation. Integration tests exercise actual HTTP errors, security
headers, pagination/filters, corrections, idempotence, locks, checksums, changed
source URLs, and last-good-publication retention after download failure.

The generated `reports/backtest.json` includes common-sample and all-sample log loss,
Brier score, calibration bins and tier/surface breakdowns. The dashboard surfaces
the same baseline comparisons rather than claiming unmeasured superiority.

Linux browser verification requires Chromium system libraries. If Playwright
reports missing `libnspr4`, `libnss3` or `libasound`, install its documented OS
dependencies (`npx playwright install --with-deps chromium`, with appropriate OS
administrator permission). During this implementation, missing libraries were
downloaded and extracted under `/tmp/opencode/browser-deps` without altering the
system; tests were run with that extracted library directory in `LD_LIBRARY_PATH`.

Browser checks cover desktop/mobile rendering, keyboard-accessible dialogs,
search/empty states, sortable headings, surface and comparison toggles, full-table
mode, player records, significant/all-result views, and axe WCAG checks. Screenshots
are test artifacts rather than part of the data/model.

## Implementation verification: November 4, 2026

- 33 Python correctness/integration tests pass.
- 12 Chromium desktop/mobile tests pass, including axe scans of the overview and
  player dialog, keyboard navigation, and simulated publication refresh/outage.
- `node --check web/app.js` passes. Browser output from this run is saved at
  `/tmp/opencode/court-current-browser-tests.log`.
- Offline publication: 3,547 players, 33,865 trailing-year matches, event-start
  cutoff 2026-06-01. Official display edition 2026-05-25. The inspected incomplete
  2026-03-30 ranking edition is excluded explicitly, not presented as complete.
- Common-sample backtest: 28,480 ranked played matches; model log loss 0.61046,
  Brier 0.21140; fixed Elo 0.62041 / 0.21582; rank transform 0.65170 / 0.22970.
  Lower is better. These provisional, approximate-date archive comparisons are
  **not an untouched final holdout**; a future independent evaluation is needed.
- Raw input files and source notices are preserved and checksummed. The published
  API snapshot remains last-good after simulated malformed/truncated inputs,
  checksum corruption, a changed source URL and network failure.

## Remaining external dependencies

These are not claimed as completed by the historical prototype:

- A permitted updating feed with complete ATP, Challenger and ATP-points ITF scope.
- Exact match timestamps/order and exact pre-match official rankings rather than
  event-start approximations; current engine intentionally freezes same-date batches.
- Licensed player headshots and verified, maintained injury/return reports.
- An untouched future predictive holdout and further parameter calibration.
- User-selected unattended schedule, always-on host, public production deployment.
- WTA data ingestion, identity reconciliation and validation; the future tab is
  labeled clearly and shares no fabricated ATP/WTA combined rank universe.
