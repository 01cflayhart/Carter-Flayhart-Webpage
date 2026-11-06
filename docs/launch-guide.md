# Launch Carter’s website

The initial website is now live at <https://carterflayhart.pages.dev>. It was deployed using the existing local Cloudflare OAuth login. GitHub Actions deployment credentials still need their own successful workflow check; owner sign-in and email setup remain unfinished. These steps use free hosting and do not require buying a domain or odds subscription. Keep the existing GitHub Pages website. Never send credentials in chat, commit them, or place them in `site/`.

Repository: <https://github.com/01cflayhart/Carter-Flayhart-Webpage>

Live website: <https://carterflayhart.pages.dev> (project creation and production URL verified).

Commands below use bash/WSL from the repository root, with Git, Node.js 22+ and Python 3 available. `npx` downloads the pinned Wrangler CLI when necessary; no global installation is required.

## Current progress — verified November 6, 2026

- [x] Cloudflare account created and Wrangler login authorized. `wrangler whoami` confirmed the account.
- [x] Direct Upload Pages project `carterflayhart` exists with hostname `carterflayhart.pages.dev` and no Git provider connected.
- [x] D1 database `carter-site-activity` exists. Its UUID is `3278b8b6-09b9-4b0f-8abe-92d18f722985` (an identifier, not a credential).
- [x] Local `wrangler.jsonc` generated in the website repository using that verified UUID. Git ignores this file. **The failed configuration command has now been completed for you.**
- [ ] Your terminal's exported variable cannot be verified from this separate agent shell. This is no longer a blocker: the local configuration is generated, and GitHub Actions will use its own repository variable.
- [x] GitHub authentication and push completed. The agent can now inspect workflow runs and settings. Both Cloudflare secret names are present, the D1 repository variable matches, and default workflow permissions are `write`.
- [ ] Section 2 authorization is **not yet fully working**: the push-triggered Cloudflare run failed with API error **7403**, and a retry still failed after the agent reset `CLOUDFLARE_ACCOUNT_ID` to the independently verified account ID. The remaining manual blocker is to check/replace the API token and its account permissions/resources, then rerun. GitHub cannot reveal its saved secret value.
- [x] Production D1 migration `0001_analytics.sql` applied successfully using the existing Cloudflare login. The analytics and rate-limit tables are created; do not recreate the database.
- [x] Initial Cloudflare production deployment completed. Live GET checks passed for the home page, CV PDF, sports hub and both tennis datasets. Anonymous owner APIs return 401; private login remains unavailable until its secrets are configured. No feedback mail or synthetic analytics events were submitted during verification.
- [x] Launch source committed locally on `main`, with the latest remote publication/ranking updates incorporated without discarding them. Generated assets, local configuration and credentials were excluded. A final documentation commit records the launch status.
- [x] Section 3 source push completed. GitHub registers **Publish to Cloudflare Pages** as active and automatically ran it on the push. An early credential/resource preflight has been added so authorization errors are reported before the expensive build. Source/guide corrections are committed and pushed by the agent.
- [ ] Confirm a successful **GitHub Actions** Cloudflare deployment after fixing the API token. The earlier successful local OAuth deployment does **not** prove the separate GitHub Actions API token works.
- [ ] Section 4: configure owner-login secrets. The Pages production secret list is currently empty.
- [ ] Section 5: optional email sender configuration; no Pages production secrets are present yet.
- [ ] Section 6: verify the live website, authorization, activity counts and actual feedback delivery.
- [ ] Sections 7–8: optional odds account connection and search-engine verification/indexing.

**Next manual step: follow “Current blocker: Cloudflare API token authorization” below. No additional terminal push is needed for the changes made by this session.** After a successful GitHub Actions deployment, continue at Section 4 for owner login and Section 5 for optional email. Do not recreate the existing project or database. The existing GitHub Pages site has not been removed. These are point-in-time checks, not claims that future steps are complete.

### Finding the workflow you could not see

Open this exact URL while signed into GitHub as 01cflayhart:

<https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/cloudflare.yml>

