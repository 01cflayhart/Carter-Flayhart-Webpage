# Remaining website launch steps

**Start with Step 1 below: create the GitHub OAuth application.**

The website is live at <https://carterflayhart.pages.dev>. GitHub Actions authorization, database migrations and the actual Cloudflare deployment are [verified successful](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/runs/42301895318). A cryptographically random `SESSION_SECRET` has also been generated and stored directly in Cloudflare Pages without displaying its value or saving it locally.

**Do not recreate tokens, hosting or databases, generate another session secret, or repeat the earlier configuration/push steps.** Keep the existing GitHub Pages hosting in place. This guide contains only remaining work:

- [ ] 1. Create the GitHub OAuth app and enable your owner dashboard.
- [ ] 2. Optionally enable feedback-form email delivery.
- [ ] 3. Complete the owner-access, tracking-preference and delivery checks.
- [ ] 4. Submit the live website to Google and Bing.
- [ ] 5. Optionally connect sportsbook prices. Validated prediction models remain separate work.

**Security:** do not paste tokens, Client Secrets or session cookies into chat. Put credentials only in the specific Cloudflare prompt or GitHub secret field below. No paid plan, purchased domain or Global API Key is required.

## 1. Enable your owner-only dashboard

Only **two new values** are needed: the GitHub OAuth **Client ID** and **Client Secret**. The session secret, owner ID and production origin are already configured. You must create/authorize the OAuth application yourself.

### 1A. Create the OAuth application — web browser

1. Sign into GitHub as **01cflayhart**.
2. Open <https://github.com/settings/developers>.
3. Select **OAuth Apps**. Do not select **GitHub Apps**.
4. Click **New OAuth App**. GitHub may ask you to confirm your identity.
5. Enter these exact values:
   - **Application name:** `Carter website owner login`
   - **Homepage URL:** `https://carterflayhart.pages.dev`
   - **Application description:** optional; you can leave it blank.
   - **Authorization callback URL:** `https://carterflayhart.pages.dev/api/auth/callback`
   - **Enable Device Flow:** leave unchecked.
6. Click **Register application**.
7. On the application's page, locate the **Client ID**. Keep the page open; you will copy that value into the first terminal prompt below. This is not the application's numeric ID or the Cloudflare account ID.
8. Click **Generate a new client secret** and complete any identity confirmation. Keep the new **Client Secret** private; GitHub normally displays its value only once.

### 1B. Store those two values — Ubuntu/WSL terminal

Open the same **Ubuntu/WSL terminal** used for the earlier commands. These commands go in that terminal, not the browser's address bar or a GitHub web form.

First enter:

```bash
cd /mnt/c/Users/Carte/Website
```

Then run this command **by itself**:

```bash
npx --yes wrangler@4.158.0 pages secret put GITHUB_CLIENT_ID --project-name carterflayhart
```

When Wrangler asks for the secret value, paste the OAuth application's **Client ID**, then press Enter. The prompt may hide what you type. Wait for the success confirmation.

Next run:

```bash
npx --yes wrangler@4.158.0 pages secret put GITHUB_CLIENT_SECRET --project-name carterflayhart
```

At that prompt, paste the OAuth **Client Secret**, then press Enter and wait for success.

Do not include extra quotes, `Bearer `, or the field name when pasting either value. These are **Cloudflare Pages runtime secrets**, not GitHub Actions repository secrets. **Do not change `SESSION_SECRET`: it has already been created securely for you.**

### 1C. Deploy the new settings and sign in — web browser

1. Open the installed workflow directly:

   <https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/cloudflare.yml>

2. Click **Run workflow** → select **Branch: main** → click **Run workflow** in that menu. Changing a Cloudflare runtime secret alone is not a substitute for this redeployment.
3. Open the newest run and wait for **Deploy static assets and protected Pages Functions** to succeed. A skipped deployment is not enough.
4. Open <https://carterflayhart.pages.dev/private>.
5. Choose GitHub sign-in and authorize the application while signed into GitHub as **01cflayhart**. Complete the browser authorization yourself.
6. Confirm the owner dashboard appears. In **Setup checks**, owner sign-in and the database should be configured. An email warning is expected until optional Step 2 is complete.

Use the exact production hostname above, not a `*.carterflayhart.pages.dev` preview URL. Preview login is intentionally blocked. If GitHub reports a callback mismatch, compare the OAuth app's callback field with the exact URL in Step 1A; do not create a second deployment project.

**Done when:** your GitHub account can sign in and see the private dashboard. The agent can check secret names and deployment logs afterward without reading or receiving your secret values.

## 2. Optional: enable feedback-form email delivery

**You can skip this.** The direct email link works without an email provider. Skipping keeps that fallback; it does not enable server-sent form messages.

### 2A. Create the sender — web browser

1. Create/sign into a free Resend account using **carter.flayhart@gmail.com**, the website's fixed feedback recipient. Verify the account email.
2. Check Resend's current sandbox restrictions: its test sender must be permitted to send to that verified address. Do not buy a domain or plan for this guide; `pages.dev` is not an email domain you own.
3. Create an API key with sending access. Keep it private.
4. Use sender `Carter Website <onboarding@resend.dev>` **only if Resend permits that sender and recipient for your account**. If it does not, stop and keep the direct email fallback rather than inventing a sender.

