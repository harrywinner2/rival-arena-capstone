#!/usr/bin/env python3
"""Measure text-to-latent fidelity on frozen arena deployment snapshots."""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
REPO_CODE = ROOT.parent / "code"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO_CODE))

from l4_arena.arena import action_codebook
from l4_arena.jobs import atomic_json
from l4_arena.link import OuterLink
from l4_arena.training import choose_cuda_dtype, seed_everything
from rival_arena.env.ipd import IteratedPrisonersDilemma
from rival_arena.env.market import BertrandPricing
from run_arena import action_prompt, comm_prompt, render_history


CONTROLS = ("trained", "random", "zero", "shuffled", "token_oracle")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--matches", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--seed", type=int, default=20260724)
    parser.add_argument("--checkpoint-every", type=int, default=8)
    parser.add_argument(
        "--layout",
        choices=("legacy", "matched"),
        default="legacy",
        help="matched appends readable-token and latent payloads after one identical prompt",
    )
    parser.add_argument(
        "--exclude-snapshots",
        type=Path,
        help="Optional prior snapshots.jsonl whose snapshot IDs must be excluded",
    )
    return parser.parse_args()


def game_for(name: str):
    if name == "ipd":
        return IteratedPrisonersDilemma({}, familiarity="canonical")
    if name == "bertrand":
        return BertrandPricing({"demand_spec": "novel"}, familiarity="canonical")
    raise ValueError(f"unsupported game: {name}")


def candidate_distribution(model, tokenizer, prompt: str, codebook, latent=None):
    prompt_ids = tokenizer(
        prompt, return_tensors="pt", truncation=True, max_length=768
    ).input_ids.cuda()
    with torch.inference_mode():
        prompt_embeds = model.get_input_embeddings()(prompt_ids)
        if latent is not None:
            prompt_embeds = torch.cat([prompt_embeds, latent], dim=1)
        prefix = prompt_embeds.shape[1]
        scores = []
        for code, _action in codebook:
            tokens = tokenizer(
                f" {code}", add_special_tokens=False, return_tensors="pt"
            ).input_ids.cuda()
            combined = torch.cat(
                [prompt_embeds, model.get_input_embeddings()(tokens)], dim=1
            )
            mask = torch.ones(
                combined.shape[:2], dtype=torch.long, device=combined.device
            )
            logits = model(
                inputs_embeds=combined, attention_mask=mask, use_cache=False
            ).logits
            prediction = logits[:, prefix - 1 : prefix - 1 + tokens.shape[1], :]
            log_probs = torch.log_softmax(prediction.float(), dim=-1)
            token_scores = log_probs.gather(-1, tokens.unsqueeze(-1)).squeeze(-1)
            scores.append(float(token_scores.mean()))
    return torch.softmax(torch.tensor(scores, dtype=torch.float64), dim=0).numpy()


def sender_states(model, tokenizer, prompt: str, message: str) -> tuple[torch.Tensor, torch.Tensor]:
    prompt_ids = tokenizer(
        prompt, return_tensors="pt", truncation=True, max_length=768
    ).input_ids.cuda()
    message_ids = tokenizer(
        message,
        add_special_tokens=False,
        return_tensors="pt",
        truncation=True,
        max_length=24,
    ).input_ids.cuda()
    if message_ids.shape[1] == 0:
        raise ValueError("empty saved message")
    combined = torch.cat([prompt_ids, message_ids], dim=1)
    with torch.inference_mode():
        output = model(combined, output_hidden_states=True, use_cache=False)
        hidden = output.hidden_states[-1][:, -message_ids.shape[1] :, :].float()
        token_embeds = model.get_input_embeddings()(message_ids)
    return hidden, token_embeds


def matched_action_prompt(game, seat: str, history, codebook) -> str:
    mappings = "; ".join(
        f"CODE {code} = {action.label}" for code, action in codebook
    )
    return (
        f"You are participant {seat}.\n{game.describe_for_prompt(seat)}\n\n"
        f"History:\n{render_history(history, seat)}\n"
        "The peer's communication payload is appended immediately after this "
        "instruction. Use the payload when deciding. It may be supplied as readable "
        "token embeddings or as a private continuous representation.\n"
        f"Choose your action now. For this decision only, the legal choices are "
        f"randomly coded: {mappings}. Choose the code corresponding to your "
        "preferred action.\nPeer payload:"
    )


def divergences(teacher: np.ndarray, student: np.ndarray) -> dict[str, float]:
    epsilon = 1e-12
    kl = float(np.sum(teacher * (np.log(teacher + epsilon) - np.log(student + epsilon))))
    return {
        "kl": kl,
        "total_variation": float(0.5 * np.abs(teacher - student).sum()),
        "top1_agreement": float(np.argmax(teacher) == np.argmax(student)),
    }


def snapshot_id(record: dict[str, Any], round_index: int, seat: str) -> str:
    return f"{record['match_id']}/round-{round_index + 1}/seat-{seat}"


