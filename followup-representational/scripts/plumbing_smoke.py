#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from l4_arena.jobs import ResultClient, atomic_json
from l4_arena.link import OuterLink


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit("CUDA GPU required for the Colab plumbing smoke")
    args.output.mkdir(parents=True, exist_ok=True)
    gpu = torch.cuda.get_device_properties(0)
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    tokenizer = AutoTokenizer.from_pretrained(args.model, token=os.environ.get("HF_TOKEN") or None)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=dtype,
        token=os.environ.get("HF_TOKEN") or None,
    ).eval().cuda()
    for parameter in model.parameters():
        parameter.requires_grad_(False)

    sender_text = "I intend to choose the mutually beneficial option this round."
    receiver_text = "A collaborator sent a private representation. Decide your next action:"
    sender = tokenizer(sender_text, return_tensors="pt").to("cuda")
    receiver = tokenizer(receiver_text, return_tensors="pt").to("cuda")
    with torch.inference_mode():
        sender_output = model(**sender, output_hidden_states=True, use_cache=False)
    hidden = sender_output.hidden_states[-1][:, -8:, :].to(torch.float32)
    dimension = hidden.shape[-1]
    link = OuterLink(dimension, dimension, hidden_dim=min(512, dimension)).cuda().to(torch.float32)
    mapped = link(hidden).to(dtype)
    prompt_embeds = model.get_input_embeddings()(receiver.input_ids)
    inputs_embeds = torch.cat([prompt_embeds, mapped], dim=1)
    mask = torch.ones(inputs_embeds.shape[:2], dtype=torch.long, device="cuda")
    with torch.inference_mode():
        output = model.generate(
            inputs_embeds=inputs_embeds,
            attention_mask=mask,
            max_new_tokens=12,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    decoded = tokenizer.decode(output[0], skip_special_tokens=True)
    report = {
        "job_id": args.job_id,
        "model": args.model,
        "gpu": gpu.name,
        "gpu_memory_bytes": gpu.total_memory,
        "dtype": str(dtype),
        "hidden_shape": list(hidden.shape),
        "mapped_shape": list(mapped.shape),
        "finite": bool(torch.isfinite(mapped).all()),
        "generated": decoded,
        "torch": torch.__version__,
    }
    if not report["finite"] or not decoded.strip():
        raise SystemExit("plumbing gate failed")
    atomic_json(args.output / "smoke_report.json", report)
    url = os.environ.get("L4_RECEIVER_URL")
    token = os.environ.get("L4_RECEIVER_TOKEN")
    if url and token:
        client = ResultClient(url, token, args.job_id)
        client.status("plumbing_smoke_complete", report)
        client.upload(args.output / "smoke_report.json", "gate-report")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
