# Rating methodology — provisional v0.3

## Strength, form, availability, rank

These are different quantities. A score is not an ATP point total. Ordinal power
rank orders eligible players by availability-adjusted score, with stable player-ID
tie-breaking. Eligible players have at least one covered played match in the
trailing 12 calendar months. Filtering does not renumber them.

The model has a persistent **strength anchor** and a **rolling recent-form overlay**:

1. Initialize an anchor once, using the player's first observed historical ATP
   rank: `max(1250, 1800 - 180 * log10(rank))`, or 1250 when unknown. No ranking
   points enter this calculation. Never seed with future or current display ranks.
2. Before a match-date batch, freeze every player's ratings and power ranks.
   Expected win probability is `1 / (1 + 10 ** ((opponent - player) / 400))`.
3. Update the anchor with constant-K Elo (K=24), using the two pre-batch anchors.
   Its historical evidence preserves cross-tier comparability. Old data remains
   an indirectly learned strength prior; this is **not** a claim that every aspect
   of the rating forgets all history after one year.
4. Add opponent-adjusted form evidence using the pre-batch combined scores:
   `K * (outcome - expectation)`, with K=40 and a bounded provisional multiplier
   `1 + 0.5 * exp(-trailing_match_count / 12)`. This permits fast learning at any age.
5. Form evidence decays exponentially with a 120-day half-life and expires after
   12 calendar months. Overall strength is `anchor + 0.35 * weighted_form_sum`.
   Older results anchor established ability; recent results have additional impact.
6. Apply all outcomes in a batch simultaneously, not in CSV row order. Store the
   pre-date rank/rating and ranking-universe size for every participant in SQLite.

An initial experiment that forgot all historical strength toward a shared baseline
over-promoted prolific lower-tier players and underperformed basic Elo. The anchor
was retained to avoid that distortion. The resulting model is still provisional,
not a claim of optimal calibration or predictive superiority.

The Elo residual inherently makes unexpected wins/losses larger than expected
wins/losses. Competitive matches carry substantial evidence. A capped extra
competitive/upset multiplier is implemented behind `extra_impact`, **off by default**
to avoid double-counting surprises without validation. When enabled it uses 1.15
for 35–65% contests, 1.25 for surprising outcomes, and 0.75 for routine outcomes.
Official-rank reporting bands are not substituted for modeled opponent strength.

## Competition-level weighting

Both the persistent anchor and rolling form updates multiply their Elo residuals
by competition weight: tour main draw **1.00**, tour qualifying **0.40**,
Challenger **0.30**, ITF **0.08**, team **0.50**, unknown **0.00**. Challenger and
ITF qualifying multiply their own tier by 0.50 (0.15 / 0.04). Retirement weight
then multiplies this again. Counting many low-level wins is not equivalent to
winning the same number of tour matches. Raw W–L counts remain unweighted.

Valuebetennis source rounds 0–3 are qualifying, not tour main draws. The public
match pages were checked for codes 1 (Qualif. 1), 3 (Qualifications), and 4
(first main-draw round). ATP Slam qualifying requires two won sets, main draws
three. Competition weight is configurable and provisional, not tuned to put any
particular player on top or claimed to be a calibrated optimum.

## Identity-verified current-ranking prior

The public TennisONE ranking feed supplies current singles ranks and points.
Name matching **only proposes** a candidate. `scripts/refresh-tennis-identities.cjs`
reads the corresponding public Valuebetennis profile in ordinary Chromium and
requires exact normalized full name, tour/gender and matching birth date; if
either birth date is absent, matching country and tour/gender are required.
Conflicting or ambiguous identities remain unknown. Proofs retain profile URL,
content checksum, method and timestamp in `site/sports/tennis/identities.json`.
Documented aliases in `tennis/identity-aliases.json` require both matching birth
date and country, plus the public citation connecting the names. The initial
Cori/Coco Gauff alias is independently corroborated, never fuzzy surname matching.
New verification works through the first 1,000 positions per tour in rank order,
at most 200 new profiles/four minutes per daily run; existing proofs are cached.
The initial verified set primarily covers the top 300 per tour. Coverage can grow
on subsequent runs; unverified players remain explicitly unknown. Links use
namespaced IDs, not a fresh name-only join on every build.

Only the current publication receives this prior:

`adjustment = clamp(0.35 * (rank_seed - result_strength), -200, +200)`

