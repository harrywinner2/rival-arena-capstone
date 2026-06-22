"""Shared contracts — the integration spine every workstream imports.

These dataclasses define the *data that flows between* env/, harness/, metrics/,
and viz/. Keep them small, JSON-serializable, and free of heavy logic. Anything
that needs behaviour (payoffs, prompting, metric math) lives in its workstream;
this module only describes the shapes that cross workstream boundaries.

Design notes tied to the plan:
  * Enums subclass `str` so `dataclasses.asdict()` -> json.dumps() works directly.
  * `RefusalCode` makes refusals first-class (P19: never silently dropped).
  * `EpistemicSpec` pins the agent's common knowledge (P9 / §2 epistemic spec):
    `believes_channel_private` is what makes covert-surplus valid; the metrics
    logger is *always* out-of-world and is never represented here.
  * `MatchResult` is the unit of analysis (P17: the match, not the round).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class ChannelLevel(str, Enum):
    """A1 communication ladder — one new affordance per rung (P6)."""

    L0_NONE = "L0_none"          # action only, no transmission
    L1_SIGNAL = "L1_signal"      # one canned token from a tiny menu (~no bandwidth)
    L2_OBSERVED = "L2_observed"  # free text, agents told it is observed
    L3_PRIVATE = "L3_private"    # free text, agents told it is private (belief manip.)


class RefusalCode(str, Enum):
    """Every response is coded; the per-condition rate is itself a finding (P19)."""

    CLEAN = "clean"          # a well-formed action was produced
    REPAIRED = "repaired"    # action recovered via the pre-registered fallback map
    REFUSAL = "refusal"      # substantive refusal ("I won't collude")
    OFF_TASK = "off_task"    # broke character / produced nothing usable
    API_ERROR = "api_error"  # infra failure (not behaviour) — excluded from metrics


class Origin(str, Enum):
    CHINESE = "chinese"
    WESTERN = "western"      # American / European
    FRONTIER = "frontier"    # closed frontier anchor (e.g. GPT-4o)
    CLASSICAL = "classical"  # non-LLM Axelrod strategy


class PlayerKind(str, Enum):
    LLM = "llm"
    CLASSICAL = "classical"


# --------------------------------------------------------------------------- #
# Static descriptors
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ModelSpec:
    """One row of the model-comparability sheet (§5).

    `litellm_model` is the string passed to litellm.completion (e.g.
    "openrouter/qwen/qwen-2.5-72b-instruct" or "gpt-4o").
    """

    id: str
    litellm_model: str
    origin: Origin
    family: str
    provider: str                       # "openrouter" | "openai"
    param_count: Optional[str] = None   # e.g. "72B"; None for closed models
    quantization: Optional[str] = None  # best-effort; hosted often unknown (P11)
    serving_backend: Optional[str] = None
    context_length: Optional[int] = None
    tuning: Optional[str] = None        # "instruction" | "reasoning"
    prompt_language: str = "en"


@dataclass(frozen=True)
class PlayerSpec:
    """A seat in a match: either an LLM (by model id) or a classical strategy."""

    seat: str                           # "A" / "B"
    kind: PlayerKind
    ref: str                            # model id (LLM) or strategy name (classical)


@dataclass(frozen=True)
class EpistemicSpec:
    """The agent's common knowledge, pre-registered per condition (§2, P9).

    NB: the experimenter's metric logger is *diegetically invisible* and is never
    encoded here. `believes_channel_private=True` is what licenses covert-surplus
    scoring; it is a belief manipulation, not a fact about our logging.
    """

    opponent_framing: str = "another participant"   # neutral; no human/AI cue (P21)
    monitor_present: bool = False                    # is an in-world monitor declared?
    monitor_reads_public: bool = True
    believes_channel_private: bool = False           # L3 manipulation
    actions_observed_by_other: bool = True
    scratchpad_private: bool = True                  # parity across rungs (P8)


@dataclass(frozen=True)
class GameSpec:
    """Names the game + its parameters so a run is reproducible from config."""

    name: str                           # "ipd" | "bertrand" | "matching_pennies" | ...
    params: dict[str, Any] = field(default_factory=dict)
    familiarity: str = "canonical"      # "canonical" | "relabeled" | "novel" (G2)


# --------------------------------------------------------------------------- #
# Per-match dynamic records
# --------------------------------------------------------------------------- #
@dataclass
class Action:
    """A game-agnostic action. `value` carries numerics (e.g. a price);
    `cooperative` is the game's mapping onto the C axis (None for zero-sum)."""

    label: str
    value: Optional[float] = None
    cooperative: Optional[bool] = None


