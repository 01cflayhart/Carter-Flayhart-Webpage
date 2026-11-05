"""Rolling, recency-weighted Elo with chronological pre-date snapshots."""
from collections import defaultdict, deque
from calendar import monthrange
from datetime import date, timedelta
from itertools import groupby
import math

VERSION = "0.3.0-provisional"
SURFACES = ("Outdoor hard", "Indoor hard", "Clay", "Grass")


def shift_months(day, months):
    ordinal = day.year * 12 + day.month - 1 + months
    year, month = divmod(ordinal, 12)
    return date(year, month + 1, min(day.day, monthrange(year, month + 1)[1]))


def parse_date(value):
    value = str(value)
    return date.fromisoformat(value) if "-" in value else date(int(value[:4]), int(value[4:6]), int(value[6:8]))


def number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None


def integer(value):
    n = number(value)
    return int(n) if n is not None and n > 0 and n == int(n) else None


def expected(a, b):
    return 1 / (1 + 10 ** (max(-2000, min(2000, b - a)) / 400))


def seed(rank, base=1250):
    return max(base, 1800 - 180 * math.log10(rank)) if rank else base


def category(own, opponent, band=25):
    if own is None or opponent is None:
        return "unknown"
    if abs(own - opponent) <= band:
        return "similar"
    return "better" if opponent < own else "worse"


def significant(own, opponent, won, band=25):
    c = category(own, opponent, band)
    return c == "similar" or (won and c == "better") or (not won and c == "worse")


def tier(row):
    level = row.get("tourney_level", "")
    if level == "C":
        return "Challenger"
    if level in ("S", "D") or row.get("tourney_name", "").startswith("Davis Cup"):
        return "Team"
    if level in ("15", "25", "35", "50", "75", "100") or row.get("family") == "ITF":
        return "ITF"
    if row.get("round", "").startswith("Q") and row.get("round") != "QF":
        return "Qualifying"
    if level in ("G", "M", "A", "F", "250", "500", "1000"):
        return "Tour"
    return "Unknown"


def normalize(rows):
    matches, seen, audit = [], {}, defaultdict(int)
    for row in rows:
        try:
            day = parse_date(row.get("match_date") or row["tourney_date"])
            event = row["tourney_id"].strip()
            w, l = row["winner_id"].strip(), row["loser_id"].strip()
            if not event or not w or not l or w == l or not row.get("winner_name") or not row.get("loser_name"):
                raise ValueError("Invalid identity")
            score = row.get("score", "").strip()
            if row.get('surface') == 'Carpet':
                audit['carpet_excluded'] += 1
                continue
            if row.get("tourney_level") == "E":
                audit["exhibitions"] += 1
                continue
            if not score or any(token in score.upper() for token in ("W/O", "WALKOVER", "DEF", "ABN", "BYE")):
                audit["not_played_or_unusable"] += 1
                continue
            key = (event, row.get("source_match_id") or row.get("round", ""), *sorted((w, l)))
            signature = (w, score, day)
            if key in seen:
                if seen[key] != signature:
                    raise ValueError(f"Conflicting duplicate {key}")
                audit["duplicates"] += 1
                continue
            seen[key] = signature
            surface = row.get('surface')
            if surface == 'Hard':
                setting = str(row.get('indoor', '')).lower()
                surface = 'Indoor hard' if setting in ('true','1') else 'Outdoor hard' if setting in ('false','0') else 'Unknown'
            match = dict(row, day=day, w=w, l=l, event=event, tier=tier(row),
                         qualifying=row.get('round', '').startswith('Q') and row.get('round') != 'QF',
                         surface=surface if surface in SURFACES else "Unknown",
                         retired="RET" in score.upper(), precision="match date" if row.get("match_date") else "event start",
                         identity="|".join(key))
            matches.append(match)
        except (ValueError, KeyError, TypeError) as error:
            # A malformed or conflicting source must not silently publish incomplete rankings.
            raise ValueError(f"Invalid match row: {error}") from error
    matches.sort(key=lambda m: (m["day"], m["identity"]))
    return matches, dict(audit)


