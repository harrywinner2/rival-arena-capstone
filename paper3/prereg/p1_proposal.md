# Pre-registration — P1: the joint-proposal predicate

**Status:** locked before any P1 seed is run. **Date:** 2026-07-24.
**Analyst:** Rival Arena team. **Seeds:** offset 300 (disjoint from A1 pilot 0–119,
A1 confirmatory 100–119, and C1 0–19).

## 1. Motivation

Prior work (GameSec poster; Zenodo extended report) established that a free-text
channel raises IPD lock-in from 0.15 to 0.60 while a fixed menu signal does not, and
attributed the effect to *semantic bandwidth* ("content is the lever"). Re-analysis of
the released corpus (2,082 matches) does not support a graded-content account:

- contingent punishment rules do not mediate the effect and appear *after* trouble
  (78.6% of first rules follow the first defection; round-level hazard 0.173 vs 0.043);
- no measured content class (threat, joint plan, affirmation, solicitation) predicts
  closing cooperation once opening behaviour is controlled;
- message length trends the *wrong way* for a bandwidth account;
- in an independent apparatus (SMS throughput probe), the single 60-character text that
  lifts a pair from 0.45 to 0.80 lock-in carries a punishment rule in only 5% of cases.

What *does* separate every coordinating arm from every non-coordinating arm in the
existing corpus is whether the channel permits a **joint proposal** (first-person-plural
commissive, "let's both do X") as opposed to only an **own intention**
(first-person-singular commissive, "I will do X"):

| arm | proposal rate/message | lock-in |
|---|---:|---:|
| L0 none | 0.000 | 0.113 |
| L1 menu signal | 0.000 | 0.057 |
| C1 selected | 0.000 | 0.050 |
| C1 restricted (self-authored, action-only) | 0.000 | 0.000 |
| C1 free | 1.000 | 0.550 |
| L2 observed | 0.918 | 0.599 |
| L3 private | 0.939 | 0.651 |

**This arm-level separation is confounded with message length** (C1 restricted averages
20.7 characters, C1 free 143). P1 breaks that confound by holding length approximately
constant and varying only the grammatical person of the commissive.

## 2. Hypothesis

**H1 (primary).** A channel restricted to short *joint proposals* produces IPD lock-in
comparable to unrestricted free text, and substantially above a channel restricted to
length-matched *own intentions*.

**H0.** Lock-in under `joint_proposal_only` is no higher than under
`own_intention_only` — the effect requires open-ended content, not the proposal form.

## 3. Design

- Game: IPD, canonical payoffs, `continuation_prob = 0.97`, `max_rounds = 20`.
- Pair: `same_origin_cn` (Qwen2.5-72B x DeepSeek-V3), matching A1 and C1.
- Seeds: 30 per arm, offset 300. Same seed set across arms (paired).
- Arms (5):

  | arm | channel | restriction |
  |---|---|---|
  | `none` | L0_NONE | — |
  | `menu` | L1_SIGNAL | — (replication anchor) |
  | `intention` | L2_OBSERVED | `own_intention_only` |
  | `proposal` | L2_OBSERVED | `joint_proposal_only` |
  | `free` | L2_OBSERVED | — (ceiling anchor) |

- Restriction texts are fixed in `paper3/src/p1_experiment.py` and are length-matched:
  both instruct exactly one short sentence, one clause, no reasoning or justification.

## 4. Primary outcome and analysis

- **Primary outcome:** match-level lock-in proportion (mean cooperation > 0.8), with
  Wilson 95% intervals — the repo's standing primary outcome for bimodal matches.
- **Primary contrast:** `proposal` vs `intention`, Fisher exact, two-sided,
  alpha = 0.05, fixed in advance.
- **Secondary contrasts:** `proposal` vs `free`; `intention` vs `none`;
  `free` vs `none` (replication of the established effect).
- **Multiplicity:** the four secondary contrasts are reported under
  Benjamini–Hochberg FDR at 0.05. The primary contrast is not corrected.
- **Effect size:** risk difference with a Newcombe interval.

## 5. Power

At n = 30/arm, Fisher exact detects a risk difference of 0.35 (e.g. 0.15 vs 0.50) with
power >= 0.80 at alpha = 0.05. The observed C1 restricted-vs-free gap is 0.55, so the
design is powered for an effect half that size. **We are not powered to establish
equivalence** between `proposal` and `free`; if that contrast is non-significant we will
report it as under-powered, not as equivalence (following the A3 precedent).

## 6. Manipulation check (must pass before H1 is interpreted)

Using the detector in `paper3/src/proposal_predicate.py`, on delivered messages:

- `proposal` arm: proposal rate >= 0.80, intention-only rate <= 0.20;
- `intention` arm: intention-only rate >= 0.80, proposal rate <= 0.20;
- mean message length in the two restricted arms within a factor of 1.5 of each other.

If the manipulation check fails, the arm is reported as a failed manipulation and H1 is
not tested on it.

## 7. Exclusions and coding

- Refusals are coded as outcomes, never dropped.
- API/transport errors are excluded from behavioural metrics and reported separately as
  `api_error_rate`.
- No match is excluded post hoc for any other reason.

## 8. Stop rule

One run at n = 30/arm. If the manipulation check passes and the primary contrast is
significant, a replication on a second pair (`cross_origin`) at the same n is run and
reported as a pre-specified replication. No further arms are added to this
pre-registration.

## 9. What would falsify the account

If `proposal` ≈ `intention` (both low), the joint-proposal predicate is wrong and the
effect requires open-ended content — supporting the original bandwidth/content reading.
That outcome will be reported as such.