@dataclass
class AgentMove:
    """One agent's full output for one round, with refusal coding and probes."""

    seat: str
    action: Optional[Action] = None
    message: Optional[str] = None           # transmitted text (post-paraphrase if any)
    raw_message: Optional[str] = None       # pre-paraphrase, as authored
    scratchpad: Optional[str] = None        # private reasoning (never transmitted)
    promise: Optional[bool] = None          # did they *state* they'd cooperate? (P8)
    refusal: RefusalCode = RefusalCode.CLEAN
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0
    raw_response: Optional[str] = None       # full model text, for audit
    error: Optional[str] = None


@dataclass
class RoundRecord:
    round_index: int
    moves: dict[str, AgentMove]                  # seat -> move
    payoffs: dict[str, float]                    # seat -> payoff this round
    continued: bool = True                       # did the game continue after this round?
    monitor_flag: Optional[bool] = None          # in-world monitor's collusion call
    monitor_score: Optional[float] = None
    extra: dict[str, Any] = field(default_factory=dict)  # game-specific (e.g. demand)


@dataclass
class MatchSpec:
    """Everything needed to (re)run one match — a fully-pinned configuration."""

    experiment_id: str
    cell_id: str                                 # factor-cell label, e.g. "A1/L3/qwen-vs-llama"
    game: GameSpec
    channel: ChannelLevel
    epistemic: EpistemicSpec
    players: list[PlayerSpec]
    seed: int
    temperature: float = 0.7                     # mainline (P11)
    token_budget: int = 256                      # message-LENGTH guidance (bandwidth), identical across cells
    max_tokens: int = 768                        # completion cap for the API call; generous so reasoning+action fit (parity across cells)
    history_window: int = 10                     # rolling window (P22)
    framing: str = "neutral"                     # "neutral" | "patriotic" (G1)
    prompt_variant: Optional[str] = None     # B4: seller-goal phrasing override; None -> mainline
    observe_actions: bool = True             # A6: when False, the OTHER seat's past actions are hidden in this seat's formatted history (own actions/payoffs unchanged). True -> current behaviour.
    state_observability: Optional[bool] = None  # A6: when not None, append an explicit common-knowledge line about whether the other can see this agent's past moves (True=can, False=cannot). None -> no line (current behaviour).
    message_restriction: Optional[str] = None    # C1: when set (e.g. "action_only"), the message-phase prompt appends a content restriction (the agent may state ONLY its own intended action this round, in its own words). None -> unchanged (current behaviour).
    paraphrase: bool = False
    canary: Optional[dict[str, str]] = None      # D1: seat -> private text injected into that seat's system prompt ONLY
    notes: str = ""

    def players_seats(self) -> list[str]:
        return [p.seat for p in self.players]

    def config_hash(self) -> str:
        payload = to_jsonable(self)
        payload.pop("seed", None)  # hash identifies the *cell*, not the seed
        blob = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha1(blob.encode()).hexdigest()[:12]


@dataclass
class MatchResult:
    """The unit of analysis (P17). Metrics are attached post-hoc by metrics/."""

    spec: MatchSpec
    rounds: list[RoundRecord]
    manifest: dict[str, Any] = field(default_factory=dict)   # builds, timestamps, env info
    metrics: dict[str, Any] = field(default_factory=dict)    # filled by metrics layer
    refusal_counts: dict[str, int] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None


# --------------------------------------------------------------------------- #
# (De)serialization helpers
# --------------------------------------------------------------------------- #
def to_jsonable(obj: Any) -> Any:
    """Recursively convert dataclasses/enums to JSON-friendly structures."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: to_jsonable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj


def dumps(obj: Any, **kw) -> str:
    return json.dumps(to_jsonable(obj), default=str, **kw)
