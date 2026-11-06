# Finish launching Carter’s website

**Start with Step 1. This guide contains only the remaining work.**

The website is already live at <https://carterflayhart.pages.dev>. The Cloudflare account, Pages project, D1 database, database migration, repository push and GitHub workflow are already set up. **Do not recreate them. Do not repeat the earlier `export`, configuration-script or Git push steps.** Keep the existing GitHub Pages hosting in place.

What remains:

- [ ] 1. Give GitHub Actions a working Cloudflare API token and confirm deployment succeeds.
- [ ] 2. Enable your owner-only dashboard.
- [ ] 3. Optionally enable feedback-form email delivery.
- [ ] 4. Verify owner access, tracking preferences and email delivery.
- [ ] 5. Submit the live website to Google and Bing.
- [ ] 6. Optionally connect available sportsbook prices. Validated predictions remain separate work.

**Security:** never paste tokens, client secrets or session cookies into chat. Put them only in the specific GitHub/Cloudflare secret field or local Wrangler prompt described below. No paid plan, purchased domain or Global API Key is required.

## 1. Fix the Cloudflare API token used by GitHub Actions

**Where:** your web browser, first Cloudflare and then GitHub. No terminal commands are needed for this step.

The saved GitHub API token was rejected by Cloudflare for D1 access with **HTTP 403 / code 7403**. The account ID, D1 repository variable and GitHub workflow permissions have already been checked. The working local Wrangler login is a different credential and does not fix the token stored in GitHub.

### 1A. Open the intended token-creation page

1. Open **this exact link** while signed into Cloudflare:

   <https://dash.cloudflare.com/profile/api-tokens>

2. This is your **profile’s API Tokens page**, for creating a **user-owned API token**. Use it for this guide. If you reached **Manage Account → Account API Tokens**, switch to the profile link above so we follow one consistent route.
3. Click **Create Token**.
4. Find **Custom token** and choose **Get started** (or the custom-token creation control shown). Do not choose a DNS template or a Global API Key.
5. Enter token name `Carter GitHub deployment`.

**Important distinction:** a *user-owned token* can have **Account permissions**. “User-owned” describes who owns the token; it does **not** mean you should select **User policy** in the permissions form. Cloudflare also supports account-owned tokens, but this guide deliberately uses the profile/user-owned route to avoid mixing two forms.

### 1B. Select the two permissions

The earlier notation `Account → Cloudflare Pages → Edit` meant **separate choices in a permission row**, not one long option. Do not search for that entire phrase.

Cloudflare’s current documentation lists both newer and older permission labels. Look for these equivalent entries:

| What the permission controls | Newer documented label | Older documented label |
| --- | --- | --- |
| Deploying this website | **Pages Write** | **Cloudflare Pages Edit** |
| Migrating/querying its database | **D1 Write** | **D1 Edit** |

Use the product’s **Write/Edit** permission, not Read. In a form with separate product and access controls, the first row is filled out like this:

1. Under **Permissions**, select the category **Account**. If the form offers **Add account policy**, choose that. Do not choose Zone or User policy.
2. Open the **product/permission dropdown in that Account row**. If it has a search box, search just `Pages`.
3. Choose **Pages** or **Cloudflare Pages**, whichever the form lists.
4. In the access dropdown to its right, choose **Write** or **Edit**, whichever that form offers for this product.
5. Click **Add more** or the control to add another permission in the Account policy.
6. In the second row, select **Account** if a category selector is shown.
7. Search the product/permission dropdown for `D1` (letter **D**, digit **1**).
8. Choose **D1**, then its **Write** or **Edit** access.

If your form combines product and access into one dropdown rather than separate controls, select **Pages Write** / **Cloudflare Pages Edit** and **D1 Write** / **D1 Edit** directly. You need one write-capable permission for each product.

**Do not choose these similarly named permissions:** Account Custom Pages, Access: Custom Pages, Page Rules, Account Settings, or User API Tokens. They do not replace the Pages deployment or D1 database permissions. Do not compensate by granting every permission.

