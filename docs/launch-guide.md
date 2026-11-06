# Remaining launch steps: profile link, Google follow-up and Bing

**Next manual action: add the website to your GitHub profile using Step 1 below. Then continue with Bing; Google's indexing-request quota does not block that work. No terminal commands or Git push are needed from you.**

The agent rechecked the live Google verification file (exact URL, unchanged bytes, HTTP 200), sitemap XML, sitemap declaration in `robots.txt`, and home-page canonical/indexability directives. These checks pass. **Carter has confirmed actual receipt of the feedback test email.** Do not repeat email setup or send another test just for this guide.

You report that Google's **Test live URL** succeeded. Your **Request indexing** attempt was rejected because of the daily quota, so an accepted manual indexing request has **not** been verified. This is not a deployment failure. Your private Search Console ownership and sitemap-submission statuses are not readable through the agent's current connection; the public file alone is not proof of Google's account-side verification. Step 2 describes the one-time status confirmation and quota follow-up, not a repeat of setup.

**Keep the existing Google verification file and its exact-URL handler permanently. Do not recreate properties, tokens, OAuth applications, hosting, databases or email keys. Keep the original GitHub Pages hosting during the transition.** The Resend sender remains a sandbox/test sender restricted to your own account email; inbox receipt does not establish approval for ongoing production use. The free [direct email fallback](mailto:carter.flayhart@gmail.com?subject=Sports%20Analysis%20Hub%20feedback) remains available.

Remaining work:

- [ ] 1. Add the website to your GitHub profile.
- [ ] 2. Confirm Google's existing ownership/sitemap status; retry the optional indexing request later only if needed.
- [ ] 3. Add/import the site into Bing and submit the sitemap.
- [ ] 4. Optionally connect sportsbook prices. Validated prediction models remain separate work.

## 1. Add the website to your GitHub profile — web browser

The authenticated GitHub API currently reports your profile website field as empty. The agent attempted to update only that field, but GitHub refused because the existing authorization does not include profile-edit permission. **No profile changes were made.** There is no need to broaden CLI permissions or create a new token for this one field.

