# Sources, schemas and provenance

## Public site's current results and published ranking tables

The archive described below is retained for historical research. Public power
ratings use `tennis.current` and the CC BY 4.0 Valuebetennis feed configured in
`current-source.json`, with independent ATP/WTA replays every six hours.

`tennis.official` separately refreshes published singles-ranking snapshots daily:

- ATP and WTA: https://tennis.one/ranking, using the same unauthenticated public
  `https://bleachr-web-api-prod.herokuapp.com/api/players/rankings` feed as the
  web page. Parameters: `gender=male|female`, `sort=singles_rank=ASC`,
  `currentPage=1…`, `take=100`. No login or session token is required.
- Retrieve the first 1,000 positions (including tied positions), not thousands
  of unranked profiles. Initial import: 1,062 ATP and 1,104 WTA players. Validate
  every page, gender, unique IDs, ordered positive ranks and nonnegative points.
- TennisONE supplies **no edition date**. Store `edition: null`, retain retrieval
  and observation timestamps, and label them honestly. Some lower-profile points
  conflict with rank order, and one female profile has an erroneous ATP label;
  these source inconsistencies are disclosed, not silently repaired. Tour identity
  comes from the requested singles list plus explicit gender, never that free-text
  profile label alone.

Store only ranking facts and provider profile links, with tour, edition, source,
retrieval time, checksum, and refresh status. Birth date/gender are retained only
as identity-validation facts, not copied headshots or biographies. A failed tour
keeps its last valid snapshot independently; failures/staleness remain visible.

Direct ATP access was retested in ordinary Chromium on 5 November 2026 and returned
Cloudflare HTTP 403, “Sorry, you have been blocked.” No challenge, proxy, or access
control bypass is used. ESPN was the previous ATP fallback; it is no longer the
scheduled source. The older adapter functions remain for replaying archived tests.

Published rankings are **not** provisional in-tournament live projections and
are not fed into the historical opponent categories. IDs are namespaced
`tennisone:ATP:…` / `tennisone:WTA:…`. Independent public profile metadata is
required to cross-link `valuebetennis:…` IDs (see METHODOLOGY.md). The public
player-history endpoint returned 401 and is not used. No authentication bypass.
The website's “Published singles rankings” table is searchable and tour-isolated.
These provider datasets carry their own terms; the Valuebetennis CC BY license
must not be applied to them. Do not copy headshots or claim exhaustive live scores.

## Current source

Jeff Sackmann / Tennis Abstract, via Aneeshers' archival mirror, pinned to
`83733587353df8a41f2fd4f516147d5aa83f5a8d`.
https://github.com/Aneeshers/tennis-sackmann-archive

CC BY-NC-SA 4.0; preserve attribution/noncommercial/share-alike obligations.
`data/raw/UPSTREAM_README.md` preserves original source documentation. The original
`JeffSackmann/tennis_atp` URLs returned 404 during research on 2026-11-04.

Required match families in config: main tour, qualifying/Challenger, and ITF men's
Futures; imported years 2024–2026. Each downloaded file has its own sidecar URL,
SHA-256, retrieval timestamp and revision. Cached content must match its checksum
and configured URL. A partial refresh cannot publish incomplete required families.
It can update cache files; the previous API publication remains intact on failure.

The actual import has results through June 1, 2026 and rankings through May 25,
2026. Individual tiers/surfaces lag this. The API coverage ledger reports latest
event start and trailing-year counts for every tier/surface, not merely the newest
date in the entire directory. Actual match completion can be later than event start.

## ATP website

https://www.atptour.com/en/rankings/singles is an official human reference. A direct
request returned 403. Section 7 of https://www.atptour.com/en/terms-and-conditions
requires prior written permission for systematic retrieval. Its robots directives
also disallow some scores/archive/statistics paths. These are distinct questions
from whether a browser can view a page. No access-control bypass or scraper is
provided. Obtain appropriate permission or a licensed feed before automated reuse.