**If Pages or D1 still is not available:** stop before creating the token. Confirm the URL is the profile link above, the permission category is Account, and no previous search/filter is hiding entries. Send a screenshot of **only the permission-selection form before a token is generated**, or type the dropdown labels/options you can see. Do not include a token value, Global API Key, authorization header or secret-bearing terminal output. The guide cannot establish your exact form layout without seeing it; do not guess a different permission.

### 1C. Restrict the token to the correct account

1. Find **Account Resources** or the account-resource selector for that policy.
2. Choose **Include → Specific account**.
3. Choose **Carter.flayhart@gmail.com’s Account**, the account containing your Pages project and D1 database. Its verified ID is:

   ```text
   3dcedb17c6e768707f97f3f0c5a3f088
   ```

4. Leave **Client IP Address Filtering** blank. GitHub-hosted runners do not use your home IP.
5. If you set an expiration/TTL, ensure the token is valid now and has not expired.
6. Click **Continue to summary**. Check that it grants **Pages Write/Edit** and **D1 Write/Edit** on that specific account.
7. Click **Create Token**.
8. Copy the newly displayed **token value**. Cloudflare normally shows it only once. Do not copy the token name, token ID or account ID. Do not add quotes or a `Bearer ` prefix.

### 1D. Replace the GitHub secret

1. Open this GitHub page, signed in as **01cflayhart**:

   <https://github.com/01cflayhart/Carter-Flayhart-Webpage/settings/secrets/actions>

2. Under **Repository secrets**, find **CLOUDFLARE_API_TOKEN**.
3. Click its edit/pencil control.
4. Paste the new token value into the secret field and save/update it.
5. Leave **CLOUDFLARE_ACCOUNT_ID**, the D1 variable and the database unchanged; they were already checked. Do not put the API token in Variables or an unused Environment.

### 1E. Run and verify the deployment

1. Open the existing workflow directly:

   <https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/cloudflare.yml>

2. The title should be **Publish to Cloudflare Pages**. Do **not** click **New workflow**; that is a template chooser, not the installed workflow.
3. Click **Run workflow** → choose **Branch: main** → click **Run workflow** in that menu.
4. Refresh the run list if necessary and open the newest run, then its **deploy** job.
5. Confirm all of these steps succeed:
   - **Verify Cloudflare account and resource access**
   - **Apply pending analytics database migrations** (“No migrations to apply” is fine)
   - **Deploy static assets and protected Pages Functions**
6. Open <https://carterflayhart.pages.dev> to confirm the website still loads.

**Done when:** the actual deployment step succeeds. A skipped deployment, a valid token-status test alone, or a successful local Wrangler OAuth deployment is not enough. Changing a GitHub secret does **not** automatically trigger a workflow; Step 1E is required. No additional Git push is needed to replace a secret.

If the run fails, send only its **run URL and error code**. Error 7403 means Cloudflare still refuses account/resource access; do not bypass the check or delete the database. Keep any old token used by other integrations; revoke an old dedicated token only after its replacement works.

## 2. Enable your owner-only dashboard

Do this after Step 1 succeeds. You must create/authorize the GitHub OAuth application yourself; do not send its secret in chat.

### 2A. Create the GitHub OAuth application — browser

1. Sign into GitHub as **01cflayhart**.
2. Open <https://github.com/settings/developers>.
3. Choose **OAuth Apps**, then **New OAuth App**. Do not choose **GitHub Apps**.
4. Fill in:
   - **Application name:** `Carter website owner login`
   - **Homepage URL:** `https://carterflayhart.pages.dev`
   - **Authorization callback URL:** `https://carterflayhart.pages.dev/api/auth/callback`
   - **Device flow:** leave disabled.
5. Register the application. Keep its page open to copy the **Client ID** and generate a **Client Secret**. The Client ID is not the application’s numeric ID.

### 2B. Save the login values in Cloudflare — WSL terminal

Open the **Ubuntu/WSL terminal**, not a browser address bar, and enter:

