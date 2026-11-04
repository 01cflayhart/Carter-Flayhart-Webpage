# Public website and custom domain

Repository: https://github.com/01cflayhart/Carter-Flayhart-Webpage

Default Pages URL: https://01cflayhart.github.io/Carter-Flayhart-Webpage/

## Hosting

`site/` supplies the personal homepage and Sports Analysis navigation. `web/`
supplies Court Current at `sports/tennis/`. `python3 -m tennis.export` creates
`_site/`, with ATP and WTA files in separate namespaces. The browser filters exported
statistics and loads individual notebooks on demand. No public Python process,
API key, localhost tunnel or paid hosting service is required.

`.github/workflows/pages.yml` tests, retrieves the open results, replays both tours,
exports and deploys using GitHub Pages. Schedule: 00:23, 06:23, 12:23 and 18:23 UTC.
GitHub may delay schedules and may disable schedules after repository inactivity.
Check Actions; use **Run workflow** for a manual refresh. If retrieval or validation
fails, deployment does not run and the last successful site stays published. Its
old build timestamp and client-computed result age remain visible; the old artifact
cannot know the new job's failure. No failure is misrepresented as fresh results.

The build serves only `_site/`, never `.git`, raw CSVs, SQLite files, tokens or
OpenCode/session configuration. Do not commit credentials. The Pages deploy uses
GitHub's short-lived job token, not a long-lived personal token.

## CarterFlayhart.com: pending registration

The user confirmed the domain is not registered. No purchase has been authorized
or made. The site continues to work at its Pages URL until the user buys the domain
and configures DNS. Domain registration/renewal is separate from free hosting.

After registering it:

1. In GitHub account **Settings → Pages**, add and verify `carterflayhart.com`
   using GitHub's generated TXT verification record. This protects against takeover.
2. In this repository **Settings → Pages → Custom domain**, save
   `carterflayhart.com` **before** pointing DNS to GitHub.
3. At the registrar/DNS provider, add these apex records:

   | Type | Host | Value |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | 01cflayhart.github.io |

   Do not include the repository path in the CNAME value. Do not add wildcard DNS.
   Preserve unrelated email/TXT records; only remove conflicting web records.
4. After DNS validation and GitHub's certificate issuance, enable **Enforce HTTPS**.
   DNS/certificate changes can take up to 24 hours. Verify apex and www redirects.

All internal site links/assets use relative paths and work both under the Pages
repository prefix and at the custom-domain root. With Actions publishing, GitHub's
custom-domain setting controls routing; a committed CNAME file is not required.

Reference: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site

## Current results and official rankings

`current-source.json` specifies Valuebetennis's explicitly CC BY 4.0 CSV downloads.
Attribution: **Valuebetennis, Résultats et cotes de tennis depuis 2021**,
https://www.valuebetennis.com/donnees.htm . No betting odds are used in ratings.

`tennis/current.py` imports 2024 onward and rebuilds independently for each tour.
Identity namespaces are `valuebetennis:ATP:…` and `valuebetennis:WTA:…`. They are
never joined to Sackmann IDs by names. Official ranks/points, birthdays, countries
and images are absent from this CSV. No invented metadata or stale archive ranks
are presented as current. Historical **power** categories are computed normally.

Current ATP rankings reference supplied by the user:
https://www.atptour.com/en/rankings/singles . Reviewed 2026-11-04; the site shows
the weekly edition 2026-11-02. ATP terms §3 restrict public republication and §7
requires written permission for systematic data/ranking retrieval. No scheduled
ATP scraper, embedded ranking table, or permission bypass is included. A permitted
official-rank integration and reviewed cross-provider identity mappings remain
necessary before those columns can be populated from ATP. Same restriction should
be checked separately for WTA. This is not legal advice or a claim of ATP approval.

The free CSV has substantial missing and partial scores and does not guarantee
exhaustive coverage. Import excludes unplayed/unknown/incomplete outcomes rather
than inventing set scores or guessing retirements. The per-tour audit ledger shows
exclusions, source checksums and accepted coverage. The last accepted WTA match
may predate the day the feed was checked. Source round codes are not reinterpreted
as known qualifying rounds. Power ratings are experimental estimates of the
**covered** matches, not definitive full-tour standings.
