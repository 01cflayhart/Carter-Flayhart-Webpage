# Sports hub operations and launch checklist

For account-by-account instructions and exact commands, start with [Launch Carter’s website](launch-guide.md). This document is the technical feed and model contract.

## Current truth

- Prop Hunt and Upset Alert are connection-ready experimental tools, **not live betting models**. No picks, wins or historical accuracy are fabricated. The prop probability baseline is implemented; independent favorite projections are an input contract, not a trained multisport model supplied by this repository.
- Free, unauthenticated nflverse 2026 weekly player stats and schedule were retrieved successfully on 2026-11-06. New stats use the `stats_player/stats_player_week_2026.csv` release, NOT the obsolete all-years player_stats.csv (which stops at 2024). Private caches live in ignored `data/sports/`; public connection metadata is in `site/sports/analysis/connections.json`.
- nflverse alone does not supply current book prices, verified injury opportunity adjustments, cross-provider identities, complete matchup projections or sportsbook-specific grading. No name-only joins are allowed. The Odds API adapter collects raw odds; it intentionally does not treat them as independent projections.
- The Odds API offers a free signup tier for DraftKings/FanDuel. Its bookmaker documentation lists **Fanatics and Caesars as paid-only**. Caesars’ API key is `williamhill_us`; the website’s internal key is `caesars`. No comprehensive free four-book solution has been authenticated or found. Do not bypass sportsbook controls or buy a plan without Carter’s permission.
- Cloudflare deployment, GitHub OAuth, D1 and email delivery are prepared but **not activated**. No Cloudflare credential was present. The opened Cloudflare dashboard is display-only in this environment; an authorized account holder must complete setup. Availability of `carterflayhart.pages.dev` has not been established.
- Changes are local until committed/pushed. GitHub workflows do not run merely because their files exist locally.

## Daily work

`python3 -m sports.daily` fetches free data, optionally retrieves authenticated odds and a normalized evidence feed, settles known frozen predictions, publishes book-specific boards, and writes daily previous-day/all-history/rolling reviews. The GitHub workflow runs at 11:17 UTC (06:17 EST / 07:17 EDT); slates use America/New_York. GitHub scheduled runs can be delayed.

OpenChamber has two enabled read-only agent review schedules: Prop Hunt at **08:15 Eastern** and Upset Alert at **08:25 Eastern**, after the scheduled data job. They use the existing `openai/gpt-6.1-sol` provider and therefore its normal inference usage/billing; no additional paid data subscription was purchased. OpenChamber must be running. Reviewers must still check timestamps and report delayed or stale input. They do not execute trades, edit forecasts or automatically promote model changes. Source/selection updates run deterministically through GitHub Actions after this code is pushed. Model improvement is evidence-based review, not an unfounded promise of daily accuracy gains.

For local inspection: `python3 -m sports.update --inputs /path/to/private-normalized.json`. No input produces honest empty boards while retaining historical results. Unit tests use synthetic fixtures only, never public picks.

### Secrets and optional controls

Set secrets through GitHub/Cloudflare settings, never in chat, frontend JavaScript or committed files:

| Setting | Where | Purpose |
|---|---|---|
| `ODDS_API_KEY` | GitHub Actions secret | Free or explicitly approved Odds API account |
| `SPORTS_INPUT_URL` | GitHub Actions secret | HTTPS normalized, independently verified pregame evidence and final-outcome feed |
| `SPORTS_INPUT_TOKEN` | GitHub Actions secret | Optional bearer authorization for that feed |
| `CLOUDFLARE_API_TOKEN` | GitHub Actions secret | Account-scoped Pages deployment authorization |
| `CLOUDFLARE_ACCOUNT_ID` | GitHub Actions secret | Target account |
| `CLOUDFLARE_D1_DATABASE_ID` | GitHub Actions repository variable | Actual D1 UUID; generated deployment binding and migrations |

The daily workflow defaults to six odds credits maximum per run and only DraftKings/FanDuel moneylines. Tennis tournaments are discovered dynamically, not guessed. Six daily credits are not a completeness guarantee. Local `ODDS_FETCH_PROPS=1` enables seven prop markets per NFL event within the budget (`ODDS_DAILY_CREDITS`, capped at 12); this may exceed free monthly quotas over a season. `ODDS_PAID_BOOKS=1` is an explicit opt-in for already-authorized paid-book access, never a subscription purchase. Provider failures retain private caches but cannot generate fresh model picks from old data.