```bash
cd /mnt/c/Users/Carte/Website
```

Run the next commands **one at a time**. Each asks for a secret locally. Paste only the requested value, then press Enter; the prompt may hide what you type.

```bash
npx --yes wrangler@4.158.0 pages secret put GITHUB_CLIENT_ID --project-name carterflayhart
```

At that prompt, paste the OAuth application’s **Client ID**.

```bash
npx --yes wrangler@4.158.0 pages secret put GITHUB_CLIENT_SECRET --project-name carterflayhart
```

At that prompt, paste the newly generated OAuth **Client Secret**.

Generate a separate random session secret in your terminal:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Copy its output privately, then run:

```bash
npx --yes wrangler@4.158.0 pages secret put SESSION_SECRET --project-name carterflayhart
```

At that prompt, paste the random output you just generated. Do not use a password, the Cloudflare API token or the GitHub Client Secret for this value. Do not share a screenshot of it.

These three values are **Cloudflare Pages runtime secrets**, not the GitHub repository’s deployment secrets. The owner ID and production origin are already set by the deployment configuration; leave them alone.

### 2C. Redeploy and test — browser

1. Run **Publish to Cloudflare Pages** again using the direct workflow link in Step 1E, so the deployment receives the new runtime secrets.
2. After success, open <https://carterflayhart.pages.dev/private>.
3. Sign in with GitHub as **01cflayhart** and complete the authorization screen yourself.
4. Confirm the owner dashboard appears and **Setup checks** reports the database ready. An email warning is expected until optional Step 3 is complete.
5. Login must use this production hostname, not a `*.carterflayhart.pages.dev` preview URL. Preview login is intentionally blocked.

**Done when:** your account can sign in and see the private dashboard. A different GitHub account must not gain owner access.

## 3. Optional: enable feedback-form email delivery

**You can skip this.** The direct email link already works without an email provider. Skipping keeps that fallback; it does not enable server-sent feedback messages.

### 3A. Create the sender — browser

1. Create/sign into a free Resend account using **carter.flayhart@gmail.com**, the website’s fixed feedback recipient. Verify the account email.
2. Check Resend’s current sandbox restrictions: its free test sender must be permitted to send to that verified address. Do not buy a domain or plan for this guide; `pages.dev` is not an email domain you own.
3. Create an API key with sending access. Keep it private.
4. Use sender `Carter Website <onboarding@resend.dev>` **only if Resend permits that sender and recipient for your account**. If it does not, stop and keep the direct email fallback rather than inventing a sender.

### 3B. Save the sender values — WSL terminal

```bash
cd /mnt/c/Users/Carte/Website
npx --yes wrangler@4.158.0 pages secret put RESEND_API_KEY --project-name carterflayhart
```

Paste the Resend API key at that command’s prompt. Then run:

```bash
npx --yes wrangler@4.158.0 pages secret put FEEDBACK_FROM --project-name carterflayhart
```

Paste the complete permitted sender string at that prompt.

### 3C. Redeploy and confirm actual delivery — browser

1. Run the Cloudflare deployment workflow again and wait for success.
2. Open the sports hub and submit one recognizable test message through its feedback form.
3. Confirm it arrives at **carter.flayhart@gmail.com**, including checking spam.

**Done when:** the message actually arrives. A configured sender or form success means neither guaranteed inbox delivery nor completed verification. If it fails, use the direct email link; the form preserves your text for retrying.

## 4. Finish the private-feature checks

After owner login works, use the browser to check:

- [ ] In an incognito/signed-out window, <https://carterflayhart.pages.dev/api/owner/stats> and <https://carterflayhart.pages.dev/api/owner/setup> return **401** without statistics/setup data. `/private` shows only a login screen.
- [ ] Signed in as 01cflayhart, `/private` displays separate daily **professional** and **sports** view counts.
- [ ] Leave **Exclude my activity** checked, visit both site areas, and confirm your own visits are excluded. Uncheck it and test inclusion. DNT or Global Privacy Control may still suppress tracking; these are coarse page-view totals, not unique-visitor counts.
- [ ] Sign out. Private data must become inaccessible; this browser’s exclusion preference should remain in effect.
- [ ] If you enabled form email, complete the actual inbox test in Step 3C. If not, verify the direct email link instead.