Add that adjustment to result strength and availability-adjusted score before
sorting. The same adjustment applies across surfaces; it is **not** surface
evidence. Ranking points are displayed but are never added directly as Elo points.
Unknown/unverified ranks receive no invented prior. Future observations and
observations older than 14 days are ineligible. Failed refreshes retain their true
last-successful observation date, not a falsely updated timestamp.

TennisONE does not supply an edition date, so dates are labelled **observed**, not
official weekly editions. Historical replay, pre-date opponent categories and
walk-forward predictions do not use today's prior. Seven-day movements are
withheld for the blended publication because comparable prior-adjusted past ranks
have not been recorded. The historical evaluation tests only the result component,
not the new current-rank blend.

## Surface partial pooling

Outdoor hard, indoor hard, clay and grass have separate anchor/form updates. Surface expectation
uses partially pooled strength. With `n` covered matches on that surface, blend
`n / (n + 12)` of surface-specific evidence with overall strength. Fewer than 12
matches is explicitly provisional; a no-match surface rating is a pooled estimate,
not proof of performance. Unknown surface is counted separately and does not update
an invented surface anchor. The current CSV explicitly distinguishes `dur` from
`dur intérieur`. Generic historical `Hard` without an explicit indoor/outdoor flag
stays unknown; event names are not used to guess conditions. Carpet matches are
excluded from ratings, records, eligibility and backtests, not merely hidden in UI.

## Availability and injuries

When a player is absent, their score cannot rise above their score immediately
after the last observed match merely because negative form evidence decays. After
42 days, deduct `min(160, 0.6 * (days_absent - 42))` points. Display strength and the
total availability adjustment separately. This conservative heuristic needs
validation; it is not a medical model. Surface scores use analogous caps.

Verified injury reports provide context only, not an extra unvalidated injury
penalty (which could double-count inactivity). No absence or bad result is itself
proof of injury. Dated reports expire at a mandatory review date. Age is descriptive:
under 21 is “Next generation”, 35+ is “Veteran”. Neither changes numerical ratings.

## Timing, records, and exceptions

- Archive `tourney_date` and row-level ATP ranks refer to event start. They are
  approximations, not verified exact pre-match rankings. Optional `match_date`
  overrides the date. All same-date results remain frozen as a batch; exact
  intra-day sequencing is not currently claimed.
- Historical power ranks are computed from information available before the date
  batch. Players without earlier observations have unknown power ranks. Later
  results cannot change an earlier stored category during the same replay.
- Corrections or model/source changes legitimately require historical replay and
  a new model/source provenance record; this is different from relabeling old
  matches using current ranks.
- Records cover `(as_of minus 12 calendar months, as_of]` and `(as_of minus 3
  calendar months, as_of]`. Leap/end-of-month dates clamp to the valid calendar day.
  They are not calendar-year counts or an undocumented 90-day approximation.
- Similar is ±25 inclusive. Better/worse exclude that band. Unknown is explicit.
  Top 50 overlaps the disjoint categories and depends only on the opponent's
  historical rank. W–L counts are unweighted.
- Significant = wins vs better/similar, losses vs worse/similar. Both historical
  comparison bases are actually computed. All qualifying results are accessible
  with pagination, not only the last few.
- Walkovers, byes, defaults, abandonments, missing scores and exhibitions are
  excluded. Retirements count as played, with 50% rating influence. The optional
  retirements filter affects records/history, **not** the published rating.
- Team matches are included by default and identifiable separately; change
  `include_team` and replay to exclude. Not every modeled result awards ATP points.
- Rank change compares overall standings to the last covered batch at or before
  seven days before the cutoff. It is not a seven-day sum of match contributions,
  and source gaps can make the reference older than seven days.

## Validation

`python3 -m tennis.backtest` replays all historical batches in order, using earlier
data for warm-up. The default evaluation window is the last covered year.
Compare log loss and Brier score on a common sample where both official ranks
exist; also report all-coverage metrics, calibration bins, tiers and surfaces.
Basic Elo uses K=32, no form overlay and a common 1500 start; the rank baseline uses
the bounded rank-to-rating transform, not ATP points. Retirements are excluded from
evaluation. Event-start ordering remains approximate. Do not confuse these
benchmarks with an optimized official-ranking model or a final untouched holdout.

Parameters are explicitly configurable and reported in each snapshot. Preserve
an untouched future holdout before tuning; do not tune to make favorite players
look right. Poor baseline comparisons are a finding, not something to conceal.