This is the existing workflow page, **not** the **New workflow** template chooser. GitHub's API confirms the workflow is active; its push-triggered run exists at <https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/runs/42296280142>. It is therefore not missing from the repository. The exact reason your previous Actions view did not show it could not be established from here; a stale page, a workflow filter or a different repository view may hide it. Use the direct link instead of searching the sidebar, and refresh the page if needed.

The page should be titled **Publish to Cloudflare Pages**. Its **Run workflow** button lets you select **Branch: main**, then **Run workflow**. Click a run's title to see its job/step results. A red run is a failed deployment, not evidence that the workflow was never installed.

### Current blocker: Cloudflare API token authorization

The original run and retry both reached the Cloudflare API and failed at D1 access with:

```text
The given account is not valid or is not authorized to access this service [code: 7403]
```

The agent verified the account through Wrangler's independent OAuth login and set GitHub secret `CLOUDFLARE_ACCOUNT_ID` to `3dcedb17c6e768707f97f3f0c5a3f088`. The D1 UUID repository variable and GitHub workflow permissions were also verified. The same failure persisted on retry. The encrypted token value and its Cloudflare policy cannot be read back from GitHub, so the exact token defect cannot be established here. Possibilities include a wrong/expired/revoked token, missing D1 access, or a policy scoped to another account. Do **not** delete the database, recreate the Pages project or change working local OAuth login to fix this.

Complete these steps in the **Cloudflare and GitHub websites**, not the terminal:

1. In Cloudflare, open your profile → **API Tokens** → **Create Token** → **Create Custom Token**. Create a dedicated replacement such as `Carter GitHub Pages and D1`.
2. Under permissions choose **Account policy**. Add **both** rows (use **Add more** for the second):
   - **Account → Cloudflare Pages → Edit**
   - **Account → D1 → Edit**
   Do not substitute Zone or User policies, or Read-only permissions.
3. Under **Account Resources**, select **Include → Specific account → Carter.flayhart@gmail.com's Account**. Confirm it is account `3dcedb17c6e768707f97f3f0c5a3f088`, the account containing `carterflayhart` and `carter-site-activity`.
4. Leave **Client IP Address Filtering** blank for this test: GitHub-hosted runners do not use your home/WSL IP. If using an expiration, make sure the token is currently valid and has not expired.
5. Select **Continue to summary**, check both Account/Edit permissions and the account resource, then **Create Token**. Copy the actual newly displayed **token value**—not its name or ID, a Global API Key, an OAuth code, or an account ID. Do not add quotes or a `Bearer ` prefix. Never send it in chat.
6. Open <https://github.com/01cflayhart/Carter-Flayhart-Webpage/settings/secrets/actions>. Under **Repository secrets**, click the edit/pencil control beside **CLOUDFLARE_API_TOKEN**. Replace its value with the new token and save. Do **not** add it under Variables or an unreferenced Environment instead.
7. Open the [direct workflow page](https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/cloudflare.yml). Select **Run workflow → main → Run workflow**. Updating a secret alone does **not** trigger a run. You do not need another Git push just to change a secret.
8. Confirm **Verify Cloudflare account and resource access**, the migration step, and **Deploy static assets and protected Pages Functions** all succeed. “No migrations to apply” is fine; the tables already exist. A skipped deploy or failed preflight is not success. If it still fails, send only the **run URL/error code**—never the token. Once the replacement works, revoke an old token only if you know it has no other consumers.

The preflight makes a read-only `SELECT 1` D1 query and checks the existing Pages project, without printing credentials or API response bodies. The actual deployment separately validates Pages write access. The live website stays on its previous successful deployment when an Actions run fails.

### Why the configuration command failed, and how to run it correctly

The error `Cannot find module '/home/carter/scripts/configure-cloudflare.cjs'` shows that your terminal was in `/home/carter`, your Linux home folder. Node resolves `scripts/configure-cloudflare.cjs` relative to the terminal's current folder. The script actually lives in `/mnt/c/Users/Carte/Website/scripts/`. This is a directory mismatch, **not** a broken Node.js installation; do not reinstall Node or recreate Cloudflare resources.