### Normalized evidence contract

JSON root: `prop-hunt` and `upset-alert` arrays, `nfl_schedule` array (`event_id`, timezone-aware `starts_at`), and `results` array. Schedule count must cover the entire NFL day, not only games with eligible props. All source/evidence fields must be public-safe prose or URLs **without credentials**; selected rows and their evidence become public. Only trusted, rights-cleared upstream transforms should create this feed.

Every candidate requires:

- Stable string `id`, `event_id`, `subject_id`; human-readable `label`, `source`, `evidence`.
- `book`: draftkings/fanduel/fanatics/caesars. `sport`: NFL/NCAAF/NCAAB/Tennis (Prop Hunt only NFL).
- American `odds`; timezone-aware `as_of` (no more than six hours old) and future `starts_at` on today’s Eastern slate.
- `identity_verified: true`, `availability_verified: true`, backed by the evidence. Do not set flags by assuming a name match or “no injury news.”

Props additionally require `season` (NFL season year), at least eight chronological unique completed-game `game_dates` strictly before the current slate date, corresponding numeric `values`, `market`, numeric `line`, `side` Over/Under, numeric `matchup_multiplier` and `opportunity_multiplier` (combined adjustment within 0.5–1.5), and `matchup_evidence`/`opportunity_evidence`. Integer over lines mean strictly greater, not “at least”; labels must match book semantics. Prior-season samples cannot be passed off as current-season consistency. Projection is a smoothed recency-weighted empirical estimate; it is not yet calibrated, and uniform role/defense scaling is a deliberately provisional approximation.

Favorites additionally require `probability` strictly between 0 and 1, `independent_projection: true`, and `projection_model` identifying the independent version. A missing independent forecast must not be replaced by the sportsbook’s implied probability. Fresh fetched moneylines now appear separately under **Market coverage · not forecasts**, using only source-native event/team labels. This adapter excludes NBA/MLB, in-play events, non-Eastern-day events and prices more than six hours old. It never joins player identities, assigns categories or creates a track record. Coverage is limited to what the authorized feed actually returned, not every matchup on the schedule. Old raw prices are hidden by the browser as well as the daily builder.

Results require an existing `prediction_id`, `outcome` win/loss/push/void, `verified_final: true`, public-safe `source`, and timezone-aware `final_at` after event start and before observation time. A prop appearing in both lists has separate placement IDs; send each ID’s settlement. Never assume DNP, retirement, postponement or tie grading is identical across books. Unknown final statuses remain pending. Conflicting corrections stop the update for explicit review instead of rewriting the ledger silently.

## Forecasts and evaluation

- Nonempty pregame slates freeze at `site/sports/analysis/archive/<tool>/<book>/<date>.json`. A rerun never revises that day’s picks, ranks or forecasts. Empty, unconnected slates can be populated later before start. `settlements.json` is separate; current JSON joins results without modifying forecasts.
- Top props: odds -150 or longer, projected probability >=55%, edge >=3 percentage points over implied price; ranked by projected probability. Whole-slate caps: 1 game→3, 2–3→5, >=4→10. One threshold per subject/market/side.
- “Safe” watchlist: >=8 current-season observations, >=90% raw hit rate and >=85% projected estimate. Publish only the strongest qualifying threshold, with easier alternatives and their estimates. This is NOT evidence of 100% reliability; early estimates can be wrong.
- Favorites: book moneyline <=-200, independent probability; categories use exact lower bounds .95/.85/.75/.60. Lower than .60 is Storm Chasers.
- Win rates exclude pushes/voids and count pending separately. Report settled n and Brier error. Rolling windows are calendar 7/30-day windows through the observation date, not the last 7/30 predictions. Prop Hunt combined totals count list placements; evaluate each list separately to avoid duplicate interpretation. Reports are grouped by book, list, top rank, category and sport.
- Daily reviews include yesterday’s result summary. Do not tune to yesterday alone. Save future model candidates under a new version, test chronologically on untouched holdout data, compare calibration/coverage, and approve before promotion. No automatic changes are made when there is no evaluation evidence.

