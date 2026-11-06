# Remaining launch steps: finish search verification

**Your next manual action is clicking Verify in Google Search Console. No file moving, terminal commands or Git push is needed from you.**

The agent copied `google5f578c920a2f92ee.html` byte-for-byte from Downloads into `site/`, leaving the original intact, and is handling publication. Your verification URL is:

**<https://carterflayhart.pages.dev/google5f578c920a2f92ee.html>**

Login/email settings and the actual deployment have been checked. The live sign-in redirect is correct, anonymous owner APIs return 401, and one real feedback test was accepted by the website and Resend. **That proves provider acceptance, not inbox arrival.** Your reported owner-dashboard, exclusion/sign-out and inbox checks cannot be independently inspected from the agent's separate browser/session. If you completed them as reported, do not repeat them. If not, confirm using the [owner dashboard](https://carterflayhart.pages.dev/private), [Gmail](https://mail.google.com/mail/u/0/#inbox) for **carter.flayhart@gmail.com**, and [Resend email logs](https://resend.com/emails). The new test message begins `Launch verification by Carter website assistant`.

**Do not recreate tokens, OAuth apps, databases or email keys. Do not change the session secret or delete the original GitHub Pages hosting.** The Resend sender remains a sandbox/test sender restricted to your own account email; provider acceptance is not production-sender approval. Keep the [direct email fallback](mailto:carter.flayhart@gmail.com?subject=Sports%20Analysis%20Hub%20feedback) if the provider does not permit the intended ongoing use. No purchase is required by this guide.

Remaining work:

- [ ] 1. Click Verify in Google Search Console.
- [ ] 2. Submit the sitemap and request Google indexing.
- [ ] 3. Add/import the site into Bing and submit the sitemap.
- [ ] 4. Optionally connect sportsbook prices. Prediction models remain separate work.

## 1. Finish Google ownership verification — web browser

1. Return to the **Google Search Console tab that gave you the downloaded HTML file**. Stay signed into the same Google account that downloaded it.
2. If you closed that tab, open **[Search Console for this website](https://search.google.com/search-console?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)**. In the top-left property selector, choose **`https://carterflayhart.pages.dev/`**. Do not choose the old GitHub Pages site or a Domain property for `pages.dev`.
3. If the verification panel is not already open, choose the unverified property or open **[Ownership verification](https://search.google.com/search-console/ownership?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)**. Select the **HTML file** method. Do not download or generate a replacement file unless Google explicitly gives you a different filename for this account/property.
4. The file to verify is **[google5f578c920a2f92ee.html](https://carterflayhart.pages.dev/google5f578c920a2f92ee.html)**. It should show exactly:

   ```text
   google-site-verification: google5f578c920a2f92ee.html
   ```

   If publication is still finishing and the URL returns 404, wait for the newest **[Cloudflare deployment](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/cloudflare.yml)** to complete, then refresh. The agent is handling this deployment; do not copy the file again or change its contents.
5. In Google's verification panel, click **Verify**.
6. Wait for **Ownership verified**, then click **Go to property** if offered.

**Done when:** Google confirms ownership. Publishing the file alone does not complete that account-side step. Keep `site/google5f578c920a2f92ee.html` permanently in the repository; Google rechecks it. Do not delete it after verification.

If Google rejects verification, share the error text and the filename Google expects, not account passwords or cookies. Confirm the Google account and exact URL-prefix property before changing anything. [Official verification help](https://support.google.com/webmasters/answer/9008080).

## 2. Submit the sitemap and request indexing — web browser

### 2A. Submit the sitemap

1. Open **[Search Console for this website](https://search.google.com/search-console?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)** after ownership is verified.
2. Confirm the top-left property is **`https://carterflayhart.pages.dev/`**.
3. In the left sidebar, select **Sitemaps** (usually under **Indexing**). A direct link is **[this property's Sitemaps page](https://search.google.com/search-console/sitemaps?resource_id=https%3A%2F%2Fcarterflayhart.pages.dev%2F)**.
4. Under **Add a new sitemap**:
   - If the site prefix is already printed before the input, type **`sitemap.xml`** only.
   - If the input asks for a complete URL, paste **`https://carterflayhart.pages.dev/sitemap.xml`**.
5. Click **Submit**. Confirm it appears under submitted sitemaps. It may be Pending before Google reports Success.
6. You can inspect the published **[sitemap XML](https://carterflayhart.pages.dev/sitemap.xml)** without signing in.

### 2B. Request indexing of the home page

1. In Search Console's top **Inspect any URL** field, paste **`https://carterflayhart.pages.dev/`** and press Enter.
2. Wait for the inspection result. A new site's **URL is not on Google** result is not itself an installation failure.
3. Select **Test live URL** if offered, then **Request indexing** when available. If the URL is already indexed, no repeated request is needed.
4. Google may take days or longer to crawl/index the site. Do not repeatedly submit the same request; first-place search ranking is not guaranteed.
5. If not already done, link the website from your **[GitHub profile](https://github.com/01cflayhart)** and academic profiles. Profile edits require your choice/permission; the agent has not changed them.

**Done when:** the sitemap is submitted and the home-page indexing request is accepted, or the page is already indexed. Search results/data can remain empty initially.

## 3. Add the site to Bing — web browser

1. Open **[Bing Webmaster Tools](https://www.bing.com/webmasters/)** and sign in with your chosen account.
2. If offered, choose **Import from Google Search Console**. Complete the Google account authorization yourself, select **`https://carterflayhart.pages.dev/`**, and finish the import. This is easiest after Step 1 succeeds.
3. If import is unavailable or you prefer not to authorize it, choose **Add site** / manual addition and enter **`https://carterflayhart.pages.dev/`**.
4. For manual verification, choose Bing's **XML file** method and download **`BingSiteAuth.xml`** (or the exact filename Bing gives you). Leave it unchanged in Downloads and tell the agent where it is; the agent can copy, commit, publish and check it, just as for the Google file. **Do not press Verify until the file is publicly accessible.** Then return to Bing and click **Verify**. Do not add DNS records for a domain you do not own.
5. Select the verified site in Bing. Open **Sitemaps** in its sidebar, click **Submit sitemap**, and enter **`https://carterflayhart.pages.dev/sitemap.xml`**. If import already added the sitemap successfully, do not duplicate it.
6. If Bing offers **URL submission** or an indexing request, submit **`https://carterflayhart.pages.dev/`** once.

**Done when:** Bing recognizes you as a verified owner and lists the sitemap. Bing sign-in, Google import consent and account-side verification require you; the agent can handle any downloaded public verification file.

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
