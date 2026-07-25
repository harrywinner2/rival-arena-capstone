"""Why do contingent-punishment rules *negatively* predict lock-in?

Three candidate explanations for the reversed sign found in mediation.py:

  (H1) REVERSE CAUSATION. Rules are uttered in response to defection. A rule then
       marks a match already in trouble. Test: when do rules appear relative to the
       first defection?
  (H2) RULES WORK CONDITIONALLY. A punishment rule is machinery for *sustaining* an
       equilibrium under deviation, so its effect should show up only among matches
       where a deviation actually happened. Test: post-defection recovery.
  (H3) THE DETECTOR IS WRONG. Handled separately in validate_detector.py.

Also tests an alternative mediator the C1 ablation points at: explicit joint-plan /
agreement proposals ("let's both set 13.00") rather than threats.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from conditional import score_series  # noqa: E402
from build_match_table import load  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
RNG = np.random.default_rng(20260724)
FREE = ["L2_observed", "L3_private"]

# Alternative mediator: a proposal of a specific joint plan (no threat required).
AGREEMENT = [
    r"\blet'?s (?:both|all)\b", r"\bwe should both\b", r"\bboth (?:set|post|price|play|choose|hold|charge)\b",
    r"\blet'?s (?:agree|settle|stabili[sz]e|commit|stick)\b",
    r"\bagree(?:d)? (?:on|to)\b", r"\bstabili[sz]e at\b", r"\bcommit to\b",
    r"\bdeal\b", r"\bmutual(?:ly)? (?:benefit|agree|profit)\b",
    r"\bwe (?:can|could|will) both\b",
]
_AGREE_RE = re.compile("|".join(AGREEMENT), re.I)


def boot_diff(a, b, n=4000):
    a = np.asarray(a, float); b = np.asarray(b, float)
    a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
    if len(a) < 3 or len(b) < 3:
        return np.nan, np.nan, np.nan
    obs = a.mean() - b.mean()
    d = np.array([RNG.choice(a, len(a), True).mean() - RNG.choice(b, len(b), True).mean()
                  for _ in range(n)])
    return obs, float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main() -> None:
    df = load()
    sc = score_series(df["message"])
    df = pd.concat([df.reset_index(drop=True), sc.reset_index(drop=True)], axis=1)
    df["agreement"] = df["message"].map(
        lambda t: int(bool(_AGREE_RE.search(t))) if isinstance(t, str) else 0)

    df = df[df.channel.isin(FREE)].copy()
    key = ["experiment_id", "cell_id", "seed"]

    out = ["# Rule-timing diagnostics\n",
           "Free-text matches only (L2/L3). Explains the reversed mediation sign.\n"]

    # ---------------- H1: rules follow defection ----------------
    out.append("\n## H1 — Are rules a *response* to defection?\n")
    rows = []
    for k, g in df.groupby(key, dropna=False):
        g = g.sort_values("round_index")
        if g.game.iloc[0] != "ipd" or g.cooperative.isna().all():
            continue
        # per round: did either seat defect?
        per_round = g.groupby("round_index").agg(
            defect=("cooperative", lambda s: int((s == 0).any())),
            rule=("rule", "max"),
        ).reset_index()
        if per_round.empty:
            continue
        first_def = per_round.loc[per_round.defect == 1, "round_index"]
        first_def = int(first_def.iloc[0]) if len(first_def) else None
        rule_rounds = per_round.loc[per_round.rule == 1, "round_index"].tolist()
        rows.append(dict(
            match=str(k), first_def=first_def,
            first_rule=int(rule_rounds[0]) if rule_rounds else None,
            n_rule=len(rule_rounds), n_rounds=len(per_round),
            rule_before_def=int(bool(rule_rounds and first_def is not None
                                     and rule_rounds[0] < first_def)),
            rule_after_def=int(bool(rule_rounds and first_def is not None
                                    and rule_rounds[0] >= first_def)),
            any_rule=int(bool(rule_rounds)),
        ))
    t = pd.DataFrame(rows)
    has = t[t.any_rule == 1]
    both = has[has.first_def.notna()]
    out.append(f"- IPD free-text matches analysed: {len(t)}")
    out.append(f"- matches containing >=1 rule: {len(has)} ({len(has)/max(len(t),1):.1%})")
    if len(both):
        out.append(f"- of those with a defection, rule appears **after** the first "
                   f"defection in {both.rule_after_def.mean():.1%} of matches, "
                   f"before it in {both.rule_before_def.mean():.1%}")
    # round-level hazard: P(rule at t | any defection before t) vs P(rule at t | none)
    hz = []
    for k, g in df[df.game == "ipd"].groupby(key, dropna=False):
        g = g.sort_values("round_index")
        pr = g.groupby("round_index").agg(defect=("cooperative", lambda s: int((s == 0).any())),
                                          rule=("rule", "max")).reset_index()
        seen = False
        for _, r in pr.iterrows():
            hz.append(dict(prior_defect=int(seen), rule=int(r["rule"])))
            seen = seen or bool(r["defect"])
    hzd = pd.DataFrame(hz)
    if len(hzd):
        a = hzd[hzd.prior_defect == 1].rule.values
        b = hzd[hzd.prior_defect == 0].rule.values
        obs, lo, hi = boot_diff(a, b)
        out.append(f"\n**Round-level hazard.** P(rule this round | a defection already "
                   f"happened) = {a.mean():.3f} (n={len(a)}) vs "
                   f"P(rule | no defection yet) = {b.mean():.3f} (n={len(b)}); "
                   f"difference **{obs:+.3f}** [{lo:+.3f}, {hi:+.3f}].")

    # ---------------- H2: conditional efficacy ----------------
    out.append("\n\n## H2 — Do rules help *after* a deviation? (recovery analysis)\n")
    out.append("For each round where a defection has already occurred, does a "
               "contingent-punishment rule uttered at round t predict mutual "
               "cooperation at t+1?\n")
    rec = []
    for k, g in df[df.game == "ipd"].groupby(key, dropna=False):
        g = g.sort_values("round_index")
        pr = g.groupby("round_index").agg(
            defect=("cooperative", lambda s: int((s == 0).any())),
            mutual_coop=("cooperative", lambda s: int((s == 1).all() and len(s) >= 2)),
            rule=("rule", "max"), agreement=("agreement", "max"),
        ).reset_index()
        seen = False
        for i in range(len(pr) - 1):
            if seen:
                rec.append(dict(rule=int(pr.rule.iloc[i]),
                                agreement=int(pr.agreement.iloc[i]),
                                next_mutual=int(pr.mutual_coop.iloc[i + 1]),
                                cur_defect=int(pr.defect.iloc[i])))
            seen = seen or bool(pr.defect.iloc[i])
    rdf = pd.DataFrame(rec)
    if len(rdf):
        obs, lo, hi = boot_diff(rdf[rdf.rule == 1].next_mutual.values,
                                rdf[rdf.rule == 0].next_mutual.values)
        out.append(f"- post-deviation rounds analysed: {len(rdf)}")
        out.append(f"- P(mutual cooperation next round | rule sent) = "
                   f"{rdf[rdf.rule==1].next_mutual.mean():.3f} (n={(rdf.rule==1).sum()})")
        out.append(f"- P(mutual cooperation next round | no rule) = "
                   f"{rdf[rdf.rule==0].next_mutual.mean():.3f} (n={(rdf.rule==0).sum()})")
        out.append(f"- **difference {obs:+.3f}, 95% CI [{lo:+.3f}, {hi:+.3f}]**")
        # restricted to rounds where a defection just happened
        sub = rdf[rdf.cur_defect == 1]
        if len(sub) > 20:
            obs2, lo2, hi2 = boot_diff(sub[sub.rule == 1].next_mutual.values,
                                       sub[sub.rule == 0].next_mutual.values)
            out.append(f"\nRestricted to rounds where a defection occurred *this* round "
                       f"(n={len(sub)}): rule {sub[sub.rule==1].next_mutual.mean():.3f} "
                       f"vs no-rule {sub[sub.rule==0].next_mutual.mean():.3f}, "
                       f"difference **{obs2:+.3f}** [{lo2:+.3f}, {hi2:+.3f}]")

    # ---------------- alternative mediator: agreement proposals ----------------
    out.append("\n\n## Alternative mediator — explicit joint-plan / agreement proposals\n")
    agg = df.groupby(key, dropna=False).agg(
        game=("game", "first"), channel=("channel", "first"), spec=("spec", "first"),
        coop=("cooperative", "mean"), price=("price", "mean"),
        agreement=("agreement", "max"), rule=("rule", "max"),
        agree_frac=("agreement", "mean"),
    ).reset_index()
    agg["lockin"] = (agg.coop > 0.8).astype(float)
    ipd = agg[(agg.game == "ipd") & agg.lockin.notna()]
    obs, lo, hi = boot_diff(ipd[ipd.agreement == 1].lockin.values,
                            ipd[ipd.agreement == 0].lockin.values)
    out.append(f"- IPD free-text, agreement present n={(ipd.agreement==1).sum()}, "
               f"lock-in {ipd[ipd.agreement==1].lockin.mean():.3f}; "
               f"absent n={(ipd.agreement==0).sum()}, "
               f"lock-in {ipd[ipd.agreement==0].lockin.mean():.3f}")
    out.append(f"- **difference {obs:+.3f}, 95% CI [{lo:+.3f}, {hi:+.3f}]**")

    txt = "\n".join(out)
    (OUT / "rule_timing.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
