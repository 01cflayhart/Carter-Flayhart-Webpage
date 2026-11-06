# Continue the sports hub without reopening the interrupted session

Original request: OpenCode session `ses_e4e1fd967ffeIVIjq3Hm50Z120`, first user prompt. Its requested personal-site copy, navigation and sports-tool scaffolding survived in this checkout. Do not discard these uncommitted files or replay the entire request from scratch.

## What the failure evidence supports

- OpenChamber logs contain connection resets/refusals and “OpenCode service unavailable.” This establishes lost service connectivity, not a proven out-of-memory, model-context or application-code cause. No relevant fatal/OOM record was found in the inspected OpenCode and kernel logs.
- Chromium initially could not launch because `libnspr4`, `libnss3` and `libasound2t64` were missing. This is a browser dependency failure, not proof that Chromium crashed OpenCode.
- `python3 -m tennis.export` exceeded a two-minute tool timeout during recovery. It writes thousands of notebooks on a Windows-mounted filesystem; do not conflate a killed/timeout build with a service crash. Allow a longer bounded build, separate from browser checks, or reuse an existing export for static-only edits.
- The OpenCode process serving OpenChamber is parented by OpenChamber. The managed `opencode service status` command reported stopped; do not start a second service or restart the current one just to apply website edits.

## Low-concurrency verification

Run each phase separately, saving verbose output to ignored `reports/` or `test-results/` instead of pasting whole traces into a session:

1. `python3 -m unittest discover -q`
2. `npm run test:security`
3. `python3 -m tennis.export` (allow up to ten minutes; no parallel browser/build job).
4. `npm run test:pages -- --reporter=dot` (one worker, both desktop and mobile).

For static-only edits with an existing valid tennis export, run `python3 -m tennis.export --assets-only` instead of phase 3. This refreshes public assets without recomputing tennis data and refuses to run if either tour's exported metadata is missing. It is not a substitute for a full build after tennis model/data changes. Never replace production data with synthetic test fixtures. The static preview intentionally lacks Cloudflare Functions; tests of those endpoints belong to the security suite and later authenticated staging checks.

`scripts/verify-pages.cjs` uses unpacked browser dependencies from `~/.cache/carter-website/browser-libs/usr/lib/x86_64-linux-gnu` when present, preserving the caller's library path. This cache survives a WSL restart unlike `/tmp/opencode`. On a new Linux machine, use Playwright's documented system dependency setup, or download and extract the three missing distro packages into that cache without root. Do not commit shared libraries.

For an isolated full-build check, `python3 -m tennis.export --output /tmp/opencode/carter-website-export` writes to Linux storage rather than the slower Windows mount. This does not update the `_site` preview. Keep screenshots on disk and open them in the file panel rather than injecting full-page image/base64 output into the conversation.

## Recovery verification, November 6, 2026

- Python: 87 tests passed.
- Cloudflare/security unit tests: 6 passed; not a substitute for live OAuth, D1 or email checks.
- Serial Chromium: 25 checks passed across desktop/mobile; one desktop-only check intentionally skipped on mobile. Log: `reports/recovery-browser-tests.log`.
- Full isolated export: 3,122 ATP and 2,534 WTA notebooks generated successfully in `/tmp/opencode/carter-website-export`.
- These operations completed in the replacement session without restarting OpenCode. This does not establish the original crash's root cause or guarantee it cannot recur.

For the subsequent launch work, see `docs/launch-guide.md`. The expanded browser suite passed 29 checks (one intentional mobile skip); the security/configuration suite passed 10 tests. The Cloudflare Functions bundle compiled with Wrangler 4.158.0. These checks do not authorize or establish a live deployment. `npm run test:cloudflare` additionally exercises an isolated local Workers/D1 runtime without a Cloudflare account; run it separately from browser verification.

## Remaining goals are not crash workarounds

See `docs/sports-operations.md` for setup and exact contracts:

- Activate Cloudflare Pages with account authorization; hostname availability remains unverified. Preserve existing hosting until the new deployment works.
- Configure GitHub-owner OAuth, D1 and email delivery; verify owner/non-owner behavior and actual delivery before calling them live.
- Connect rights-cleared sportsbook prices, verified player/context mappings, independent favorite projections and book-specific final grading. Free four-book completeness has not been established. Raw moneylines are not forecasts.
- Validate new prediction models on chronological holdout data before promotion. The current prop baseline and independent-forecast input contract are not a completed trained multisport model. Do not imply daily reviews guarantee improving accuracy.
- Commit/push reviewed changes to activate GitHub daily workflows. Existing OpenChamber daily reviewer schedules alone do not deploy code or populate missing data.
- Verify Google/Bing ownership and submit the sitemap after the canonical hostname is live. No search rank can be guaranteed.

Neither deleting session history nor changing global OpenCode settings is necessary to continue these independent steps here.
