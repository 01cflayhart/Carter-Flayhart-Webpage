# Remaining website launch steps

**Next optional setup: Step 1, feedback email. No OAuth setup needs to be repeated.**

The [website](https://carterflayhart.pages.dev) and [GitHub Actions deployment](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/runs/42304387785) are working. Cloudflare contains all three login settings. The live sign-in endpoint redirects to GitHub with the exact production callback, state protection and a secure HTTP-only cookie. Anonymous owner APIs still return 401.

This verifies the login **configuration and redirect**, not the final GitHub code exchange or your signed-in dashboard: those require your browser authorization. If you already signed in and saw the dashboard, do not repeat the setup; finish only the checks in Step 2 that you have not done.

**Do not recreate API tokens, OAuth applications, hosting or databases, regenerate the session secret, or repeat the earlier configuration/push steps.** Keep existing GitHub Pages hosting in place. Never send credentials or session cookies in chat.

Remaining work:

- [ ] 1. Optionally create the Resend account/key and verify feedback delivery.
- [ ] 2. Confirm your actual owner sign-in, activity exclusion and sign-out behavior.
- [ ] 3. Verify Google/Bing ownership and submit the sitemap.
- [ ] 4. Optionally connect available sportsbook prices. Validated prediction models remain separate engineering work.

## 1. Optional: enable feedback-form email delivery

You can skip this: the [direct email link](mailto:carter.flayhart@gmail.com?subject=Sports%20Analysis%20Hub%20feedback) already works without an email provider. No paid plan or purchased domain is required to keep that fallback.

The agent has prepared `FEEDBACK_FROM` in Cloudflare as `Carter Website <onboarding@resend.dev>`. **This is a sandbox/test sender, not a verified-domain production sender.** `RESEND_API_KEY` is still missing, so form delivery is not enabled. No test message has been sent on your behalf.

### 1A. Create your Resend account — web browser

1. Open **[Create a Resend account](https://resend.com/signup)**. If you already have an account, use **[Resend sign-in](https://resend.com/login)**.
2. Register with **carter.flayhart@gmail.com**, the website's fixed feedback recipient. If using Google sign-in, explicitly select that Google account rather than your RIT account. If Resend sends an email verification link/code, complete it yourself.
3. Use the **Free transactional-email plan**. Do not enable paid upgrades, overages, marketing tools or a domain purchase for these instructions. [Current pricing and limits](https://resend.com/pricing) list 3,000 emails/month and 100/day on Free; provider limits can change.
4. If onboarding asks for a domain, do not enter `pages.dev`, `rit.edu` or any other domain you do not control. Open the API-key link in Step 1B to see whether you can proceed with a sandbox test. If domain verification is mandatory for your account, stop and keep the direct email fallback rather than purchasing anything.

**Sandbox restriction:** [Resend's documentation](https://resend.com/docs/knowledge-base/403-error-resend-dev-domain) says `onboarding@resend.dev` can send test emails only to the email address associated with your Resend account. That is why the account address must match **carter.flayhart@gmail.com**. This does not establish approval or reliability for an ongoing public production form. A production sender requires following Resend's domain/policy requirements; if that requires a domain you do not already own, keep the free email-link fallback unless you explicitly choose otherwise.

### 1B. Create a sending-only API key — web browser

1. Open **[Resend → API keys](https://resend.com/api-keys)** while signed in.
2. Click **Create API Key**.
3. Name it `Carter website feedback`.
4. For **Permission**, choose **Sending access**, not Full access. [Official key-creation instructions](https://resend.com/docs/create-an-api-key) describe these controls.
5. Domain restriction is optional. For the sandbox test, leave that optional restriction unset; do not select a domain you do not own. If the controls differ or require a verified domain, stop rather than granting unrelated permissions or buying a domain.
6. Create the key and copy its newly displayed value. Resend normally shows it only once. Do not paste it into chat, a source file or a GitHub issue.

### 1C. Store the key — Ubuntu/WSL terminal

Open the **Ubuntu/WSL terminal**, not the browser's address bar. First enter:

```bash
cd /mnt/c/Users/Carte/Website
```

Then run this command by itself:

```bash
npx --yes wrangler@4.158.0 pages secret put RESEND_API_KEY --project-name carterflayhart
```

At the secret-value prompt, paste **only the Resend API key**, then press Enter. Do not add quotes, `Bearer ` or the field name. Wait for the success confirmation. The prompt may hide what you type.

This is a **Cloudflare Pages runtime secret**, not a GitHub repository secret. The sender is already prepared; you do not need another `FEEDBACK_FROM` command for this sandbox test. Do not modify the three GitHub-login/session settings.

### 1D. Redeploy — web browser

1. Open **[Publish to Cloudflare Pages](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/cloudflare.yml)**.
2. Click **Run workflow** → select **Branch: main** → click **Run workflow** in the menu.
3. Open the newest run and wait for **Deploy static assets and protected Pages Functions** to succeed. A skipped deployment is not enough. Changing a runtime secret alone is not a substitute for this redeployment.

No new Git push is needed to save a runtime secret. Alternatively, after saving it, ask the agent to redeploy and check the logs for you; do not send the key.

### 1E. Verify the actual test email — web browser

1. Open **[Sports hub → Help improve the hub](https://carterflayhart.pages.dev/sports/#feedback-title)**.
2. Enter a recognizable message of at least 10 characters, such as `Website feedback delivery test`, and click **Send feedback**. Your email field is optional; it is not the delivery destination.
3. Open **[Gmail inbox](https://mail.google.com/mail/u/0/#inbox)** and confirm you are viewing **carter.flayhart@gmail.com**, not another signed-in account. Check spam too.
4. Open **[Resend → Emails/logs](https://resend.com/emails)** to inspect the message status if needed. A provider's accepted/delivered status does not replace your inbox check.

**Done when:** the sandbox test actually arrives. A configured API key, setup-check badge or successful form response is not proof of inbox arrival or production-sender approval.

If you see a Resend 403 about testing recipients, check that the Resend account email matches the fixed recipient and review the linked sandbox documentation. Do not change the destination to an arbitrary visitor address or invent a sender. If the service does not permit the intended use, keep the direct email fallback. Do not send the agent a key-bearing screenshot; share only the safe error message.

## 2. Confirm your actual owner sign-in and preferences

The configuration/deployment is verified. The agent cannot inspect your private browser session or prove the Client Secret's code exchange from secret names alone. Complete only the following checks you have not already done:

1. Open **[Owner dashboard](https://carterflayhart.pages.dev/private)**. If signed out, select GitHub sign-in and complete authorization as **01cflayhart** yourself.
2. Confirm the dashboard appears and **Setup checks** reports owner sign-in and database configured. An email warning is expected if you skipped Step 1. Tell the agent whether these checks succeeded; do not share your session cookie.
3. Confirm separate daily **professional** and **sports** counts appear. Leave **Exclude my activity** checked, visit the [home page](https://carterflayhart.pages.dev/) and [sports hub](https://carterflayhart.pages.dev/sports/), and confirm your visits are excluded. Uncheck it and test inclusion if desired. DNT/Global Privacy Control may still suppress tracking; counts are page views, not unique people.
4. Sign out. Private data must become inaccessible, while this browser's activity-exclusion preference remains in effect.
5. In an incognito/signed-out window, **[owner statistics API](https://carterflayhart.pages.dev/api/owner/stats)** and **[owner setup API](https://carterflayhart.pages.dev/api/owner/setup)** must return **401** without private data. The agent has verified these anonymous checks; repeat them after testing your authenticated session if needed.

If the actual GitHub sign-in fails, open **[GitHub OAuth app settings](https://github.com/settings/developers)** → **OAuth Apps** → your existing app. Its callback/Redirect URI must be exactly `https://carterflayhart.pages.dev/api/auth/callback`. Use the production hostname, not a preview subdomain. Share only the error text or failed run URL; do not create a replacement app or send credentials without first diagnosing the problem.

Keep the old GitHub Pages hosting until the transition is fully verified. This guide does not instruct deleting or redirecting it.

## 3. Verify search ownership and submit the sitemap

The public canonical URL and sitemap prerequisites have passed automated checks. Signing into Google/Bing and verifying site ownership require you.

### 3A. Google Search Console

1. Open **[Google Search Console](https://search.google.com/search-console)** and sign into your Google account.
2. Choose **Add property → URL prefix**. Do not choose a DNS/Domain property for `pages.dev`.
3. Enter `https://carterflayhart.pages.dev/`.
4. Choose **HTML file** verification and download Google's verification file. [Google's ownership-verification help](https://support.google.com/webmasters/answer/9008080) explains the method if the controls differ.
5. Put the file **unchanged** in `/mnt/c/Users/Carte/Website/site/`. Do not put it in generated `_site/`. You can supply this non-secret verification file to the agent and ask it to add/commit/push it for you.
6. Wait for a successful [Cloudflare deployment](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/cloudflare.yml). Open the website followed by the exact downloaded filename and confirm it is accessible.
7. Return to Search Console and click **Verify**. Keep the verification file in the repository afterward.
8. In **Sitemaps**, submit **[the website sitemap](https://carterflayhart.pages.dev/sitemap.xml)**: `https://carterflayhart.pages.dev/sitemap.xml`.
9. Use **URL inspection** for `https://carterflayhart.pages.dev/` and request indexing if offered. Link the website from your [GitHub profile](https://github.com/01cflayhart) and academic profiles.

### 3B. Bing Webmaster Tools

1. Open **[Bing Webmaster Tools](https://www.bing.com/webmasters/)** and sign in.
2. Import the verified Search Console site if offered, or add `https://carterflayhart.pages.dev/` using Bing's HTML-file verification method.
3. If downloading a file, follow the same `site/` → commit/push → successful deployment → verification sequence. The agent can handle the repository/deployment work after you provide the non-secret file.
4. Submit **[the same sitemap](https://carterflayhart.pages.dev/sitemap.xml)**.

**Done when:** ownership is verified and the sitemap is submitted. Indexing takes time; a first-place search result is not guaranteed.

## 4. Optional: connect sportsbook prices, not validated predictions

1. Open **[The Odds API](https://the-odds-api.com/)** and use its **Get API Key** signup for the free plan. Do not choose a paid subscription unless you explicitly want one. [API documentation](https://the-odds-api.com/liveapi/guides/v4/) explains the key and quota.
2. Open **[New GitHub repository secret](https://github.com/01cflayhart/Carter-Flayhart-Webpage/settings/secrets/actions/new)**:
   - **Name:** `ODDS_API_KEY`
   - **Secret:** the odds-provider API key.
3. Open **[Review and archive sports analysis daily](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/sports-analysis.yml)**.
4. Click **Run workflow → main → Run workflow**.
5. Confirm it and its subsequent [Cloudflare deployment](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/cloudflare.yml) succeed. Inspect the [sports hub](https://carterflayhart.pages.dev/sports/) for current coverage or a clear missing-data notice.

Available DraftKings/FanDuel moneylines appear under **Market coverage · not forecasts**. Six credits per run are budgeted; manual runs also consume quota. Coverage is partial. Fanatics/Caesars are not on the documented free tier; do not enable paid sources automatically. No bets are placed.

**An odds key does not complete the prediction models.** Prop Hunt picks and Upset Alert probability categories still require validated independent model/evidence and settlement feeds. This is additional data/model engineering, not another account checkbox for you. Leave `SPORTS_INPUT_URL` and related optional feed secrets unset until a verified source exists. Do not substitute implied odds for independent probabilities or invent picks. Technical requirements remain in [sports-operations.md](sports-operations.md).