def main() -> None:
    args = parse_args()
    if args.samples < 16:
        raise SystemExit("use at least 16 snapshots")
    seed_everything(args.seed)
    dtype = choose_cuda_dtype()
    token = os.environ.get("HF_TOKEN") or None
    tokenizer = AutoTokenizer.from_pretrained(args.model, token=token)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, token=token, torch_dtype=dtype, low_cpu_mem_usage=True
    ).cuda().eval()
    model.config.use_cache = False
    for parameter in model.parameters():
        parameter.requires_grad_(False)

    saved = torch.load(args.job_dir / "faithful_link.pt", map_location="cpu", weights_only=True)
    if saved["model"] != args.model:
        raise SystemExit("model mismatch")
    dimension = int(model.config.hidden_size)
    trained = OuterLink(dimension, dimension, hidden_dim=min(1024, dimension)).cuda().float().eval()
    trained.load_state_dict(saved["link"])
    seed_everything(args.seed + 1)
    random_link = OuterLink(dimension, dimension, hidden_dim=min(1024, dimension)).cuda().float().eval()

    excluded: set[str] = set()
    if args.exclude_snapshots:
        if not args.exclude_snapshots.exists():
            raise SystemExit(f"missing exclusion file: {args.exclude_snapshots}")
        for line in args.exclude_snapshots.read_text().splitlines():
            if line.strip():
                excluded.add(json.loads(line)["snapshot_id"])
    records = [json.loads(line) for line in args.matches.read_text().splitlines() if line.strip()]
    candidates = []
    for record in records:
        for round_index, round_record in enumerate(record["rounds"]):
            for seat in ("A", "B"):
                other = "B" if seat == "A" else "A"
                identifier = snapshot_id(record, round_index, seat)
                if round_record[other].get("internal_message") and identifier not in excluded:
                    candidates.append((record, round_index, seat))
    random.Random(args.seed).shuffle(candidates)
    candidates = candidates[: min(args.samples, len(candidates))]

    output_name = (
        "arena_context_fidelity_matched_v2"
        if args.layout == "matched"
        else "arena_context_fidelity_v1"
    )
    output = args.job_dir / output_name
    output.mkdir(parents=True, exist_ok=True)
    rows_path = output / "snapshots.jsonl"
    completed = set()
    results = []
    if rows_path.exists():
        for line in rows_path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                completed.add(row["snapshot_id"])
                results.append(row)

    manifest = {
        "job_id": args.job_id,
        "model": args.model,
        "source_matches": str(args.matches),
        "requested_samples": args.samples,
        "available_snapshots": len(candidates),
        "excluded_snapshots": len(excluded),
        "seed": args.seed,
        "layout": args.layout,
        "link_config_fingerprint": saved["config_fingerprint"],
        "controls": list(CONTROLS),
        "saved_message_tokens_reconstructed_from_text": True,
        "primary_gate": "trained KL must beat shuffled and random on arena action distributions",
    }
    atomic_json(output / "manifest.json", manifest)
    started = time.time()
    for index, (record, round_index, seat) in enumerate(candidates, 1):
        identifier = snapshot_id(record, round_index, seat)
        if identifier in completed:
            continue
        game = game_for(record["game"])
        history = record["rounds"][:round_index]
        other = "B" if seat == "A" else "A"
        message = record["rounds"][round_index][other]["internal_message"]
        codebook = action_codebook(
            game.action_menu(seat),
            f"{record['game']}/{record['seed']}/{round_index}/{seat}",
        )
        hidden, token_embeds = sender_states(
            model, tokenizer, comm_prompt(game, other, history), message
        )
        if args.layout == "matched":
            teacher_prompt = matched_action_prompt(game, seat, history, codebook)
            latent_prompt = teacher_prompt
            teacher = candidate_distribution(
                model, tokenizer, teacher_prompt, codebook, token_embeds
            )
        else:
            teacher_prompt = action_prompt(game, seat, history, message, codebook)
            latent_prompt = action_prompt(game, seat, history, None, codebook)
            teacher = candidate_distribution(
                model, tokenizer, teacher_prompt, codebook
            )
        with torch.inference_mode():
            mapped = trained(hidden).to(dtype)
            random_mapped = random_link(hidden).to(dtype)
            generator = torch.Generator(device="cuda")
            generator.manual_seed(args.seed + index)
            order = torch.randperm(mapped.shape[1], generator=generator, device="cuda")
            latents = {
                "trained": mapped,
                "random": random_mapped,
                "zero": torch.zeros_like(mapped),
                "shuffled": mapped[:, order, :],
                "token_oracle": token_embeds,
            }
        metrics = {}
        distributions = {"text": teacher.tolist()}
        for name, latent in latents.items():
            student = candidate_distribution(
                model, tokenizer, latent_prompt, codebook, latent
            )
            distributions[name] = student.tolist()
            metrics[name] = divergences(teacher, student)
        row = {
            "snapshot_id": identifier,
            "game": record["game"],
            "seed": record["seed"],
            "round": round_index + 1,
            "seat": seat,
            "message": message,
            "metrics": metrics,
            "action_distributions": distributions,
        }
        with rows_path.open("a") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        results.append(row)
        completed.add(identifier)
        if index == 1 or index % args.checkpoint_every == 0:
            print(f"[{len(completed)}/{len(candidates)}] {identifier}")

    grouped: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in results:
        for control, metrics in row["metrics"].items():
            for metric, value in metrics.items():
                grouped[control][metric].append(float(value))
    summary = {
        control: {
            metric: float(np.mean(values))
            for metric, values in metrics.items()
        }
        for control, metrics in grouped.items()
    }
    trained_kl = summary["trained"]["kl"]
    gate = {
        "trained_kl_beats_random": trained_kl < summary["random"]["kl"],
        "trained_kl_beats_shuffled": trained_kl < summary["shuffled"]["kl"],
    }
    gate["pass"] = bool(all(gate.values()))
    report = {
        "job_id": args.job_id,
        "snapshots": len(results),
        "summary": summary,
        "gate": gate,
        "elapsed_seconds": time.time() - started,
    }
    atomic_json(output / "arena_context_fidelity_report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