Before running repository commands in any new terminal, run these **one line at a time**:

```bash
cd /mnt/c/Users/Carte/Website
pwd
ls scripts/configure-cloudflare.cjs
```

`pwd` should print `/mnt/c/Users/Carte/Website`; `ls` should print the script path without an error. Then, if you want to repeat the already-completed configuration step:

```bash
export CLOUDFLARE_D1_DATABASE_ID='3278b8b6-09b9-4b0f-8abe-92d18f722985'
node scripts/configure-cloudflare.cjs
```

Use that actual UUID, **not** the literal text `paste-the-database-uuid-here`. If you previously exported the placeholder unchanged, the shell accepted it as a string but it was not a valid database ID. `export` applies to that terminal and processes started from it; it does not automatically change other terminals, GitHub Actions or Cloudflare settings. Closing the terminal normally loses the variable, but the generated local configuration stays on disk.

Alternatively, this single command works from any bash/WSL folder and does not rely on a prior `export`:

```bash
CLOUDFLARE_D1_DATABASE_ID='3278b8b6-09b9-4b0f-8abe-92d18f722985' node /mnt/c/Users/Carte/Website/scripts/configure-cloudflare.cjs
```

The script always writes to this repository, even when called using its absolute path. Repeating it with the same configuration is safe. If it reports that a different configuration already exists, review that file instead of deleting or overwriting it blindly.

## 1. Create the Cloudflare project and database

Sign up for/sign in to a free Cloudflare account. In a terminal in this repository, run the following **one at a time**. Login opens your browser; complete that authorization yourself. Do not use a temporary preview account.

```bash
cd /mnt/c/Users/Carte/Website
npx --yes wrangler@4.158.0 login
npx --yes wrangler@4.158.0 whoami
npx --yes wrangler@4.158.0 pages project create carterflayhart --production-branch main
npx --yes wrangler@4.158.0 d1 create carter-site-activity
```

This guide uses a **Direct Upload Pages project deployed by GitHub Actions**, not Cloudflare Git integration. Do not enable a second deployment method. If either resource already exists in your account, reuse it rather than creating a duplicate. If the project name is taken, stop: the canonical URLs, sitemap and OAuth callback must be updated together before using a different name.

Copy the D1 **database UUID**, not the account ID, from the command output. Replace the example text below with that UUID; do not enter the placeholder literally. For this already-created database, use the exact command in the progress section above. To prepare your ignored local configuration:

```bash
export CLOUDFLARE_D1_DATABASE_ID='paste-the-database-uuid-here'
node scripts/configure-cloudflare.cjs
```

The script validates the UUID and writes `wrangler.jsonc`, which Git ignores. It writes no tokens or passwords and refuses to overwrite a different local configuration. The file binds the database as `DB` and sets the production origin and your GitHub owner ID. GitHub Actions generates the same configuration afresh.

## 2. Authorize GitHub Actions deployment

1. In Cloudflare, open **My Profile → API Tokens → Create Token → Create Custom Token**.
2. Choose **Account policy**, not Zone or User. Add two permission rows: **Account → Cloudflare Pages → Edit** and **Account → D1 → Edit**. Under Account Resources, choose **Include → Specific account → your account**. Continue to summary and create the token. Keep it private. Your verified **Account ID** is `3dcedb17c6e768707f97f3f0c5a3f088`; `npx --yes wrangler@4.158.0 whoami` also displays it.
3. Open the GitHub repository → **Settings → Secrets and variables → Actions → Secrets → New repository secret**. Add:
   - `CLOUDFLARE_API_TOKEN`: the token you just created.
   - `CLOUDFLARE_ACCOUNT_ID`: your Cloudflare account ID.
4. In the adjacent **Variables** tab, add repository variable `CLOUDFLARE_D1_DATABASE_ID` with value `3278b8b6-09b9-4b0f-8abe-92d18f722985`, the verified D1 database UUID. This ID is configuration, not an authentication credential. The earlier terminal `export` does **not** create this GitHub variable; you must add it on GitHub separately.
5. Under **Settings → Actions → General → Workflow permissions**, enable **Read and write permissions** so the existing daily data jobs can commit validated snapshots. Save. If organization policy prevents this, an organization administrator must enable it.

