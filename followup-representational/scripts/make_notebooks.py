#!/usr/bin/env python3
"""Generate small reviewed Colab controllers; implementation stays in Python modules."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks"


def markdown(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(True),
    }


def notebook(title: str, purpose: str, command: str, defaults: dict[str, str]) -> dict:
    default_lines = "\n".join(f'{key} = {value!r}' for key, value in defaults.items())
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"name": title, "provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
        },
        "cells": [
            markdown(f"# {title}\n\n{purpose}\n\nRun cells from top to bottom. Re-running resumes from Drive."),
            code(
                "from google.colab import drive, userdata\n"
                "drive.mount('/content/drive')\n"
                "import os, pathlib, subprocess, torch\n"
                "assert torch.cuda.is_available(), 'Select a GPU runtime first'\n"
                "print(subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total', "
                "'--format=csv,noheader'], text=True))\n"
                "for name in ('HF_TOKEN', 'L4_RECEIVER_URL', 'L4_RECEIVER_TOKEN'):\n"
                "    try:\n"
                "        value = userdata.get(name)\n"
                "        if value: os.environ[name] = value\n"
                "    except Exception:\n"
                "        print(f'{name}: not configured (optional for smoke)')\n"
            ),
            code(
                "REPO = 'https://github.com/harrywinner2/rival-arena-capstone.git'\n"
                "REVISION = '4d0467233b644df641f1c5604a7b142d873d7206'\n"
                "WORK = pathlib.Path('/content/rival-arena-capstone')\n"
                "if not WORK.exists(): subprocess.run(['git', 'clone', REPO, str(WORK)], check=True)\n"
                "subprocess.run(['git', '-C', str(WORK), 'fetch', '--all'], check=True)\n"
                "subprocess.run(['git', '-C', str(WORK), 'checkout', REVISION], check=True)\n"
                "subprocess.run(['pip', 'install', '-q', '-r', str(WORK/'followup-representational/requirements.txt')], check=True)\n"
            ),
            code(default_lines + "\nprint('Job:', JOB_ID)\n"),
            code(
                "JOB_DIR = pathlib.Path('/content/drive/MyDrive/rival-arena-l4') / JOB_ID\n"
                "JOB_DIR.mkdir(parents=True, exist_ok=True)\n"
                f"command = {command}\n"
                "print(' '.join(map(str, command)))\n"
                "subprocess.run(list(map(str, command)), cwd=WORK/'followup-representational', check=True, env=os.environ)\n"
            ),
            markdown("## Completion\n\nThe final cell exits only after the stage checkpoint is on Drive and its compact report has reached the VM receiver."),
        ],
    }


SPECS = {
    "00_plumbing_smoke.ipynb": notebook(
        "L4 00 — activation plumbing smoke",
        "Proves hidden-state extraction, OuterLink mapping, embedding injection, generation, Drive persistence, and VM reporting on a small model.",
        "['python', 'scripts/plumbing_smoke.py', '--model', MODEL, '--output', JOB_DIR, '--job-id', JOB_ID]",
        {"JOB_ID": "smoke-qwen05b-001", "MODEL": "Qwen/Qwen2.5-0.5B-Instruct"},
    ),
    "05_capability_gate_3b.ipynb": notebook(
        "L4 05 — Qwen 3B text-channel capability gate",
        "Runs only no-channel versus readable-text conditions. Train a 3B latent link only if this stronger base model demonstrates that it can behaviorally use text communication.",
        "['python', 'scripts/run_arena.py', '--model', MODEL, '--job-dir', JOB_DIR, '--job-id', JOB_ID, '--profile', 'baseline']",
        {"JOB_ID": "capability-qwen3b-t4-001", "MODEL": "Qwen/Qwen2.5-3B-Instruct"},
    ),
    "10_train_faithful.ipynb": notebook(
        "L4 10 — train faithful link",
        "Trains only the representational adapter on neutral transmission, with frozen base weights and resumable checkpoints.",
        "['python', 'scripts/train_link.py', '--model', MODEL, '--output', JOB_DIR, '--job-id', JOB_ID, '--steps', str(STEPS)]",
        {"JOB_ID": "faithful-qwen05b-t4-001", "MODEL": "Qwen/Qwen2.5-0.5B-Instruct", "STEPS": "300"},
    ),
    "11_train_scaled_1p5b.ipynb": notebook(
        "L4 11 — train faithful link (Qwen 1.5B)",
        "Capability-scale run for T4: trains a larger faithful link for a stronger frozen base model, with Drive resume and the same neutral-only objective.",
        "['python', 'scripts/train_link.py', '--model', MODEL, '--output', JOB_DIR, '--job-id', JOB_ID, '--steps', str(STEPS), '--checkpoint-every', '25']",
        {"JOB_ID": "faithful-qwen15b-t4-001", "MODEL": "Qwen/Qwen2.5-1.5B-Instruct", "STEPS": "600"},
    ),
    "20_validate_and_probe.ipynb": notebook(
        "L4 20 — validate channel and train probe",
        "Runs held-out fidelity/coherence controls and trains the diagnostic intent probe. This is the spend gate before arena execution.",
        "['python', 'scripts/validate_link.py', '--model', MODEL, '--job-dir', JOB_DIR, '--job-id', JOB_ID, '--examples', str(EXAMPLES), '--probe-examples', str(PROBE_EXAMPLES), '--generation-samples', str(GENERATION_SAMPLES)]",
        {"JOB_ID": "faithful-qwen05b-t4-001", "MODEL": "Qwen/Qwen2.5-0.5B-Instruct", "EXAMPLES": "512", "PROBE_EXAMPLES": "480", "GENERATION_SAMPLES": "20"},
    ),
    "21_validate_scaled_1p5b.ipynb": notebook(
        "L4 21 — validate Qwen 1.5B channel",
        "Runs the full held-out fidelity/control suite and intent probe for the scaled link.",
        "['python', 'scripts/validate_link.py', '--model', MODEL, '--job-dir', JOB_DIR, '--job-id', JOB_ID, '--examples', str(EXAMPLES), '--probe-examples', str(PROBE_EXAMPLES), '--generation-samples', str(GENERATION_SAMPLES)]",
        {"JOB_ID": "faithful-qwen15b-t4-001", "MODEL": "Qwen/Qwen2.5-1.5B-Instruct", "EXAMPLES": "512", "PROBE_EXAMPLES": "480", "GENERATION_SAMPLES": "20"},
    ),
    "30_run_arena.ipynb": notebook(
        "L4 30 — run arena cells",
        "Runs checkpointed PD/Bertrand pilot or frozen confirmatory cells using a validated link hash.",
        "['python', 'scripts/run_arena.py', '--model', MODEL, '--job-dir', JOB_DIR, '--job-id', JOB_ID, '--profile', PROFILE]",
        {"JOB_ID": "faithful-qwen05b-t4-001", "MODEL": "Qwen/Qwen2.5-0.5B-Instruct", "PROFILE": "pilot"},
    ),
    "31_run_arena_scaled_1p5b.ipynb": notebook(
        "L4 31 — run Qwen 1.5B arena pilot",
        "Runs the corrected legal-choice-scored PD/Bertrand pilot using the validated 1.5B link.",
        "['python', 'scripts/run_arena.py', '--model', MODEL, '--job-dir', JOB_DIR, '--job-id', JOB_ID, '--profile', PROFILE]",
        {"JOB_ID": "faithful-qwen15b-t4-001", "MODEL": "Qwen/Qwen2.5-1.5B-Instruct", "PROFILE": "pilot"},
    ),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in SPECS.items():
        (OUT / name).write_text(json.dumps(value, indent=1) + "\n")


if __name__ == "__main__":
    main()