## Cloudflare Pages activation

1. Sign in to Cloudflare and create a Pages project named `carterflayhart` (if available), production branch `main`. This is what reserves the desired pages.dev hostname. Do not assume the hostname exists just because canonical metadata references it.
2. The recommended route is a Direct Upload Pages project deployed by `.github/workflows/cloudflare.yml`, authorized by the two Cloudflare GitHub secrets and D1 repository variable above. Do not also enable Cloudflare Git integration. The workflow skips when any required setting is missing; it also refreshes every six hours.
3. Create D1 database `carter-site-activity` and set its actual UUID as `CLOUDFLARE_D1_DATABASE_ID`. `node scripts/configure-cloudflare.cjs` generates ignored `wrangler.jsonc` with binding `DB`, production origin and owner ID; GitHub Actions runs this automatically. The workflow applies pending `migrations/` before deployment. No placeholder ID is deployed. See the launch guide for local CLI setup.
4. Register a GitHub OAuth app with callback `https://carterflayhart.pages.dev/api/auth/callback`. Set Pages secrets `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `SESSION_SECRET` (cryptographically random >=32 bytes) and `GITHUB_OWNER_ID=168453384`. The numeric ID was verified from the public GitHub API for `01cflayhart`. No repository scopes are requested. Preview hosts need separate callback configuration; do not authorize arbitrary redirect hosts.
5. Configure a free email sender provider (implemented adapter: Resend) with `RESEND_API_KEY` and `FEEDBACK_FROM` as Pages secrets. Resend’s sandbox sender can generally send only to the verified account owner; verify that the recipient is Carter’s personal email before relying on it. Custom-domain sender verification requires a domain; pages.dev is not yours to verify for email. No successful email delivery has been claimed or tested here.
6. Deploy and verify: public boards, feedback actually arriving at `carter.flayhart@gmail.com`, anonymous `/api/owner/stats` denied, non-owner GitHub login denied, owner `/private` working, owner exclusion on/off, cookies/no-store headers and D1 counts split by sports/professional.

`/private` renders only a login prompt without owner authorization. Statistics never ship as a static JSON file. A private tab is added to navigation only after server authorization. Owner activity is excluded by default on login; an HTTP-only preference cookie lets Carter include it or exclude it on that browser, and exclusion persists after logout. Public visitors can disable application tracking through DNT or Global Privacy Control. Counts are coarse daily page views, not unique visitors or complete bot-filtered analytics.

Owner-only `/api/owner/setup` checks OAuth configuration, the live presence of both D1 tables, and email configuration without exposing credential values or sending mail. `/private` displays these checks with retry controls. Missing login configuration shows an explanatory screen; authentication is restricted to the configured production origin, not arbitrary preview hosts. Email configuration is never presented as verified inbox delivery.

## Search visibility

Canonical URLs, sitemap, robots.txt, descriptive titles, social metadata and Person structured data target `https://carterflayhart.pages.dev`. Once live, verify ownership in Google Search Console and Bing Webmaster Tools, submit `/sitemap.xml`, request indexing, and link this address from the GitHub profile and academic profiles. Keep existing GitHub Pages available until Cloudflare succeeds; then redirect or retain the Cloudflare canonical to consolidate indexing. Search positions and first place for “Carter Flayhart” cannot be guaranteed. Account verification and search-engine submission require Carter’s authenticated accounts.

## Verification

`python3 -m unittest discover -q` · `npm run test:security` · `npm run test:cloudflare` · `python3 -m tennis.export` · `npm run test:pages`. Run local Workers/D1 and Chromium checks serially. The Cloudflare check uses isolated temporary storage, synthetic credentials and only a local D1 migration; it does not create resources in an account or send mail.

Browser checks default to one worker. See `docs/session-recovery.md` for bounded continuation and persistent Linux browser dependencies.

These test static behavior and handler logic. Real GitHub OAuth, Cloudflare/D1 routing, email arrival and live licensed-feed coverage still need integration testing with authorized accounts.