### 2B. Save the sender values — Ubuntu/WSL terminal

First enter:

```bash
cd /mnt/c/Users/Carte/Website
```

Then run:

```bash
npx --yes wrangler@4.158.0 pages secret put RESEND_API_KEY --project-name carterflayhart
```

Paste the Resend API key only at that command's secret prompt and wait for success. Next run:

```bash
npx --yes wrangler@4.158.0 pages secret put FEEDBACK_FROM --project-name carterflayhart
```

Paste the complete permitted sender string at that prompt and wait for success.

### 2C. Redeploy and confirm actual delivery — web browser

1. Run the Cloudflare deployment workflow from Step 1C again and wait for an actual successful deployment. If you entered the OAuth and email values together, one redeployment after all values are saved is sufficient.
2. Open the sports hub and submit one recognizable test message through its feedback form.
3. Confirm it arrives at **carter.flayhart@gmail.com**, including checking spam.

**Done when:** the message actually arrives. A configured sender or successful form response does not prove inbox delivery. If delivery fails, use the direct email link; the form preserves your text for retrying.

## 3. Complete the owner-feature checks

After enabling login, use your browser to check the final configured state:

- [ ] Signed in as 01cflayhart, `/private` displays separate daily **professional** and **sports** view counts.
- [ ] Leave **Exclude my activity** checked, visit both areas and confirm your own visits are excluded. Uncheck it and test inclusion. DNT or Global Privacy Control can still suppress tracking; these are coarse page-view totals, not unique-visitor counts.
- [ ] Sign out. Private data becomes inaccessible, and this browser's exclusion preference remains in effect.
- [ ] In an incognito/signed-out window, <https://carterflayhart.pages.dev/api/owner/stats> and <https://carterflayhart.pages.dev/api/owner/setup> return **401** without private data. These checks already passed before login configuration; repeat them after the new settings are deployed. `/private` should show only a login screen.
- [ ] If you enabled email, complete the actual inbox test in Step 2C. If not, verify the direct email link instead.

Do not share session cookies or private dashboard data publicly. Keep the original GitHub Pages hosting until the transition is fully verified; this guide does not instruct deleting or redirecting it.

## 4. Submit the live site to Google and Bing

**Where:** browser; one downloaded verification file must also be added to the repository. Account sign-in and site ownership verification require you.

### Google Search Console

1. Open <https://search.google.com/search-console> and sign into your Google account.
2. Choose **Add property → URL prefix**. Do not choose a DNS/Domain property for `pages.dev`.
3. Enter `https://carterflayhart.pages.dev/`.
4. Choose **HTML file** verification and download Google's verification file.
5. Place it **unchanged** in `/mnt/c/Users/Carte/Website/site/`. Do not place it in `_site/`, which is generated. You can supply this non-secret verification file to the agent and ask it to add/commit/push it for you.
6. Wait for a successful Cloudflare deployment. Open `https://carterflayhart.pages.dev/` followed by the exact downloaded filename and confirm it is accessible.
7. Return to Search Console and click **Verify**. Keep the file in the repository afterward.
8. In **Sitemaps**, submit `https://carterflayhart.pages.dev/sitemap.xml`.
9. Use **URL inspection** for the home page and request indexing if offered. Link the new website from your GitHub and academic profiles.

### Bing Webmaster Tools

1. Open <https://www.bing.com/webmasters/> and sign in.
2. Import the verified Google Search Console site if offered, or add the same site using Bing's HTML-file verification method.
3. If using a file, follow the same `site/` → commit/push → successful deployment → verification sequence.
4. Submit the same sitemap URL.

**Done when:** ownership is verified and the sitemap is submitted. Search indexing takes time; a first-place result is not guaranteed.

## 5. Optional: connect sportsbook prices, not validated predictions

1. Create a free account at <https://the-odds-api.com/> and obtain an API key.
2. In [GitHub repository secrets](https://github.com/01cflayhart/Carter-Flayhart-Webpage/settings/secrets/actions), choose **New repository secret**:
   - **Name:** `ODDS_API_KEY`
   - **Secret:** your odds-provider API key.
3. Open <https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/sports-analysis.yml>.
4. Select **Run workflow → main → Run workflow**.
5. Confirm that workflow and its subsequent Cloudflare deployment succeed. Inspect the sports pages for current coverage or a transparent missing-data notice.

Available DraftKings/FanDuel moneylines appear under **Market coverage · not forecasts**. Six credits per run are budgeted; manual runs also consume quota. Coverage is partial. Fanatics/Caesars are not on the documented free tier; do not enable paid sources unless you explicitly choose to do so yourself. No bets are placed.

**An odds key does not finish the prediction models.** Prop Hunt picks and Upset Alert probability categories still require validated independent model/evidence and settlement feeds. That is additional data/model engineering, not another account checkbox for you. Leave `SPORTS_INPUT_URL` and related optional feed secrets unset until a verified source exists. Do not substitute implied odds for independent probabilities or invent picks to fill an empty board. Technical requirements remain in [sports-operations.md](sports-operations.md).