1. Open **[GitHub → Public profile settings](https://github.com/settings/profile)** while signed in as **01cflayhart**.
2. Find the profile **URL / Website** field. This is the website link associated with your public profile, not a repository URL or a social-account field. Scroll down if necessary.
3. Paste exactly:

   ```text
   https://carterflayhart.pages.dev
   ```

4. Click **Update profile** or the profile-save button on that page. Leave all other profile details unchanged.
5. Open **[your public GitHub profile](https://github.com/01cflayhart)**. Refresh if needed, find the website link under your profile information, and click it to confirm it opens the website.

**Done when:** the link is visible on the public profile and opens the production website. Tell the agent once saved; it can independently confirm the public profile/API value afterward. If the settings page differs, share only the field labels or a cropped screenshot of the non-secret profile form. Do not change account-security settings.

You can also link the site from academic profiles you control. Those edits are optional and require your choice; the agent has not modified them.

## 2. Google: confirm existing status and handle the indexing quota

### 2A. Confirm the account-side statuses once — do not redo completed setup

The public prerequisites pass. To confirm the Google-account portion that the agent cannot inspect:

1. Open **[Search Console for this property](https://search.google.com/search-console?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)**, signed into the same Google account used for verification. Confirm the top-left property is **`https://carterflayhart.pages.dev/`**.
2. Open **[Settings → Ownership verification](https://search.google.com/search-console/ownership?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)** and confirm it reports that you are a verified owner. If you already saw **Ownership verified**, do not click Verify again or download another file. The [existing verification URL](https://carterflayhart.pages.dev/google5f578c920a2f92ee.html) is still accessible and unchanged.
3. Open **[Indexing → Sitemaps](https://search.google.com/search-console/sitemaps?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)**. Confirm **`https://carterflayhart.pages.dev/sitemap.xml`** appears under submitted sitemaps:
   - **Success:** submission is confirmed; do not submit it again.
   - **Pending / processing:** leave it in place and check later; do not duplicate it.
   - **No entry:** submit `sitemap.xml` if the form already supplies the website prefix, or the complete URL if it asks for a full URL. Click **Submit** once.
   - **Couldn't fetch / another error:** share the exact status/error with the agent. The [public sitemap](https://carterflayhart.pages.dev/sitemap.xml) has passed the live checks, but that does not prove Google has fetched it successfully. Do not remove/recreate the property to troubleshoot this.
4. Tell the agent the **ownership status** and **sitemap status**, or supply a cropped screenshot containing those labels and the property URL. Do not send passwords, authorization codes or cookies. This is enough to close out the account-side confirmation; no repeat of the live-URL test is required.

### 2B. Indexing-request quota — wait, do not rebuild anything

Your successful **Test live URL** checks current accessibility; it does not mean the page is already indexed. The subsequent daily-quota message means the manual request was not accepted at that time.

1. **Stop retrying for now.** Google's [official recrawl guidance](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl) states that individual indexing requests have a quota and repeated requests do not speed crawling. There is no guaranteed reset time or indexing deadline in these instructions.
2. Keep the valid sitemap and public profile link in place. **An accepted manual request is not required for normal discovery/crawling.** You can proceed to Bing now; waiting for this quota is not a launch blocker.
3. On a later day, open **[Search Console](https://search.google.com/search-console?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)**. In the top **Inspect any URL** field, paste **`https://carterflayhart.pages.dev/`** and press Enter.
4. If it says **URL is on Google**, no indexing request is needed. Otherwise, select **Request indexing** once if available. There is no need to repeat a successful live test unless Google reports a new accessibility issue.
5. If the quota is still exceeded, leave the sitemap submitted and allow normal discovery; check the indexing report later. Do not create alternate properties/accounts or new API tokens to try to bypass the quota. Do not repeatedly press the button.

**Done for launch:** ownership is verified and the sitemap is submitted. A future accepted request or confirmed indexing can be recorded later; waiting for Google is not another setup task you must solve. Crawling/indexing can take days or weeks, inclusion is not guaranteed, and a first-place search result cannot be promised.

## 3. Add the site to Bing — web browser

You have not started this section yet. It is independent of Google's indexing-request quota.

1. Open **[Bing Webmaster Tools](https://www.bing.com/webmasters/)** and sign in with your chosen account.
2. If offered, choose **Import from Google Search Console**. Complete Google's authorization yourself, select **`https://carterflayhart.pages.dev/`**, and finish the import. Google ownership must be verified; an accepted Google indexing request is **not** required.
3. If import is unavailable or you prefer not to authorize it, choose **Add site** / manual addition and enter **`https://carterflayhart.pages.dev/`**.
4. For manual verification, choose Bing's **XML file** method and download **`BingSiteAuth.xml`** (or the exact filename Bing gives you). Leave it unchanged in Downloads and tell the agent where it is. The agent can copy, commit, publish and check it. **Do not press Verify until the agent confirms the file is publicly accessible.** Then return to Bing and click **Verify**. Do not add DNS records for `pages.dev` or any domain you do not own.
5. Select the verified site in Bing. Open **Sitemaps** in its sidebar, click **Submit sitemap**, and enter **`https://carterflayhart.pages.dev/sitemap.xml`**. If import already added it successfully, do not duplicate it.
6. If Bing offers **URL submission** or an indexing request, submit **`https://carterflayhart.pages.dev/`** once. Bing indexing can also take time.

**Done when:** Bing recognizes you as a verified owner and lists the sitemap. Account sign-in, Google-import consent and clicking Verify require you; the agent can handle any supplied public verification file and website-side troubleshooting.

## 4. Optional: connect sportsbook prices, not validated predictions

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
