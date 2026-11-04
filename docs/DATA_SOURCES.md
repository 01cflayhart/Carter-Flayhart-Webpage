# Sources, schemas and provenance

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
