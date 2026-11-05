# Personal site content

The personal pages live in `site/index.html` and `site/sports/index.html`.
They use `site/site.css`; `site/site.js` progressively enhances the homepage's
hash links into section switching. With JavaScript disabled, all sections display.
Sports Analysis keeps its existing URL and dashboard/data pipeline.

The profile and content use a muted slate palette with a lightly translucent,
blurred content layer over the COSMOS-Web background, rather than a bright paper
panel. Text, links, and focus indicators retain accessible contrast.

## Profile, CV, and contact

The portrait is Carter's supplied photo, extracted from the publicly shared Google
Doc on 5 November 2026 and resized as `site/assets/carter-flayhart.jpg`. It appears
in both profile headers. Bio, education, research, awards, and the four presentation
summaries were checked against Carter's three-page Overleaf CV (updated 5 November
2026). Talks retain month precision and are newest-first in HTML and JavaScript.
User-supplied hobbies and emails appear in Hobbies and Contact; no phone number
was copied into the contact page.

CV follows Hobbies in navigation, then Contact. CV opens
`site/assets/carter-flayhart-cv.pdf` in a new tab. `scripts/refresh-cv.cjs` reads
the public Overleaf viewer in an ordinary browser, retrieves the compiled PDF,
validates completeness, and replaces it atomically. The **Refresh CV and published
tennis rankings** workflow (`website-data.yml`) checks daily at **08:43 UTC** and
can be run manually. This is a synchronized PDF, not a compile-on-every-click
service: changes appear after a successful sync and deployment. The live Overleaf
document is also linked from About Me. If access or compilation fails, the last
valid PDF remains available. No cookies or temporary compilation URLs are published.

The profile's academic title, institution, and research description use Carter's
provided wording. No email address, publication, or talk was inferred.

## Publications and automatic updates

The Publications tab is generated into `site/index.html` from
`site/publications.json`, a dated snapshot of Carter's SciX author search. It is
readable without JavaScript and requires no browser-side API token.

`publications/update.py` uses the supported ADS/SciX Developer API endpoint,
`https://api.adsabs.harvard.edu/v1/search/query`, and paginates the exact query
`author:"Carter Flayhart"`. It retrieves full author lists, citation counts,
document types, titles, journal information, identifiers, and dates.

- Include only `article` and `eprint` document types. Exclude datasets, observing
  proposals, theses, abstracts, and other non-paper records, even if SciX marks
  them with a broader ARTICLE property.
- Match Carter in the author list; reject truncated author lists or invalid counts.
- Deduplicate connected DOI, arXiv, bibcode, or normalized-title/first-author aliases.
  Prefer the journal record over its preprint and never sum citation counts from
  duplicate records (use the maximum recorded count).
- One paper list, with All papers / First author / Refereed / Non-refereed buttons.
  Refereed status uses SciX's `REFEREED` property, not the mere existence of a DOI.
  Client-side sorting offers citations (default), newest, oldest, and title.
  The non-JavaScript fallback keeps first-author-first and citation ordering.
- Label preprints as not peer reviewed and show the source check date.
- Failed requests or invalid/empty results leave the existing snapshot unchanged.

The initial snapshot was retrieved directly from SciX on 4 November 2026:
19 records, 14 papers. The omitted five were two catalogues, two HST proposals,
and a master's thesis; no first-author article/preprint was in that selection.

The authenticated GitHub updater was tested successfully on 5 November 2026:
19 records fetched, 14 papers selected, snapshot committed, and Pages dispatched
([workflow run](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/runs/42107515300)).
The API token stays in the repository's Actions secrets, never in public assets.
The publication source/date line remains; explanatory introduction and exclusion
notes are intentionally omitted from generated HTML at Carter's request.

### Activate the daily updater

1. Sign in to SciX and generate a Developer API token in the account settings:
   https://scixplorer.org/user/settings/token
   (ADS equivalent: https://ui.adsabs.harvard.edu/user/settings/token).
2. Add a repository Actions secret named **ADS_API_TOKEN**. Never commit the token,
   put it in a public file, or send it to a visitor's browser.
3. Run **Refresh SciX publications** in GitHub Actions (`publications.yml`).

The workflow runs daily at **08:11 UTC** and can also be triggered manually. It
tests the updater, fetches/validates metadata, commits the static snapshot and HTML,
then explicitly dispatches `pages.yml` to publish. The explicit dispatch is
necessary because commits made by GITHUB_TOKEN do not trigger push workflows.
If ADS_API_TOKEN is missing, the workflow logs a warning and leaves the current
list intact; automatic fetching is not active until the secret is configured.

Local refresh (with the token already set in the environment):
`python -m publications.update`

Offline regeneration without modifying the last-check timestamp:
`python -m publications.update --offline`

API documentation: https://github.com/adsabs/adsabs-dev-api

## Astronomy image

`site/assets/cosmos-web.jpg` is ESA/Webb image **potm2504a**, “A visual feast of
galaxies,” released 29 April 2025. The local copy is the 1920×1200 wallpaper:
https://cdn.esawebb.org/archives/images/wallpaper4/potm2504a.jpg

Source: https://esawebb.org/images/potm2504a/
Usage terms: https://esawebb.org/copyright/
License: Creative Commons Attribution 4.0 International.

Full required credit (displayed on both personal pages):
ESA/Webb, NASA & CSA, G. Gozaliasl, A. Koekemoer, M. Franco, and the COSMOS-Web team

The background is cropped and darkened with a CSS overlay. The research section
also displays the wallpaper without that overlay. No third-party fonts, analytics,
or runtime image services are required.