class State:
    def __init__(self, initial, day, config):
        self.base = config["baseline"]
        self.anchor = initial
        self.anchor_surface = {s: initial for s in SURFACES}
        self.form_weight = config.get("form_weight", .35)
        self.day = self.last = day
        self.evidence = deque()
        self.sums = defaultdict(float)
        self.counts = defaultdict(int)
        self.total = 0
        self.last_strength = initial
        self.last_surface = {s: initial for s in SURFACES}

    def advance(self, day, config):
        factor = 2 ** (-(day - self.day).days / config["half_life_days"])
        self.sums = defaultdict(float, {s: v * factor for s, v in self.sums.items()})
        boundary = shift_months(day, -12)
        while self.evidence and self.evidence[0][0] <= boundary:
            old, surface, delta, surface_delta = self.evidence.popleft()
            weight = 2 ** (-(day - old).days / config["half_life_days"])
            self.sums["Overall"] -= delta * weight
            self.sums[surface] -= surface_delta * weight
            self.counts[surface] -= 1
            self.total -= 1
        self.day = day

    def strength(self, surface="Overall", config=None):
        overall = self.anchor + self.form_weight * self.sums["Overall"]
        if surface == "Overall":
            return overall
        n = self.counts[surface]
        blend = n / (n + config["surface_blend_matches"])
        return overall * (1 - blend) + (self.anchor_surface.get(surface, self.anchor) + self.form_weight * self.sums[surface]) * blend

    def anchor_on(self, surface, config):
        n = self.counts[surface]
        blend = n / (n + config["surface_blend_matches"])
        return blend * self.anchor_surface.get(surface, self.anchor) + (1 - blend) * self.anchor

    def score(self, surface="Overall", config=None):
        strength = self.strength(surface, config)
        last = self.last_strength if surface == "Overall" else self.last_surface.get(surface, self.last_strength)
        # An inactive player cannot gain merely because negative evidence decays.
        cap = min(strength, last) if self.day > self.last else strength
        return cap - min(160, max(0, (self.day - self.last).days - 42) * .6)

    def add(self, day, surface, delta, surface_delta):
        self.evidence.append((day, surface, delta, surface_delta))
        self.sums["Overall"] += delta
        self.sums[surface] += surface_delta
        self.counts[surface] += 1
        self.total += 1
        self.last = day


def empty_stats():
    return {key: [0, 0] for key in ("overall", "top50", "similar", "better", "worse", "unknown", *SURFACES, "Unknown")}


def statistics(history, cutoff, basis, exclude_retirements=False, surface="Overall"):
    result = empty_stats()
    for row in history:
        if row["date"] <= cutoff.isoformat() or (exclude_retirements and row["retired"]):
            continue
        if surface != "Overall" and row["surface"] != surface:
            continue
        c = category(row["own_" + basis], row["opp_" + basis])
        keys = ["overall", c, row["surface"]]
        if row["opp_" + basis] is not None and row["opp_" + basis] <= 50:
            keys.append("top50")
        for key in keys:
            result[key][0 if row["won"] else 1] += 1
    return result