The Cloudflare workflow checks all three settings, builds the website, applies pending D1 migrations, then deploys the assets and Functions. Missing credentials cause an explicit skip, not a claimed deployment. A failed migration stops deployment.

### Check whether Section 2 is complete

These are **GitHub website** checks, not terminal commands. The agent has now verified the secret names, D1 variable value and default workflow permissions. Secret values remain deliberately unreadable; the actual API token has not yet passed deployment authorization:

1. Open <https://github.com/01cflayhart/Carter-Flayhart-Webpage/settings/secrets/actions>. Under **Repository secrets**, confirm that `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` are listed. GitHub deliberately does not reveal their saved values. Do not send the token in chat.
2. Open <https://github.com/01cflayhart/Carter-Flayhart-Webpage/settings/variables/actions>. Confirm `CLOUDFLARE_D1_DATABASE_ID` is a **repository variable** with value `3278b8b6-09b9-4b0f-8abe-92d18f722985`.
3. Open <https://github.com/01cflayhart/Carter-Flayhart-Webpage/settings/actions>. Under **Workflow permissions**, confirm **Read and write permissions** is selected and saved.
4. Once the source is pushed, a successful **Publish to Cloudflare Pages** workflow is the actual end-to-end check of token validity/account permissions. A green run that says deployment was skipped is **not** sufficient. A successful manual Wrangler deployment proves only the separate local OAuth login, not the saved GitHub API token.

## 3. Publish the source changes

**Already completed for this launch:** GitHub authentication and the source push have succeeded, and the workflow has run. The agent also pushes the subsequent preflight/guide fixes. You do not need to repeat these steps to fix the Cloudflare API token; change the GitHub secret and run the existing workflow instead. The instructions below are retained for future source edits or a new terminal setup. Do not include `.env*`, `.dev.vars*`, `wrangler.jsonc`, caches, or generated `_site/`; these are ignored. The maintained `wrangler.jsonc.example` is safe to commit; it contains only a placeholder database ID.

**Where to type the push:** use your **Ubuntu/WSL terminal**, the same kind of terminal where you ran `npx` and `export`. Do not type Git commands in Cloudflare's website, GitHub's website, a browser address bar or the Node.js interactive prompt. The terminal can initially be in `/home/carter`; the first command below moves it to the correct website folder.

Run these **one line at a time**:

```bash
cd /mnt/c/Users/Carte/Website
pwd
git status
git log -1 --oneline
git push origin main
```

`pwd` should print `/mnt/c/Users/Carte/Website`. `git log` should show the newly prepared launch/documentation commit. The initial launch changes are committed by the agent, so you do **not** need to run `git add` or `git commit` again for them. `git push` uploads commits, not uncommitted files. If you make additional edits afterward, those need a separate review and commit first. A successful push lists updated commit IDs; it is not the same as a completed Actions deployment.

### If GitHub authentication is requested or the push fails

Cloudflare login does **not** sign Git into GitHub. Do not enter your ordinary GitHub password as a Git HTTPS password. For a browser-based GitHub login in WSL, run:

```bash
sudo apt update
sudo apt install gh
gh auth login --scopes workflow
```

Installing `gh` is a local system package step; if already installed, skip the installation. In `gh auth login`, choose **GitHub.com → HTTPS → Log in with a web browser**, then follow its one-time code/link instructions using your 01cflayhart account. The `workflow` scope permits pushing the new GitHub Actions workflow files. Complete authorization yourself. Then run:

```bash
gh auth setup-git
cd /mnt/c/Users/Carte/Website
git push origin main
```

If installing software is not allowed on your machine, use your editor's authenticated Source Control push for this same folder instead. No need to paste a personal access token into chat.

