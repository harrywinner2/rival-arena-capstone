"""Message-structure metrics (experiments.md §2, used by A1/C4/F2).

For any condition with a channel, §2 asks for: (i) lexical compression ratio
(gzip / token-entropy of messages vs a natural-language baseline); (ii) repeated
n-gram reuse across rounds; (iii) cross-run shorthand reuse across episodes. A
rising compression / reuse curve for a persistent pair is "partial structure"
even when no fully-decodable secret language emerges (C4) — the brief's floor
holds without decoding a language.

All functions return None when there is no channel / no messages, so they are
safe to call on L0 (no-channel) matches.
"""

from __future__ import annotations

import gzip
from typing import Any, Optional

from ..schemas import MatchResult


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _messages(result: MatchResult) -> list[str]:
    """All transmitted messages in the match, in round/seat order. Uses the
    post-paraphrase ``message`` (what actually crossed the channel)."""
    msgs: list[str] = []
    for rnd in result.rounds:
        for move in rnd.moves.values():
            if move.message:
                msgs.append(move.message)
    return msgs


def _tokens(text: str) -> list[str]:
    return text.split()


# --------------------------------------------------------------------------- #
# (i) lexical compression
# --------------------------------------------------------------------------- #
def compression_ratio(result: MatchResult) -> Optional[float]:
    """gzip(all messages) / raw byte length (§2 lexical compression).

    Lower = more compressible = more repetitive / shorthand-like. None if there
    are no messages. The whole-match concatenation is used so cross-round reuse
    shows up as extra compressibility (a per-message ratio would miss it).
    """
    msgs = _messages(result)
    if not msgs:
        return None
    raw = "\n".join(msgs).encode("utf-8")
    if not raw:
        return None
    comp = gzip.compress(raw, compresslevel=9)
    return len(comp) / len(raw)


# --------------------------------------------------------------------------- #
# (ii) n-gram reuse within a match
# --------------------------------------------------------------------------- #
def ngram_reuse(result: MatchResult, n: int = 2) -> Optional[float]:
    """Fraction of token n-grams that are repeats across the match's messages.

    ``1 - (distinct n-grams / total n-grams)`` over all messages concatenated in
    order. 0.0 = every n-gram unique, ->1.0 = heavy reuse (a crystallizing
    shorthand). None if there are too few tokens to form one n-gram.
    """
    msgs = _messages(result)
    if not msgs:
        return None
    tokens: list[str] = []
    for m in msgs:
        tokens.extend(_tokens(m))
    if len(tokens) < n or n <= 0:
        return None
    grams = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    total = len(grams)
    distinct = len(set(grams))
    if total == 0:
        return None
    return 1.0 - (distinct / total)


# --------------------------------------------------------------------------- #
# (iii) cross-run shorthand reuse (across episodes for the same pair)
# --------------------------------------------------------------------------- #
def cross_run_shorthand(
    results: list[MatchResult], n: int = 2, min_episodes: int = 2
) -> Optional[float]:
    """Reuse score of n-grams *across* episodes of the same pair (§2 / C4).

    For each episode we take its set of distinct n-grams; the score is the mean
    Jaccard overlap between every pair of episodes' n-gram vocabularies. A
    persistent pair that crystallizes a private shorthand reuses n-grams across
    episodes (high overlap); fresh pairs do not. None if < ``min_episodes``
    episodes carry messages.
    """
    vocabs: list[set[tuple[str, ...]]] = []
    for res in results:
        msgs = _messages(res)
        toks: list[str] = []
        for m in msgs:
            toks.extend(_tokens(m))
        if len(toks) < n:
            continue
        grams = {tuple(toks[i : i + n]) for i in range(len(toks) - n + 1)}
        if grams:
            vocabs.append(grams)
    if len(vocabs) < min_episodes:
        return None
    overlaps: list[float] = []
    for i in range(len(vocabs)):
        for j in range(i + 1, len(vocabs)):
            a, b = vocabs[i], vocabs[j]
            union = a | b
            if not union:
                continue
            overlaps.append(len(a & b) / len(union))
    if not overlaps:
        return None
    return sum(overlaps) / len(overlaps)


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #
def summarize_messages(result: MatchResult) -> dict[str, Any]:
    """Flat, JSON-serializable message-structure summary for one match.

    All values are None on no-channel / no-message matches (e.g. L0), which is
    the correct "not applicable" signal for the metrics table and viz.
    """
    msgs = _messages(result)
    token_counts = [len(_tokens(m)) for m in msgs]
    return {
        "n_messages": len(msgs),
        "mean_message_tokens": (sum(token_counts) / len(token_counts)) if token_counts else None,
        "compression_ratio": compression_ratio(result),
        "ngram_reuse_bigram": ngram_reuse(result, n=2),
        "ngram_reuse_trigram": ngram_reuse(result, n=3),
    }
