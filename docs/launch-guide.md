# Remaining launch steps: Google sitemap fetch and Bing verification

**Your next actions are account-side: test Google's fetch of `sitemap.xml`, then click Verify in Bing. Its XML file is already live and checked; no waiting, file copying, terminal commands or Git push are needed from you.**

Google ownership, home-page indexing, feedback inbox delivery and the GitHub profile link are already confirmed. Do not repeat their setup. Bing import did not offer the site; you have already added it manually and supplied its XML file. The agent copied `BingSiteAuth.xml` unchanged from Downloads into `site/`, preserving the original, committed/pushed it and [deployed it successfully](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/runs/42313475365). Live checks confirmed direct HTTP 200 without login/redirect and byte-for-byte identity with Downloads.

Keep both verification files permanently (`site/google5f578c920a2f92ee.html` and `site/BingSiteAuth.xml`) and the Google exact-URL handler. Do not recreate properties, API tokens, OAuth apps, databases or hosting. Retain the original GitHub Pages hosting during the transition. The Resend sender is still a sandbox/test sender, not proof of approval for ongoing production use; the free [direct email fallback](mailto:carter.flayhart@gmail.com?subject=Sports%20Analysis%20Hub%20feedback) remains available. No further email tests are needed.

Remaining work:

- [ ] 1. Get Google's live sitemap fetch result and resolve its report status.
- [ ] 2. Click Bing Verify, then submit/check its sitemap.
- [ ] 3. Optionally connect sportsbook prices. Validated predictions remain separate engineering work.

## 1. Google: test the sitemap itself, not the home page

### What the browser's XML message means

**“This XML file does not appear to have any style information associated with it” is normal. It is not a fetch error.** Sitemaps are machine-readable XML, not styled web pages. The five URLs you saw are the expected sitemap. Do not add a stylesheet, turn it into HTML, rename it, or change the hosting to remove that browser message.