If GitHub rejects a workflow-file push because the OAuth token lacks `workflow` scope, run `gh auth refresh -h github.com -s workflow`, finish browser authorization, and retry the push.

If the push is rejected because `main` has newer remote commits, run `git status` first. With a clean working tree, run `git pull --rebase origin main`, then `git push origin main`. If conflicts are reported, stop and ask for help; do not force-push, reset or discard files.

Open <https://github.com/01cflayhart/Carter-Flayhart-Webpage/actions/workflows/cloudflare.yml> → **Run workflow → main** if the push did not already start it. Wait for a green deployment, not merely a skipped job. Keep the original GitHub Pages workflow enabled during this transition.

The first deployment can be public before owner sign-in/email are configured. Those features fail closed. Subsequent publication/CV/ranking updates dispatch both hosting workflows; Cloudflare also refreshes every six hours. GitHub schedules can be delayed.

## 4. Enable your private dashboard

1. Sign in to GitHub as **01cflayhart**. Open <https://github.com/settings/developers> → **OAuth Apps → New OAuth App**.
2. Enter:
   - Application name: `Carter website owner login`
   - Homepage URL: `https://carterflayhart.pages.dev`
   - Authorization callback URL: `https://carterflayhart.pages.dev/api/auth/callback`
   - Leave device flow disabled. This app does not request repository scopes.
3. Copy the Client ID, then generate a Client Secret. Add them to your Pages project using these commands, one at a time; paste each value only at Wrangler’s local prompt:

```bash
npx --yes wrangler@4.158.0 pages secret put GITHUB_CLIENT_ID --project-name carterflayhart
npx --yes wrangler@4.158.0 pages secret put GITHUB_CLIENT_SECRET --project-name carterflayhart
```

4. Generate a new session secret in your own terminal:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Copy its output into the next command’s prompt. This value signs your login cookies; do not reuse another password or publish it.

```bash
npx --yes wrangler@4.158.0 pages secret put SESSION_SECRET --project-name carterflayhart
```

`GITHUB_OWNER_ID=168453384` and `SITE_ORIGIN=https://carterflayhart.pages.dev` are already set by the generated configuration; they are not secrets. Authorization uses your immutable GitHub numeric ID, not a name or email. Login intentionally refuses other hosts, including previews.

## 5. Enable feedback email, or keep the free email-link fallback

The direct `mailto:` link already works without an email provider. To enable form delivery:

1. Create a free Resend account using/authorized for **carter.flayhart@gmail.com**, the fixed feedback recipient. Do not buy a domain or plan for this setup.
2. Create an API key with sending access. Using the free sandbox sender requires the recipient to be the account’s permitted verified address. Check Resend’s current sandbox restrictions before proceeding.
3. At Wrangler’s prompts, set:

```bash
npx --yes wrangler@4.158.0 pages secret put RESEND_API_KEY --project-name carterflayhart
npx --yes wrangler@4.158.0 pages secret put FEEDBACK_FROM --project-name carterflayhart
```

For `FEEDBACK_FROM`, use `Carter Website <onboarding@resend.dev>` **only if Resend permits this sender and recipient for your account**. A verified custom-domain sender is optional, not required for keeping the email-link fallback. `pages.dev` is not your email domain to verify.

Run **Publish to Cloudflare Pages** again after adding runtime secrets so a new production deployment receives them. Visit `/private`, sign in, and inspect **Setup checks**. A configured sender is not proof of delivery.

## 6. Verify before calling the launch complete

- Open the home page, CV PDF, publications, sports hub and both tennis tours at the new hostname.
- In an incognito window, `/api/owner/stats` and `/api/owner/setup` must return **401** without data. `/private` must show only the owner-login screen. Do not share or capture your session cookie.
- Sign in as 01cflayhart: `/private` should show database setup complete and separate professional/sports daily counts. A different GitHub account must be denied access.
- Leave **Exclude my activity** checked. Visit both areas and confirm your views are not counted. Uncheck it and test again; sign-out retains this browser’s exclusion preference. DNT/GPC can still suppress tracking; totals are page views, not unique people.
- Submit one feedback message with a recognizable subject/content and confirm it actually arrives at **carter.flayhart@gmail.com** (including spam). A successful form response means the email service accepted the message, not that inbox delivery is guaranteed. If delivery fails, use the direct email link; the form preserves your text.
- Leave GitHub Pages intact until all required behavior works. Do not redirect/delete it as part of these instructions.

