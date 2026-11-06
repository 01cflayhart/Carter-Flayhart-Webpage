# Remaining launch steps: sitemap follow-up and Bing

**Google ownership and the home page's inclusion in Google are confirmed by Carter. The public GitHub profile now links to the website (independently verified). No further ownership verification, GitHub profile editing or home-page indexing request is needed.**

Your remaining Google issue is the sitemap's **Couldn't fetch** status. It does not mean the already-indexed home page has disappeared from Google. The agent has checked the live sitemap: GET and HEAD return HTTP 200 directly, Content-Type is `application/xml`, its XML/namespace and five canonical URLs are valid, and `robots.txt` permits Googlebot access and advertises the correct sitemap. No website-side fetch/format defect has been identified. Google's exact error details are needed before choosing a fix; a successful request from the agent does not prove Google's fetch succeeded.

**Do not recreate properties, verification files, tokens, OAuth apps, hosting, databases or email keys. Keep the Google verification file and its exact-URL handler permanently, and retain the original GitHub Pages hosting during the transition.** Email receipt is already confirmed; no more feedback tests are needed. The Resend sender is still a sandbox/test sender, not proof of production-sender approval; the free [direct email fallback](mailto:carter.flayhart@gmail.com?subject=Sports%20Analysis%20Hub%20feedback) remains available.

Remaining work:

- [ ] 1. Inspect and resolve Google's sitemap fetch status.
- [ ] 2. Add/import the site into Bing and submit the sitemap. You can do this while Google retries.
- [ ] 3. Optionally connect sportsbook prices. Validated prediction models remain separate engineering work.

No terminal commands or Git push are needed from you for these steps.

## 1. Google: inspect the sitemap fetch failure — web browser

### 1A. Get the exact submitted URL and detailed error

1. Open **[Search Console → Sitemaps for this website](https://search.google.com/search-console/sitemaps?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)**. Confirm the property selector says **`https://carterflayhart.pages.dev/`**.
2. Click the actual sitemap row showing **Couldn't fetch**. Do not stop at the summary table.
3. In the details page, copy the **complete Sitemap URL**. It must be exactly:

   ```text
   https://carterflayhart.pages.dev/sitemap.xml
   ```

   It must not have a trailing slash after `.xml`, a duplicated website prefix, the old GitHub Pages hostname, or an extra folder. The [correct public sitemap](https://carterflayhart.pages.dev/sitemap.xml) is currently accessible without a login.
4. Click/expand **Sitemap could not be read** or the error shown there. Record the detailed reason/HTTP code, if any, and the **Last read** value (including if it is blank).
5. Send the agent the complete submitted URL and expanded error text, or a cropped screenshot of that details section. Do not include passwords, cookies or API keys. The agent cannot inspect this private Google report through the current connection.

If the submitted URL is wrong, add the exact correct URL using **Add a new sitemap** on the report page. If the form already prints the site prefix, enter **`sitemap.xml`** only; otherwise paste the full URL above. Submit once. Do not delete the property or change the actual sitemap file to match a mistyped URL. An obsolete, wrong submission can be removed from the report later without deleting the site/property.

### 1B. Test Google's fetch of the sitemap itself

This is different from the home-page test you already completed. Google's [official sitemap troubleshooting instructions](https://support.google.com/webmasters/answer/7451001#fetch_errors) recommend this check.

1. In Search Console's top **Inspect any URL** field, paste **`https://carterflayhart.pages.dev/sitemap.xml`** and press Enter.
2. Choose **Test live URL**.
3. Expand **Page availability** or the crawl/fetch details. Look specifically for:
   - **Crawl allowed? → Yes**
   - **Page fetch → Successful**
4. If either fails, share the detailed error with the agent. That is stronger diagnostic evidence than the summary **Couldn't fetch** label.
5. If Google's live sitemap fetch succeeds, return to **[Sitemaps](https://search.google.com/search-console/sitemaps?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)**. If it is still failed, submit the exact same correct sitemap URL **once** to ask Google to fetch it again, then allow time for the report to update. If it now says **Success**, stop; do not resubmit.
6. If the report remains failed, share its detailed error and Last read rather than repeatedly resubmitting. Google's documentation says transient fetch errors can occur and it retries failed sitemaps for a few days; the cause here has not been established, so no guaranteed completion/reset time is claimed.

**Do not select Request indexing for `sitemap.xml`.** It is an XML discovery file, not a page that needs to appear in search results. Your home page already reports **URL is on Google**, so it also needs no more manual indexing requests. The earlier request quota is no longer a task to resolve.

**Done when:** the sitemap report says **Success**. You can continue with Bing while this is being diagnosed. Do not disable security controls, create alternate Google accounts/properties, rename the working sitemap, or recreate hosting merely to try to clear this status.

## 2. Add the site to Bing — web browser

You have not started Bing yet. It is independent of the remaining Google sitemap error; verified Google ownership is sufficient for attempting import.

1. Open **[Bing Webmaster Tools](https://www.bing.com/webmasters/)** and sign in with your chosen account.
2. If offered, choose **Import from Google Search Console**. Complete Google's authorization yourself, select **`https://carterflayhart.pages.dev/`**, and finish the import. An additional Google indexing request is not required.
3. If import is unavailable or you prefer not to authorize it, choose **Add site** / manual addition and enter **`https://carterflayhart.pages.dev/`**.
4. For manual verification, choose Bing's **XML file** method and download **`BingSiteAuth.xml`** (or its exact provided filename). Leave it unchanged in Downloads and tell the agent where it is. The agent can copy, commit, publish and check it. **Do not press Verify until the agent confirms the file is public.** Then return to Bing and click **Verify**. Do not add DNS records for `pages.dev` or a domain you do not own.
5. Select the verified site in Bing. Open **Sitemaps** in its sidebar, click **Submit sitemap**, and enter **`https://carterflayhart.pages.dev/sitemap.xml`**. If import already added it successfully, do not duplicate it. If Bing also reports a fetch error, send the exact URL and details to the agent rather than changing the site speculatively.
6. If Bing offers **URL submission** or an indexing request, submit **`https://carterflayhart.pages.dev/`** once. Bing indexing can take time.

**Done when:** Bing recognizes you as a verified owner and lists the sitemap successfully. Sign-in, Google-import consent and account-side verification require you; the agent can handle supplied public verification files and website-side troubleshooting.

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
