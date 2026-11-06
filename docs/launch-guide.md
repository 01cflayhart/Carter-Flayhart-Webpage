# Remaining launch steps: monitor sitemap processing

**No further required setup action is needed right now. Do not submit either sitemap again today or request indexing again. Your remaining search work is to check the existing sitemap reports later, and report persistent errors.**

Google ownership, home-page indexing, feedback inbox delivery and the GitHub profile link are confirmed. You also confirmed Bing verification, Bing's **Indexed successfully** result for the home page, successful Google live fetch of `sitemap.xml`, and Google's **Sitemap submitted successfully** notification. Bing's sitemap is currently **Processing**; Google's existing report still says **Couldn't fetch**. Neither report has yet been confirmed as processed successfully. The agent cannot directly inspect your private Google/Bing reports, so their account-side statuses are based on your confirmations.

The agent rechecked the public home page, sitemap, robots file and both verification files after your latest report. They are accessible directly with HTTP 200; verification bytes are unchanged, the XML/namespace and five canonical sitemap URLs validate, and Googlebot/Bingbot are allowed by `robots.txt`. The latest deployment checked successfully. **No current website-side fetch/format defect has been identified; Google's original fetch failure has not been explained or proven fixed.** No speculative hosting, XML or security changes were made.

**Keep** `site/google5f578c920a2f92ee.html`, `site/BingSiteAuth.xml` and the Google exact-URL handler published permanently. Do not recreate properties, verification files, API tokens, OAuth apps, hosting, databases or email keys. Retain the original GitHub Pages hosting during the transition. No file copying, terminal commands or Git push are needed from you. The Resend sender remains a sandbox/test sender; delivered test mail does not establish production-sender approval. The free [direct email fallback](mailto:carter.flayhart@gmail.com?subject=Sports%20Analysis%20Hub%20feedback) remains available.

Remaining work:

- [ ] 1. Check Google's existing sitemap report later for Success or a persistent error.
- [ ] 2. Check Bing's existing sitemap report after Processing finishes.
- [ ] 3. Optional: connect sportsbook prices. Validated prediction models remain separate engineering work.

## 1. Google: monitor the submitted sitemap, do not repeat setup

### What your results mean

- **Page fetch → Successful** in the sitemap's live test means Google's inspection tool could retrieve that XML at test time. This completed the diagnostic test; do not repeat it just to follow this guide.
- **Sitemap submitted successfully** means Google accepted the submission. It does **not** mean Google's sitemap fetch/processing completed successfully.
- **Couldn't fetch** in the report is still an unresolved recorded result. It may describe an earlier attempt until the report updates, but that cannot be confirmed without its timestamps/new result. A successful live test does not guarantee the separate sitemap fetch has succeeded.
- **Sitemap could not be read** does not have to be an expandable control. You already confirmed there are no further details; do not keep trying to click it.
- The home page already reports **URL is on Google**. Its indexing and the sitemap report are separate. No more Request indexing attempts are needed, including for the XML itself.

### Your only remaining Google actions