## 7. Optional: connect odds (not trained predictions)

Create a free account at <https://the-odds-api.com/>. In **GitHub repository → Settings → Secrets and variables → Actions**, add secret `ODDS_API_KEY`. Run **Actions → Review and archive sports analysis daily → Run workflow**.

This connects available DraftKings/FanDuel moneylines under **Market coverage · not forecasts**. Six credits per run are budgeted; repeated manual runs also consume quota. Coverage is partial. Fanatics/Caesars are not on the documented free tier; do not enable paid books without explicitly choosing a supported paid plan yourself. No bets are placed.

**Prop Hunt picks and Upset Alert probability categories still need a verified independent evidence/model feed.** Do not paste a sportsbook URL into `SPORTS_INPUT_URL`, set verification flags by assumption, or substitute implied odds for independent probabilities. See `docs/sports-operations.md` for the exact feed contract. Leave those optional feed secrets unset until a validated source/model exists; empty boards are intentional. The current prop baseline is not a completed calibrated multisport model.

## 8. Search-engine setup

Once the hostname is live, open Google Search Console and add a **URL-prefix property** for `https://carterflayhart.pages.dev/`. Use HTML-file verification: download Google’s file, place it unchanged in `site/`, commit/push, wait for deployment, then select **Verify**. This does not require control of `pages.dev` DNS. Add the same URL-prefix site in Bing Webmaster Tools using its HTML-file method, or import the verified Search Console property if offered.

Submit `https://carterflayhart.pages.dev/sitemap.xml` in each service. Request indexing for the home page and link the new URL from your GitHub/academic profiles. Do not remove the verification file afterward. No first-place search ranking is guaranteed.

## Troubleshooting

- **Cannot find “Publish to Cloudflare Pages” in Actions:** use the direct workflow URL above, not **New workflow**. This workflow exists and is active; a push-triggered run already failed at Cloudflare authorization. Refresh/check the repository and filters instead of creating another deployment workflow.
- **Cloudflare 7403:** see the current-blocker token replacement steps above. Account ID has been independently checked/reset; D1 access still fails with the saved API token. A working local Wrangler OAuth login does not grant access to a different API token stored in GitHub.
- **`Cannot find module '/home/carter/scripts/configure-cloudflare.cjs'`:** the terminal is in your home folder, not the repository. Run `cd /mnt/c/Users/Carte/Website`, then retry. See the exact recovery commands above. Cloudflare-wide commands such as `whoami` can work from your home folder, which is why earlier steps succeeded there.
- **`Set CLOUDFLARE_D1_DATABASE_ID to the database UUID`:** the variable is missing in this terminal or contains the placeholder. Re-export the actual UUID in this same terminal or use the one-line absolute-path command above. Do not reinstall Node.
- **Workflow skipped:** check both GitHub secrets and the D1 repository **variable**, then run again. Dashboard runtime secrets belong to Pages, not GitHub Actions.
- **Unknown project/name unavailable:** resolve the Pages project name before creating the OAuth app or publishing different canonical URLs.
- **Database needs setup:** confirm the correct database UUID, migration step success and binding name `DB`. Do not drop tables or recreate the database to fix an ID typo.
- **Login unavailable:** check the three Pages login secrets, exact callback, strong session secret and production hostname; redeploy after changing settings. Preview login is intentionally blocked.
- **Feedback error:** confirm D1/rate-limit tables, session secret, Resend sender/recipient permissions and sending quota; the email-link fallback remains available.
- **No predictions:** odds access is not independent model evidence. Empty forecasts are not a broken installation.
- **Local browser/build problems:** follow `docs/session-recovery.md`; use one browser worker and `python3 -m tennis.export --assets-only` for static-only edits.