def replay(matches, config, as_of, collect=True):
    """Freeze ranks per date, then apply all same-date outcomes simultaneously."""
    rc = config["rating"]
    states, bio, history, snapshots, predictions = {}, {}, defaultdict(list), [], []
    previous, prior_ranks = {}, {}
    basic = defaultdict(lambda: 1500.)
    for day, group in groupby((m for m in matches if m["day"] <= as_of and (rc["include_team"] or m["tier"] != "Team")), key=lambda m: m["day"]):
        batch = list(group)
        for st in states.values():
            st.advance(day, rc)
        eligible = [pid for pid, st in states.items() if st.total]
        pre = {pid: i + 1 for i, pid in enumerate(sorted(eligible, key=lambda p: (-states[p].score(config=rc), p)))}
        pre_scores = {pid: states[pid].score(config=rc) for pid in pre}
        for m in batch:
            for side, pid in (("winner", m["w"]), ("loser", m["l"])):
                if pid not in states:
                    states[pid] = State(seed(integer(m.get(side + "_rank")), rc["baseline"]), day, rc)
                bio[pid] = {"id": pid, "name": m[side + "_name"], "country": m.get(side + "_ioc", ""),
                            "age": number(m.get(side + "_age")), "bio_date": day.isoformat(),
                            "hand": m.get(side + "_hand", ""), "height": integer(m.get(side + "_ht"))}
        pending, basic_delta = [], defaultdict(float)
        for m in batch:
            w, l, s = m["w"], m["l"], m["surface"]
            a, b = states[w], states[l]
            p = expected(a.score(config=rc), b.score(config=rc))
            ps = expected(a.score(s, rc), b.score(s, rc))
            anchor_p = expected(a.anchor, b.anchor)
            anchor_ps = expected(a.anchor_on(s, rc), b.anchor_on(s, rc))
            pb = expected(basic[w], basic[l])
            wr, lr = integer(m.get("winner_rank")), integer(m.get("loser_rank"))
            pa = expected(seed(wr), seed(lr)) if wr and lr else None
            predictions.append({"date": day.isoformat(), "tier": m["tier"], "surface": s, "model": p, "elo": pb, "atp": pa, "winner_first": w < l,
                                "retired": m["retired"], "precision": m["precision"]})
            basic_delta[w] += 32 * (1 - pb)
            basic_delta[l] -= 32 * (1 - pb)
            event_weight = rc.get('tier_weights', {}).get(m['tier'], 1)
            if m.get('qualifying') and m['tier'] != 'Qualifying':
                event_weight *= rc.get('qualifying_multiplier', .5)
            weight = event_weight * (rc["retirement_weight"] if m["retired"] else 1)
            for pid, opp, won, prob, surfprob, ap, asp, side, other in (
                (w, l, True, p, ps, anchor_p, anchor_ps, "winner", "loser"), (l, w, False, 1 - p, 1 - ps, 1-anchor_p, 1-anchor_ps, "loser", "winner"),
            ):
                k = rc["k"] * (1 + .5 * math.exp(-states[pid].total / 12))
                multiplier = 1.
                if rc.get("extra_impact"):
                    multiplier = 1.15 if .35 <= prob <= .65 else 1.25 if (won and prob < .35) or (not won and prob > .65) else .75
                delta = k * (int(won) - prob) * weight * multiplier
                sd = k * (int(won) - surfprob) * weight * multiplier
                anchor_delta = rc.get("anchor_k", 24) * (int(won) - ap) * weight
                anchor_sd = rc.get("anchor_k", 24) * (int(won) - asp) * weight
                pending.append((pid, s, delta, sd, anchor_delta, anchor_sd))
                if collect:
                    history[pid].append({"date": day.isoformat(), "event": m.get("tourney_name", ""), "tier": m["tier"], "round": m.get("round", ""),
                        "surface": s, "opponent": bio[opp]["name"], "opponent_id": opp, "won": won, "score": m.get("score", ""),
                         "retired": m["retired"], "event_weight": event_weight, "qualifying": m.get('qualifying', False), "delta": round(anchor_delta + rc.get("form_weight", .35) * delta, 3), "expected": round(prob, 5), "precision": m["precision"],
                        "own_atp": integer(m.get(side + "_rank")), "opp_atp": integer(m.get(other + "_rank")),
                        "own_power": pre.get(pid), "opp_power": pre.get(opp)})
        for pid, s, delta, sd, ad, asd in pending:
            states[pid].add(day, s, delta, sd)
            states[pid].anchor += ad
            if s in SURFACES:
                states[pid].anchor_surface[s] += asd
        for pid in {p[0] for p in pending}:
            st = states[pid]
            st.last_strength = st.strength()
            st.last_surface = {s: st.strength(s, rc) for s in SURFACES}
        for pid, delta in basic_delta.items():
            basic[pid] += delta
        if day <= as_of - timedelta(days=7):
            previous = {pid: st.score(config=rc) for pid, st in states.items() if st.total}
        if collect:
            # The database stores pre-date snapshots, not future-adjusted ranks.
            participants = {m[k] for m in batch for k in ("w", "l")}
            snapshots.extend((day.isoformat(), pid, pre.get(pid), round(pre_scores[pid], 4) if pid in pre else None, len(pre)) for pid in sorted(participants))
    prior_ranks = {pid: i + 1 for i, pid in enumerate(sorted(previous, key=lambda p: (-previous[p], p)))}
    for st in states.values():
        st.advance(as_of, rc)
    return states, bio, history, snapshots, predictions, prior_ranks