Do not share session cookies or private dashboard data publicly. Keep the original GitHub Pages hosting until the transition is fully verified; this guide does not instruct deleting or redirecting it.

## 5. Submit the live site to Google and Bing

**Where:** browser; one downloaded verification file must also be added to the repository.

### Google Search Console

1. Open <https://search.google.com/search-console> and sign into your Google account.
2. Choose **Add property → URL prefix**. Do not choose a DNS/Domain property for `pages.dev`.
3. Enter `https://carterflayhart.pages.dev/`.
4. Choose **HTML file** verification and download Google’s verification file.
5. Place the file **unchanged** in `/mnt/c/Users/Carte/Website/site/`. Do not place it in `_site/`, which is generated. You can ask the agent to add/commit/push this non-secret verification file after supplying it.
6. Wait for a successful Cloudflare deployment. Open `https://carterflayhart.pages.dev/` followed by the exact downloaded filename and confirm it is accessible.
7. Return to Search Console and click **Verify**. Keep the file in the repository afterward.
8. In **Sitemaps**, submit `https://carterflayhart.pages.dev/sitemap.xml`.
9. Use **URL inspection** for the home page and request indexing if offered. Link the new website from your GitHub and academic profiles.

### Bing Webmaster Tools

1. Open <https://www.bing.com/webmasters/> and sign in.
2. Import the verified Google Search Console site if offered, or add the same site using Bing’s HTML-file verification method.
3. If using a file, follow the same `site/` → commit/push → successful deployment → verification sequence.
4. Submit the same sitemap URL.

**Done when:** ownership is verified and the sitemap is submitted. Search indexing takes time; a first-place result is not guaranteed.

## 6. Optional: connect sportsbook prices, not validated predictions

1. Create a free account at <https://the-odds-api.com/> and obtain an API key.
2. In [GitHub repository secrets](https://github.com/01cflayhart/Carter-Flayhart-Webpage/settings/secrets/actions), choose **New repository secret**:
   - **Name:** `ODDS_API_KEY`
   - **Secret:** your odds-provider API key.
3. Open <https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/sports-analysis.yml>.
4. Select **Run workflow → main → Run workflow**.
5. Confirm that workflow and its subsequent Cloudflare deployment succeed. Inspect the sports pages for current coverage or a transparent missing-data notice.

Available DraftKings/FanDuel moneylines appear under **Market coverage · not forecasts**. Six credits per run are budgeted; manual runs also consume quota. Coverage is partial. Fanatics/Caesars are not on the documented free tier; do not enable paid sources unless you explicitly choose to do so yourself. No bets are placed.

**An odds key does not finish the prediction models.** Prop Hunt picks and Upset Alert probability categories still require validated independent model/evidence and settlement feeds. That is additional data/model engineering, not another account checkbox for you. Leave `SPORTS_INPUT_URL` and related optional feed secrets unset until a verified source exists. Do not substitute implied odds for independent probabilities or invent picks to fill an empty board. Technical requirements remain in [sports-operations.md](sports-operations.md).

## Sources for the Cloudflare permission names

Checked against Cloudflare’s documentation when this remaining-steps guide was rewritten:

- [Create API token](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/): distinguishes the **My Profile** user-token route from the **Manage Account** account-token route, and explains Account/User/Zone permission groups.
- [API token permissions](https://developers.cloudflare.com/fundamentals/api/reference/permissions/): lists both **Pages Write / D1 Write** and **Cloudflare Pages Edit / D1 Edit** names under account permissions. Similar “Custom Pages” permissions are for other services.

These sources document the permission names, not proof of the exact layout in your current dashboard. If your form still differs, use the safe screenshot/option-list instruction in Step 1B instead of guessing.
