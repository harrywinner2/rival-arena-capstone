#!/usr/bin/env python3
"""Train a faithful representational link while keeping the base LM frozen.

Teacher: the frozen receiver reads the collaborator's neutral text.
Student: the same frozen receiver sees only mapped sender hidden states.
The link minimizes KL divergence between teacher and student next-token
distributions over a short answer continuation. Rival-game data and rewards never
enter this training loop.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

import torch
import torch.nn.functional as F
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from l4_arena.jobs import ResultClient, atomic_json
from l4_arena.link import OuterLink
from l4_arena.training import (
    TrainConfig,
    capture_rng_state,
    choose_cuda_dtype,
    extract_alpaca_example,
    load_checkpoint,
    restore_rng_state,
    save_checkpoint_atomic,
    seed_everything,
)

CONTEXT = (
    "You are solving a benign assistance task. A collaborator supplied the "
    "following information through a private representation. Respond usefully.\n"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--dataset", default="yahma/alpaca-cleaned")
    parser.add_argument("--dataset-split", default="train")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--grad-accumulation", type=int, default=4)
    parser.add_argument("--max-message-tokens", type=int, default=24)
    parser.add_argument("--max-target-tokens", type=int, default=12)
    parser.add_argument("--checkpoint-every", type=int, default=25)
    parser.add_argument("--seed", type=int, default=20260722)
    parser.add_argument("--fresh", action="store_true")
    return parser.parse_args()


def token_ids(tokenizer, text: str, maximum: int) -> torch.Tensor:
    encoded = tokenizer(
        text,
        add_special_tokens=False,
        truncation=True,
        max_length=maximum,
        return_tensors="pt",
    ).input_ids
    if encoded.shape[1] == 0:
        raise ValueError("text tokenized to an empty sequence")
    return encoded.cuda()


def continuation_logits(logits: torch.Tensor, prefix_length: int, target_length: int) -> torch.Tensor:
    start = prefix_length - 1
    end = start + target_length
    return logits[:, start:end, :]


def report_to_receiver(client: ResultClient | None, stage: str, payload: dict) -> None:
    if client is None:
        return
    try:
        client.status(stage, payload)
    except Exception as error:
        print(f"receiver status failed (training continues): {type(error).__name__}")


def main() -> None:
    args = parse_args()
    if args.steps <= 0 or args.grad_accumulation <= 0:
        raise SystemExit("steps and grad accumulation must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    config = TrainConfig(
        model=args.model,
        dataset=args.dataset,
        dataset_split=args.dataset_split,
        steps=args.steps,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        grad_accumulation=args.grad_accumulation,
        max_message_tokens=args.max_message_tokens,
        max_target_tokens=args.max_target_tokens,
        checkpoint_every=args.checkpoint_every,
        seed=args.seed,
    )
    seed_everything(config.seed)
    dtype = choose_cuda_dtype()
    gpu = torch.cuda.get_device_properties(0)
    print(f"GPU: {gpu.name} ({gpu.total_memory / 1024**3:.1f} GiB); dtype={dtype}")
    if gpu.total_memory < 14 * 1024**3:
        raise SystemExit("at least 14 GiB GPU memory is required")

    token = os.environ.get("HF_TOKEN") or None
    tokenizer = AutoTokenizer.from_pretrained(config.model, token=token)
    model = AutoModelForCausalLM.from_pretrained(
        config.model,
        token=token,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
    ).cuda().eval()
    model.config.use_cache = False
    for parameter in model.parameters():
        parameter.requires_grad_(False)

    dimension = int(model.config.hidden_size)
    link = OuterLink(dimension, dimension, hidden_dim=min(1024, dimension)).cuda().float()
    optimizer = torch.optim.AdamW(
        link.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    checkpoint_path = args.output / "checkpoint.pt"
    start_step = 0
    examples_seen = 0
    losses: list[float] = []
    if not args.fresh:
        checkpoint = load_checkpoint(checkpoint_path, config.fingerprint())
        if checkpoint:
            link.load_state_dict(checkpoint["link"])
            optimizer.load_state_dict(checkpoint["optimizer"])
            start_step = int(checkpoint["step"])
            examples_seen = int(checkpoint["examples_seen"])
            losses = list(checkpoint.get("losses", []))
            restore_rng_state(checkpoint["rng"])
            print(f"resuming at optimizer step {start_step}, example {examples_seen}")

    receiver_url = os.environ.get("L4_RECEIVER_URL")
    receiver_token = os.environ.get("L4_RECEIVER_TOKEN")
    client = (
        ResultClient(receiver_url, receiver_token, args.job_id)
        if receiver_url and receiver_token
        else None
    )
    manifest = {
        "job_id": args.job_id,
        "objective": "teacher_text_vs_student_latent_continuation_kl",
        "base_weights_frozen": True,
        "rival_game_training_data": False,
        "config": asdict(config),
        "config_fingerprint": config.fingerprint(),
        "gpu": gpu.name,
        "gpu_memory_bytes": gpu.total_memory,
        "dtype": str(dtype),
        "torch": torch.__version__,
        "link_parameters": link.trainable_parameter_count,
    }
    atomic_json(args.output / "manifest.json", manifest)
    report_to_receiver(client, "training_started", manifest)

    dataset = load_dataset(
        config.dataset,
        split=config.dataset_split,
        streaming=True,
        token=token,
    ).shuffle(seed=config.seed, buffer_size=2_000)
    iterator = iter(dataset)
    for _ in range(examples_seen):
        next(iterator)

    context_ids = token_ids(tokenizer, CONTEXT, 48)
    context_embeds = model.get_input_embeddings()(context_ids).detach()
    optimizer.zero_grad(set_to_none=True)
    optimizer_step = start_step
    accumulated = 0
    running_loss = 0.0
    started = time.time()

    while optimizer_step < config.steps:
        row = next(iterator)
        examples_seen += 1
        example = extract_alpaca_example(row)
        if example is None:
            continue
        message, target = example
        message_ids = token_ids(tokenizer, message, config.max_message_tokens)
        target_ids = token_ids(tokenizer, target, config.max_target_tokens)

        with torch.no_grad():
            sender = model(message_ids, output_hidden_states=True, use_cache=False)
            sender_hidden = sender.hidden_states[-1].float()
            teacher_ids = torch.cat([context_ids, message_ids, target_ids], dim=1)
            teacher = model(teacher_ids, use_cache=False)
            teacher_prefix = context_ids.shape[1] + message_ids.shape[1]
            teacher_logits = continuation_logits(
                teacher.logits, teacher_prefix, target_ids.shape[1]
            ).float()

        mapped = link(sender_hidden).to(dtype)
        target_embeds = model.get_input_embeddings()(target_ids).detach()
        student_embeds = torch.cat([context_embeds, mapped, target_embeds], dim=1)
        attention_mask = torch.ones(
            student_embeds.shape[:2], dtype=torch.long, device=student_embeds.device
        )
        student = model(
            inputs_embeds=student_embeds,
            attention_mask=attention_mask,
            use_cache=False,
        )
        student_prefix = context_embeds.shape[1] + mapped.shape[1]
        student_logits = continuation_logits(
            student.logits, student_prefix, target_ids.shape[1]
        ).float()
        loss = F.kl_div(
            F.log_softmax(student_logits, dim=-1),
            F.softmax(teacher_logits, dim=-1),
            reduction="batchmean",
        ) / target_ids.shape[1]
        if not torch.isfinite(loss):
            raise RuntimeError("non-finite training loss")
        (loss / config.grad_accumulation).backward()
        accumulated += 1
        running_loss += float(loss.detach())

        if accumulated < config.grad_accumulation:
            continue
        torch.nn.utils.clip_grad_norm_(link.parameters(), 1.0)
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        optimizer_step += 1
        step_loss = running_loss / accumulated
        losses.append(step_loss)
        accumulated = 0
        running_loss = 0.0

        if optimizer_step == 1 or optimizer_step % 5 == 0:
            elapsed = time.time() - started
            print(
                f"step {optimizer_step}/{config.steps} loss={step_loss:.5f} "
                f"examples={examples_seen} elapsed={elapsed/60:.1f}m"
            )

        should_save = (
            optimizer_step % config.checkpoint_every == 0
            or optimizer_step == config.steps
        )
        if should_save:
            payload = {
                "version": 1,
                "config_fingerprint": config.fingerprint(),
                "step": optimizer_step,
                "examples_seen": examples_seen,
                "link": {key: value.detach().cpu() for key, value in link.state_dict().items()},
                "optimizer": optimizer.state_dict(),
                "rng": capture_rng_state(),
                "losses": losses,
            }
            save_checkpoint_atomic(checkpoint_path, payload)
            progress = {
                "step": optimizer_step,
                "steps": config.steps,
                "examples_seen": examples_seen,
                "latest_loss": step_loss,
                "elapsed_seconds": time.time() - started,
            }
            atomic_json(args.output / "progress.json", progress)
            report_to_receiver(client, "training_checkpoint", progress)

    link_path = args.output / "faithful_link.pt"
    save_checkpoint_atomic(
        link_path,
        {
            "version": 1,
            "config": asdict(config),
            "config_fingerprint": config.fingerprint(),
            "model": config.model,
            "source_dim": dimension,
            "target_dim": dimension,
            "link": {key: value.detach().cpu() for key, value in link.state_dict().items()},
            "training_steps": optimizer_step,
            "examples_seen": examples_seen,
            "loss_sha256": hashlib.sha256(json.dumps(losses).encode()).hexdigest(),
        },
    )
    final = {
        "job_id": args.job_id,
        "status": "complete",
        "steps": optimizer_step,
        "examples_seen": examples_seen,
        "initial_loss": losses[0] if losses else math.nan,
        "final_loss": losses[-1] if losses else math.nan,
        "best_loss": min(losses) if losses else math.nan,
        "elapsed_seconds": time.time() - started,
        "link_path": str(link_path),
    }
    atomic_json(args.output / "training_report.json", final)
    report_to_receiver(client, "training_complete", final)
    if client:
        try:
            client.upload(args.output / "training_report.json", "training-report")
        except Exception as error:
            print(f"receiver upload failed; Drive artifact is safe: {type(error).__name__}")
    print(json.dumps(final, indent=2))


if __name__ == "__main__":
    main()

