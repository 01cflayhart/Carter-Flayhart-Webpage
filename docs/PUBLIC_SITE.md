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

## Requested free URL: CarterFlayhart.github.io

GitHub Pages reserves `<owner>.github.io` for that GitHub account/organization.
Changing a repository name or adding a CNAME cannot give `01cflayhart` the owner
hostname `CarterFlayhart.github.io`. No existing public account/organization with
that name was found on 5 November 2026; availability is ultimately checked by GitHub.

The least disruptive path is to create a **free organization** named
`CarterFlayhart` at https://github.com/organizations/plan, owned by the existing
account. Then publish a public repository named `CarterFlayhart.github.io` in that
organization with Pages enabled. Creation/account terms must be completed by the
user. Do not rename the personal account, transfer this repository, duplicate
automation, or claim the new URL is live without an explicit hosting decision.
The current URL stays live meanwhile. Relative links support either location.

## Optional future custom domain (not the current free-URL request)

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

The user selected https://tennis.one/ranking for both tours. Daily workflow
`website-data.yml` reads its unauthenticated public ranking-page feed and verifies
new cross-provider IDs against public profile birth-date or country/tour facts.
No name-only joins, private history endpoints or copied headshots are used. Source
terms are separate from the CSV's CC BY license; no claim of ATP approval is made.
Current ranks enter a bounded publication-time prior; they never relabel historical
opponents. TennisONE has no edition date, so observation dates are labelled honestly.
See METHODOLOGY.md and DATA_SOURCES.md for exact weighting and validation.

The free CSV has substantial missing and partial scores and does not guarantee
exhaustive coverage. Import excludes unplayed/unknown/incomplete outcomes rather
than inventing set scores or guessing retirements. The per-tour audit ledger shows
exclusions, source checksums and accepted coverage. The last accepted WTA match
may predate the day the feed was checked. Round codes 0–3 are qualifying (codes
1/3/4 checked against public match-page labels). Power ratings are estimates of the
**covered** matches, not definitive full-tour standings.
