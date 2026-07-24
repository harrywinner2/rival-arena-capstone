#!/usr/bin/env python3
"""Fine-tune a link for contextual sender states and post-instruction injection.

Only benign Alpaca examples are used. Rival-game prompts, actions, histories,
rewards, and results never enter this training loop.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from l4_arena.jobs import atomic_json
from l4_arena.link import OuterLink
from l4_arena.training import (
    capture_rng_state,
    choose_cuda_dtype,
    extract_alpaca_example,
    restore_rng_state,
    save_checkpoint_atomic,
    seed_everything,
)


CONTEXT_PAIRS = (
    (
        "You are a collaborator helping with a benign task. Review the prior notes and "
        "formulate useful information for another assistant.\nPrior note: clarify the "
        "request, preserve important constraints, and be concise.\nYour information:\n",
        "You are solving a benign assistance task. The collaborator wrote:\n",
        "\nUse that information to answer the request accurately.\nAnswer:",
        "You are solving a benign assistance task. The collaborator sent a private "
        "continuous representation that is appended after these instructions. You "
        "cannot read a text message from them. Use the representation to answer the "
        "request accurately.\nAnswer:",
    ),
    (
        "You are the first assistant in a two-assistant benign workflow. Earlier workflow "
        "notes emphasize correctness, specificity, and respecting the supplied input. "
        "Prepare your contribution now.\nContribution:\n",
        "Act as the second assistant in a benign workflow. Here is the first assistant's "
        "contribution:\n",
        "\nIntegrate the contribution and produce the best final response.\nFinal response:",
        "Act as the second assistant in a benign workflow. The first assistant's "
        "contribution is available only as a private representation appended after this "
        "instruction. Integrate it and produce the best final response.\nFinal response:",
    ),
    (
        "A teammate needs to pass task-relevant information to a downstream model. The "
        "work is harmless and unrelated to games, bargaining, monitoring, or competition. "
        "State the relevant information below.\nMessage:\n",
        "Complete this harmless request using the teammate's note below.\nTeammate note:\n",
        "\nReason from the note, then provide a direct useful answer.\nAnswer:",
        "Complete this harmless request using the teammate's private representation, "
        "which is appended after this instruction. No readable teammate note is "
        "available. Reason from the representation, then provide a direct useful "
        "answer.\nAnswer:",
    ),
    (
        "You are contributing to a cooperative question-answering pipeline. A prior step "
        "checked that the task is benign. Supply the key instruction and input for the "
        "receiver without adding unrelated material.\nPayload:\n",
        "You are the receiver in a cooperative question-answering pipeline.\nReadable "
        "payload from the sender:\n",
        "\nFollow the payload and return the requested result.\nResult:",
        "You are the receiver in a cooperative question-answering pipeline. The sender's "
        "payload is a continuous representation appended after the full instruction. "
        "There is no readable payload. Follow the represented information and return the "
        "requested result.\nResult:",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset", default="yahma/alpaca-cleaned")
    parser.add_argument("--dataset-split", default="train")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--init-link", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--learning-rate", type=float, default=8e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--grad-accumulation", type=int, default=4)
    parser.add_argument("--max-message-tokens", type=int, default=24)
    parser.add_argument("--max-target-tokens", type=int, default=12)
    parser.add_argument("--checkpoint-every", type=int, default=25)
    parser.add_argument("--seed", type=int, default=20260725)
    parser.add_argument("--gradient-checkpointing", action="store_true")
    return parser.parse_args()


def token_ids(tokenizer, text: str, maximum: int, special: bool = False) -> torch.Tensor:
    value = tokenizer(
        text,
        add_special_tokens=special,
        truncation=True,
        max_length=maximum,
        return_tensors="pt",
    ).input_ids
    if value.shape[1] == 0:
        raise ValueError("empty token sequence")
    return value.cuda()


def continuation(logits: torch.Tensor, prefix: int, length: int) -> torch.Tensor:
    return logits[:, prefix - 1 : prefix - 1 + length, :]


def config_dict(args: argparse.Namespace, init_fingerprint: str) -> dict:
    return {
        "model": args.model,
        "dataset": args.dataset,
        "dataset_split": args.dataset_split,
        "steps": args.steps,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "grad_accumulation": args.grad_accumulation,
        "max_message_tokens": args.max_message_tokens,
        "max_target_tokens": args.max_target_tokens,
        "checkpoint_every": args.checkpoint_every,
        "seed": args.seed,
        "context_template_version": 1,
        "init_link_fingerprint": init_fingerprint,
    }


def fingerprint(config: dict) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    seed_everything(args.seed)
    dtype = choose_cuda_dtype()
    token = os.environ.get("HF_TOKEN") or None
    tokenizer = AutoTokenizer.from_pretrained(args.model, token=token)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, token=token, torch_dtype=dtype, low_cpu_mem_usage=True
    ).cuda().eval()
    model.config.use_cache = False
    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False}
        )
    for parameter in model.parameters():
        parameter.requires_grad_(False)

    initial = torch.load(args.init_link, map_location="cpu", weights_only=True)
    if initial["model"] != args.model:
        raise SystemExit("initial link model mismatch")
    dimension = int(model.config.hidden_size)
    link = OuterLink(dimension, dimension, hidden_dim=min(1024, dimension)).cuda().float()
    link.load_state_dict(initial["link"])
    optimizer = torch.optim.AdamW(
        link.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay
    )
    config = config_dict(args, initial["config_fingerprint"])
    config_fingerprint = fingerprint(config)
    checkpoint_path = args.output / "context_checkpoint.pt"
    start_step = 0
    examples_seen = 0
    losses: list[float] = []
    if checkpoint_path.exists():
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if checkpoint["config_fingerprint"] != config_fingerprint:
            raise SystemExit("context checkpoint configuration mismatch")
        link.load_state_dict(checkpoint["link"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        start_step = int(checkpoint["step"])
        examples_seen = int(checkpoint["examples_seen"])
        losses = list(checkpoint.get("losses", []))
        restore_rng_state(checkpoint["rng"])
        print(f"resuming at optimizer step {start_step}")

    manifest = {
        "job_id": args.job_id,
        "objective": "contextual_teacher_text_vs_post_instruction_latent_kl",
        "base_weights_frozen": True,
        "rival_game_training_data": False,
        "context_templates": len(CONTEXT_PAIRS),
        "config": config,
        "config_fingerprint": config_fingerprint,
        "initial_link_fingerprint": initial["config_fingerprint"],
        "gpu": torch.cuda.get_device_name(0),
        "dtype": str(dtype),
        "link_parameters": link.trainable_parameter_count,
    }
    atomic_json(args.output / "manifest.json", manifest)
    dataset = load_dataset(
        args.dataset, split=args.dataset_split, streaming=True, token=token
    ).shuffle(seed=args.seed, buffer_size=2_000)
    iterator = iter(dataset)
    for _ in range(examples_seen):
        next(iterator)

    optimizer.zero_grad(set_to_none=True)
    optimizer_step = start_step
    accumulated = 0
    running = 0.0
    started = time.time()
    while optimizer_step < args.steps:
        row = next(iterator)
        examples_seen += 1
        example = extract_alpaca_example(row)
        if example is None:
            continue
        message, target = example
        sender_prefix, teacher_pre, teacher_post, student_prompt = random.choice(
            CONTEXT_PAIRS
        )
        message_ids = token_ids(tokenizer, message, args.max_message_tokens)
        target_ids = token_ids(tokenizer, target, args.max_target_tokens)
        sender_prefix_ids = token_ids(tokenizer, sender_prefix, 128, special=True)
        sender_ids = torch.cat([sender_prefix_ids, message_ids], dim=1)
        teacher_ids = torch.cat(
            [
                token_ids(tokenizer, teacher_pre, 128, special=True),
                message_ids,
                token_ids(tokenizer, teacher_post, 96),
            ],
            dim=1,
        )
        student_ids = token_ids(tokenizer, student_prompt, 256, special=True)
        with torch.no_grad():
            sender = model(sender_ids, output_hidden_states=True, use_cache=False)
            sender_hidden = sender.hidden_states[-1][
                :, -message_ids.shape[1] :, :
            ].float()
            teacher_full = torch.cat([teacher_ids, target_ids], dim=1)
            teacher_output = model(teacher_full, use_cache=False)
            teacher_logits = continuation(
                teacher_output.logits, teacher_ids.shape[1], target_ids.shape[1]
            ).float()
            student_prompt_embeds = model.get_input_embeddings()(student_ids).detach()
            target_embeds = model.get_input_embeddings()(target_ids).detach()
        mapped = link(sender_hidden).to(dtype)
        student_embeds = torch.cat(
            [student_prompt_embeds, mapped, target_embeds], dim=1
        )
        mask = torch.ones(
            student_embeds.shape[:2], dtype=torch.long, device=student_embeds.device
        )
        student_output = model(
            inputs_embeds=student_embeds, attention_mask=mask, use_cache=False
        )
        student_prefix = student_ids.shape[1] + mapped.shape[1]
        student_logits = continuation(
            student_output.logits, student_prefix, target_ids.shape[1]
        ).float()
        loss = F.kl_div(
            F.log_softmax(student_logits, dim=-1),
            F.softmax(teacher_logits, dim=-1),
            reduction="batchmean",
        ) / target_ids.shape[1]
        if not torch.isfinite(loss):
            raise RuntimeError("non-finite training loss")
        (loss / args.grad_accumulation).backward()
        running += float(loss.detach())
        accumulated += 1
        if accumulated < args.grad_accumulation:
            continue
        torch.nn.utils.clip_grad_norm_(link.parameters(), 1.0)
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        optimizer_step += 1
        step_loss = running / accumulated
        losses.append(step_loss)
        running = 0.0
        accumulated = 0
        if optimizer_step == 1 or optimizer_step % 5 == 0:
            print(
                f"step {optimizer_step}/{args.steps} loss={step_loss:.5f} "
                f"examples={examples_seen} elapsed={(time.time()-started)/60:.1f}m"
            )
        if optimizer_step % args.checkpoint_every == 0 or optimizer_step == args.steps:
            payload = {
                "version": 2,
                "config_fingerprint": config_fingerprint,
                "step": optimizer_step,
                "examples_seen": examples_seen,
                "link": {
                    key: value.detach().cpu() for key, value in link.state_dict().items()
                },
                "optimizer": optimizer.state_dict(),
                "rng": capture_rng_state(),
                "losses": losses,
            }
            save_checkpoint_atomic(checkpoint_path, payload)
            atomic_json(
                args.output / "progress.json",
                {
                    "step": optimizer_step,
                    "steps": args.steps,
                    "examples_seen": examples_seen,
                    "latest_loss": step_loss,
                    "elapsed_seconds": time.time() - started,
                },
            )

    link_payload = {
        "version": 2,
        "config": config,
        "config_fingerprint": config_fingerprint,
        "model": args.model,
        "source_dim": dimension,
        "target_dim": dimension,
        "examples_seen": examples_seen,
        "link": {key: value.detach().cpu() for key, value in link.state_dict().items()},
    }
    save_checkpoint_atomic(args.output / "faithful_link.pt", link_payload)
    report = {
        "job_id": args.job_id,
        "steps": optimizer_step,
        "examples_seen": examples_seen,
        "initial_loss": losses[0],
        "best_loss": min(losses),
        "final_loss": losses[-1],
        "elapsed_seconds": time.time() - started,
        "config_fingerprint": config_fingerprint,
    }
    atomic_json(args.output / "training_report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
