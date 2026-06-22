"""Model registry — loads configs/models.yaml into ModelSpec objects and
resolves named pairs for the origin factor.
"""

from __future__ import annotations

import functools

import yaml

from .config import CONFIG_DIR
from .schemas import ModelSpec, Origin


@functools.lru_cache(maxsize=1)
def _raw() -> dict:
    with open(CONFIG_DIR / "models.yaml") as f:
        return yaml.safe_load(f)


@functools.lru_cache(maxsize=1)
def all_models() -> dict[str, ModelSpec]:
    out: dict[str, ModelSpec] = {}
    for mid, row in _raw()["models"].items():
        out[mid] = ModelSpec(
            id=mid,
            litellm_model=row["litellm_model"],
            origin=Origin(row["origin"]),
            family=row["family"],
            provider=row["provider"],
            param_count=row.get("param_count"),
            quantization=row.get("quantization"),
            serving_backend=row.get("serving_backend", row["provider"]),
            context_length=row.get("context_length"),
            tuning=row.get("tuning"),
            prompt_language=row.get("prompt_language", "en"),
        )
    return out


def get_model(model_id: str) -> ModelSpec:
    try:
        return all_models()[model_id]
    except KeyError as e:
        raise KeyError(
            f"Unknown model id {model_id!r}. Known: {sorted(all_models())}"
        ) from e


def get_pair(pair_name: str) -> list[str]:
    """Return the two model ids for a named pair (e.g. 'cross_origin')."""
    pairs = _raw().get("pairs", {})
    if pair_name == "smoke_pair":
        return list(_raw()["smoke_pair"])
    if pair_name not in pairs:
        raise KeyError(f"Unknown pair {pair_name!r}. Known: {sorted(pairs)}")
    return list(pairs[pair_name])


def comparability_row(model_id: str) -> dict:
    """One row of the model-comparability sheet, for the run manifest (§5)."""
    m = get_model(model_id)
    return {
        "id": m.id,
        "litellm_model": m.litellm_model,
        "origin": m.origin.value,
        "family": m.family,
        "param_count": m.param_count,
        "quantization": m.quantization,
        "serving_backend": m.serving_backend,
        "context_length": m.context_length,
        "tuning": m.tuning,
        "prompt_language": m.prompt_language,
    }