1. Leave the current submission in place. Check **[Google Search Console → Sitemaps](https://search.google.com/search-console/sitemaps?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)** later/tomorrow, rather than repeatedly submitting or refreshing today. Select property **`https://carterflayhart.pages.dev/`** and open the existing `sitemap.xml` row.
2. If the status is **Success**, this task is done. Tell the agent; do not submit it again.
3. If it is pending/processing, leave it alone and check later.
4. If it remains **Couldn't fetch**, record the **Submitted** and **Last read** values, including if Last read is blank. If those labels are unavailable, say so. A cropped screenshot of the whole sitemap details panel is more useful than another copy of the public XML.
5. If it persists for the next few days, or the report shows a new failed read after your successful live test/resubmission, share that screenshot/timestamps with the agent. Share any new explicit HTTP/error code immediately. The agent can recheck the site and narrow the next troubleshooting step using the new evidence.

Google's [official sitemap report documentation](https://support.google.com/webmasters/answer/7451001#fetch_errors) says failed fetches can be retried over a few days and transient errors can occur. **This is not a guaranteed reset time or proof that the current failure is only a delay.** Do not delete the property, rename the working sitemap, disable security controls, create alternate accounts or repeatedly resubmit to try to force a result.

Your [public sitemap](https://carterflayhart.pages.dev/sitemap.xml) is also declared in [robots.txt](https://carterflayhart.pages.dev/robots.txt), so discovery is not limited to the manual report. A browser's “no style information” XML message is normal and needs no fix.

**Done when:** the existing Google sitemap report says **Success**. The already-indexed home page does not need more setup while this is pending.

## 2. Bing: let the existing sitemap finish Processing

### What your results mean

- **Successful Verify:** ownership setup is complete based on your confirmation. You do not need another ownership badge or a repeat of Verify to follow this guide.
- **URL Inspection → Indexed successfully / URL can appear on Bing:** Bing's index report says the inspected home page is indexed and eligible to appear. This does not promise appearance for every search or any particular ranking.
- **Live URL → URL can be indexed by Bing:** this checks the current page's crawl/index eligibility. Its generic conditional wording does not undo the index report. Index status and the live check answer different questions; the two positive results are compatible. See Bing's [official URL Inspection explanation](https://www.bing.com/webmasters/help/url-inspection-55a30305).
- **Sitemap → Processing:** Bing has not finished processing the submitted sitemap. This is pending, not a reported fetch failure and not a request for you to submit it again.
- **No Submit URLs tab:** no action is required. That optional step is no longer relevant because the home page is already reported indexed. Do not hunt for a missing tab or create a new site entry.

### Your only remaining Bing actions

1. Open **[Bing Webmaster Tools](https://www.bing.com/webmasters/)** later/tomorrow. Select the already-verified **`https://carterflayhart.pages.dev/`** site and open **Sitemaps** in its sidebar.
2. Find the existing **`https://carterflayhart.pages.dev/sitemap.xml`** submission.
3. If it finishes successfully, this task is done; tell the agent. If still **Processing**, leave it in place and check later. There is no promised processing deadline in these instructions.
4. If it changes to **Failed / Couldn't fetch / another error**, click the sitemap entry if possible and share the exact error, submitted URL and any submitted/last-processed timestamps. A cropped screenshot is fine; do not send passwords, cookies or API keys.
5. If it stays Processing for several days without an update, share the report and timestamps with the agent for further diagnosis. Do not resubmit, re-verify ownership, add the site again or change the XML just to clear a pending status.

**Done when:** Bing's existing sitemap is processed successfully. Ownership and home-page indexing are already confirmed by your reported results. Keep [BingSiteAuth.xml](https://carterflayhart.pages.dev/BingSiteAuth.xml) published afterward. Search results/rankings are not guaranteed by a positive inspection result.

## 3. Optional: connect sportsbook prices, not validated predictions

Skip this if you only want to finish the academic website/search launch. No odds-provider key is currently configured in the repository; this is not a search-launch requirement.

1. Open **[The Odds API](https://the-odds-api.com/)** and use **Get API Key** to sign up for its free plan. Do not choose a paid plan unless you explicitly want one. [Provider documentation](https://the-odds-api.com/liveapi/guides/v4/) explains the key and quota.
2. Open **[New GitHub repository secret](https://github.com/01cflayhart/Carter-Flayhart-Webpage/settings/secrets/actions/new)** and save:
   - **Name:** `ODDS_API_KEY`
   - **Secret:** your odds-provider API key. Do not send its value in chat.
3. Open **[Review and archive sports analysis daily](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/sports-analysis.yml)** → **Run workflow → main → Run workflow**.
4. Confirm it and the following **[Cloudflare deployment](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/cloudflare.yml)** succeed. The agent can trigger/check these after you save the key.
5. Inspect the **[sports hub](https://carterflayhart.pages.dev/sports/)** for current market coverage or a clear missing-data notice.

Available DraftKings/FanDuel moneylines appear under **Market coverage · not forecasts**. Six credits per run are budgeted; manual runs also consume quota. Coverage is partial. Fanatics/Caesars are not on the documented free tier; do not enable paid sources automatically. No bets are placed.

**An odds key does not complete the prediction models.** Prop Hunt picks and Upset Alert probability categories still require validated independent model/evidence and settlement feeds. This is additional engineering, not another account checkbox for you. Leave `SPORTS_INPUT_URL` and related optional feed secrets unset until a verified source exists. Do not substitute implied odds for independent probabilities or invent picks. Technical requirements remain in [sports-operations.md](sports-operations.md).