def build(matches, rankings, config, as_of, health=None, photos=None, current_rankings=None):
    states, bio, history, snapshots, predictions, previous = replay(matches, config, as_of)
    rc = config["rating"]
    start, recent = shift_months(as_of, -12), shift_months(as_of, -3)
    eligible = [pid for pid, st in states.items() if st.total]
    # A current, identity-verified observation is a publication-time prior only.
    # It NEVER enters historical replay, opponent categories, or backtest inputs.
    current = {pid: r for pid,r in (current_rankings or {}).items()
               if r.get('observed_at') and 0 <= (as_of-parse_date(r['observed_at'][:10])).days <= 14 and integer(r.get('rank'))}
    weight = rc.get('official_prior_weight', .35)
    adjustments = {pid: max(-200, min(200, weight * (seed(current[pid]['rank'], rc['baseline']) - states[pid].strength())))
                   for pid in eligible if pid in current}
    score_on = lambda pid,s='Overall': states[pid].score(s, rc) + adjustments.get(pid,0)
    ordered = sorted(eligible, key=lambda p: (-score_on(p), p))
    surface_ranks = {s: {pid: i + 1 for i, pid in enumerate(sorted(eligible, key=lambda p: (-score_on(p,s), p)))} for s in SURFACES}
    rank_day = max((d for d in rankings if d <= as_of), default=None)
    edition = rankings.get(rank_day, {})
    players = []
    for i, pid in enumerate(ordered):
        st, person = states[pid], bio[pid]
        records = sorted([r for r in history[pid] if r["date"] > start.isoformat()], key=lambda r: r["date"], reverse=True)
        stats = {b: {"year": statistics(records, start, b), "recent": statistics(records, recent, b)} for b in ("atp", "power")}
        age = person["age"]
        if age is not None:
            age += (as_of - parse_date(person["bio_date"])).days / 365.25
        flags = []
        if age is not None and age < 21:
            flags.append("Next generation")
        if age is not None and age >= 35:
            flags.append("Veteran")
        inactive = (as_of - st.last).days
        if inactive >= 42:
            flags.append("Inactive")
        if st.total < 15:
            flags.append("Provisional")
        status = (health or {}).get(pid)
        if status:
            required = ("source_url", "reported_at", "review_after", "status", "confidence")
            if not all(status.get(k) for k in required) or not status["source_url"].startswith("https://"):
                raise ValueError(f"Unsourced health report for {pid}")
            if not (parse_date(status["reported_at"]) <= as_of <= parse_date(status["review_after"])):
                status = None
        if status:
            flags.append("Reported status")
        photo = (photos or {}).get(pid)
        if photo and not (str(photo.get("url", "")).startswith("https://") and str(photo.get("license_url", "")).startswith("https://") and photo.get("credit")):
            raise ValueError(f"Photo needs HTTPS URL, credit and license for {pid}")
        official = current.get(pid) or edition.get(pid, {})
        adjustment = adjustments.get(pid, 0)
        strength = st.strength() + adjustment
        score = score_on(pid)
        players.append(dict(person, rank=i + 1, rating=round(score, 2), strength=round(strength, 2),
            availability_adjustment=round(score - strength, 2), age=round(age, 1) if age is not None else None,
            result_strength=round(st.strength(),2), official_adjustment=round(adjustment,2),
            atp_rank=official.get("rank"), atp_points=official.get("points"), atp_date=rank_day.isoformat() if rank_day and pid not in current and official else None,
            official_observed_at=official.get('observed_at'), official_source=official.get('source_url'), official_identity=official.get('id'),
            movement=previous[pid] - (i + 1) if pid in previous and not current else None,
            surfaces={s: {"rank": surface_ranks[s][pid], "rating": round(score_on(pid,s), 2), "matches": st.counts[s], "provisional": st.counts[s] < 12} for s in SURFACES},
            stats=stats, history=records, last_played=st.last.isoformat(), inactive_days=inactive, flags=flags, health=status, photo=photo,
            matches=st.total, tiers=sorted({r["tier"] for r in records}), confidence="Established" if st.total >= 30 else "Developing" if st.total >= 15 else "Provisional"))
    return {"players": players, "as_of": as_of.isoformat(), "window_start_exclusive": start.isoformat(), "recent_start_exclusive": recent.isoformat(),
            "ranking_date": rank_day.isoformat() if rank_day else None, "match_count": sum(len(p["history"]) for p in players) // 2,
            "model_version": VERSION}, snapshots, predictions