Your submitted URL is now confirmed as correct: **[https://carterflayhart.pages.dev/sitemap.xml](https://carterflayhart.pages.dev/sitemap.xml)**. The agent rechecked public GET and HEAD: HTTP 200 without redirects, `application/xml`, unchanged valid XML, five unique canonical URLs, and Googlebot access permitted by `robots.txt`. **This proves current public availability—not that Google fetched it successfully.** The cause of Google's earlier **Couldn't fetch** remains unconfirmed.

### 1A. Use Google's live test for this exact XML URL

1. Open **[Search Console for this website](https://search.google.com/search-console?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)**. Confirm the property selector is **`https://carterflayhart.pages.dev/`**.
2. In the top **Inspect any URL** field, paste exactly:

   ```text
   https://carterflayhart.pages.dev/sitemap.xml
   ```

3. Press Enter, then click **Test live URL**. This is a different URL from your already-successful home-page test.
4. Expand **Page availability** / crawl details in the live-test result. Find **Crawl allowed?** and **Page fetch**. Google's [official sitemap troubleshooting instructions](https://support.google.com/webmasters/answer/7451001#fetch_errors) recommend these checks.
5. Tell the agent both values:
   - Expected **Crawl allowed? → Yes**.
   - Expected **Page fetch → Successful**.
   - If either fails, share the exact detailed error/HTTP code or a cropped screenshot. That evidence is needed to choose a fix; a generic **Couldn't fetch** status alone cannot identify the cause.

**Do not click Request indexing for the XML file.** It is not a search-results page. Ignore a general “not indexed” result for the sitemap when troubleshooting its *fetch*; focus on the crawl/fetch details. Your home page already reports **URL is on Google**, so no further home-page indexing requests are needed either.

### 1B. Update the sitemap report only after the fetch test

1. Open **[Search Console → Sitemaps](https://search.google.com/search-console/sitemaps?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)** and click the existing failed sitemap row.
2. **Stay on Google's report page to inspect errors.** **Open Sitemap** only opens the public XML in your browser; it does not display Google's fetch diagnostics or fix its status.
3. Record **Last read** (including if blank) and click/expand **Sitemap could not be read** or the displayed error if the report offers details. If there are no further details, say so; do not hunt for a nonexistent control. A cropped screenshot of that report is useful.
4. If **Page fetch is Successful** in Step 1A and the sitemap report still says **Couldn't fetch**, return to the Sitemaps list and submit the same correct URL **once**:
   - If the site prefix is already printed before the input, type **`sitemap.xml`** only.
   - If it asks for a complete URL, paste **`https://carterflayhart.pages.dev/sitemap.xml`**.
   - Click **Submit**, then allow time for Google's report to update. Do not delete/recreate the property or repeatedly submit the URL.
5. If the report already says **Success**, stop; no resubmission is needed. If Google's live fetch fails, share that failure first rather than resubmitting blindly. If a successful live fetch is followed by continuing report failures, share the error/Last read with the agent.

Google documents transient fetch errors and retry attempts over a few days; that is a possibility, not a proven explanation here. No exact reset/completion time is guaranteed. Do not bypass quotas, disable security controls, or create alternate properties/accounts. **You may complete Bing while Google retries.**

**Done when:** Google's sitemap report says **Success**. Ownership and home-page indexing do not need to be repeated while resolving this separate report.

## 2. Bing: verify the existing manually added site

**Do not retry Google import or add another copy of the site.** You have already completed manual addition. Your supplied file is published and independently checked at:

**[https://carterflayhart.pages.dev/BingSiteAuth.xml](https://carterflayhart.pages.dev/BingSiteAuth.xml)**

### 2A. Click Verify in Bing

1. Return to the Bing tab that provided **BingSiteAuth.xml**. If closed, open **[Bing Webmaster Tools](https://www.bing.com/webmasters/)**, sign into the same account and select the existing **`https://carterflayhart.pages.dev/`** site that still needs verification.
2. Return to its verification panel / XML file verification method if needed. You do not need another download or a new verification method.
3. Open **[BingSiteAuth.xml](https://carterflayhart.pages.dev/BingSiteAuth.xml)**. It is public without login and contains a `<users>` element with a `<user>` verification value. The browser's “no style information” message is also normal here. The agent has checked its bytes against the Downloads original; do not edit it.
4. In **Bing's verification panel**, click **Verify**. Opening the XML itself does not complete the account-side verification.
5. Wait for successful verification / access to the site's dashboard. If Bing fails, share its exact error; do not change DNS for `pages.dev`, replace a working verification file or add the site again.

### 2B. Submit the sitemap and optionally the home page

1. With the verified site selected in **[Bing Webmaster Tools](https://www.bing.com/webmasters/)**, open **Sitemaps** in its sidebar.
2. Click **Submit sitemap** and enter **`https://carterflayhart.pages.dev/sitemap.xml`**. If that exact sitemap is already listed successfully, do not duplicate it.
3. Confirm submission is listed, then check its processing status. If Bing reports a fetch error, share the complete URL and detailed error with the agent. Browser access alone does not confirm Bing's fetch.
4. If Bing offers **URL submission** / **Submit URLs**, submit **`https://carterflayhart.pages.dev/`** once. This is optional; sitemap submission also supports discovery. Indexing can take time and is not guaranteed.
5. Tell the agent the **ownership verification result** and **sitemap status**, or provide a cropped screenshot. The agent cannot inspect your private Bing account through the current connection.

**Done when:** Bing confirms ownership and lists the sitemap successfully. Keep `BingSiteAuth.xml` published afterward; do not delete it once verified.

## 3. Optional: connect sportsbook prices, not validated predictions

Skip this if you only want to finish the academic website/search launch.

1. Open **[The Odds API](https://the-odds-api.com/)** and use **Get API Key** to sign up for its free plan. Do not choose a paid plan unless you explicitly want one. [Provider documentation](https://the-odds-api.com/liveapi/guides/v4/) explains the key and quota.
2. Open **[New GitHub repository secret](https://github.com/01cflayhart/Carter-Flayhart-Webpage/settings/secrets/actions/new)** and save:
   - **Name:** `ODDS_API_KEY`
   - **Secret:** your odds-provider API key. Do not send its value in chat.
3. Open **[Review and archive sports analysis daily](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/sports-analysis.yml)** → **Run workflow → main → Run workflow**.
4. Confirm it and the following **[Cloudflare deployment](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/cloudflare.yml)** succeed. The agent can trigger/check these after you save the key.
5. Inspect the **[sports hub](https://carterflayhart.pages.dev/sports/)** for current market coverage or a clear missing-data notice.

Available DraftKings/FanDuel moneylines appear under **Market coverage · not forecasts**. Six credits per run are budgeted; manual runs also consume quota. Coverage is partial. Fanatics/Caesars are not on the documented free tier; do not enable paid sources automatically. No bets are placed.

**An odds key does not complete the prediction models.** Prop Hunt picks and Upset Alert probability categories still require validated independent model/evidence and settlement feeds. This is additional engineering, not another account checkbox for you. Leave `SPORTS_INPUT_URL` and related optional feed secrets unset until a verified source exists. Do not substitute implied odds for independent probabilities or invent picks. Technical requirements remain in [sports-operations.md](sports-operations.md).