## Swapping sources

Change `source.base_url`, `revision`, `years`, `families`, `rankings`, `documents`,
attribution/license metadata and `live` in `config.json`. `live` is just a source
claim and must not be enabled for a frozen archive. Keep `revision` meaningful.
The initial adapter supports **Sackmann-compatible CSVs**, not arbitrary provider
APIs. Integrating another schema requires an explicit adapter before `normalize`.
Do not change file URLs and assume unrelated IDs will reconcile automatically.

Required match fields: `tourney_id`, `tourney_name`, `tourney_date` (YYYYMMDD),
`winner_id`, `loser_id`, `winner_name`, `loser_name`, `score`. Optional fields:
`surface`, `tourney_level`, `round`, `winner_rank`, `loser_rank`, corresponding
`*_rank_points`, `*_age`, `*_ioc`, `*_hand`, `*_ht`, and `match_date` (YYYYMMDD or ISO).
Missing participant ranks stay unknown. Exact intra-day order is not supported yet.

Ranking CSV: `ranking_date,rank,player,points`; aliases `ranking,player_id,ranking_points`
are supported. Choose one edition at/before cutoff. Duplicate conflicting identities
are **quarantined entirely for that edition**, not resolved by picking better rank
or larger points. Quarantines are logged in snapshot audit metadata. Editions must
contain rank 1; configurable minimum-edition checks guard truncated files.

One inspected archive edition, **2026-03-30**, contains only ranks 1–700, versus
roughly 2,200 rows in neighboring editions. It is explicitly excluded with a reason
in `config.json` and the publication audit ledger. At that cutoff use the earlier
complete edition and label its true date. Other unexpectedly truncated editions
still fail validation; do not lower the threshold merely to hide a failed import.

Match identity = event ID + round + sorted participant IDs, independent of outcome
and score. Across source snapshots a corrected winner replaces the match, not a
second win. Conflicting copies inside one import fail validation. A provider with
multiple same-pair matches in one event/round needs an adapter with a trusted match
ID before use. Never force that source into this identity rule.

The SQLite `identity_mappings` table stores provider-scoped IDs. The current adapter
uses the Sackmann namespace. For a second provider, create reviewed mappings based
on stable provider IDs and corroborating biography, not names alone. Provider IDs
must not collide silently. Alternate names are not sufficient identity evidence.

## Optional metadata

`data/health.json` maps stable player IDs to reports:

```json
{
  "PLAYER_ID": {
    "status": "Returning after a reported injury",
    "reported_at": "2026-05-20",
    "review_after": "2026-06-10",
    "confidence": "Source-reported; not independently medically verified",
    "source_url": "https://example.org/verified-report",
    "correction_history": []
  }
}
```

This is a schema example, **not a real report**. URLs must be HTTPS. Only reports
valid at the historical cutoff appear. Maintain correction history in the report;
published reports are retained in the audit database and raw JSON. No fabricated
or unreviewed medical status should be added. Sources and confidence remain visible.

`data/photos.json` maps IDs to `{ "url": "https://…", "credit": "…", "license_url":
"https://…" }`. Verify identity and reuse rights manually; merely supplying a URL
does not establish rights. Images have initials fallbacks on missing/failed loading.
No copyrighted ATP headshots are copied by default.

## Storage and failure behavior

SQLite stores normalized players, match identities/statuses, official editions,
participant pre-date power snapshots with eligible-universe counts, source checksums,
health reports and identity mappings. Rebuilding deterministically handles deletions
and corrections without accumulation of duplicate records. It is an audit database,
not a writable public API. The read-only API serves one atomic JSON publication.

`data/update.lock` prevents concurrent writers. Bounded network retries apply to
transient errors; 403/404 are not repeatedly retried. `data/status.json` records the
latest attempt even when it fails. The last good API snapshot survives. The SQLite
database and JSON snapshot have generation metadata; the API only reads the JSON
snapshot, so it cannot mix generations during publication.
