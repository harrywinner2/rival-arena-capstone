# L4 representational-channel follow-up

This directory implements the follow-up described in `PLAN.md` as a resumable
Colab job fleet. Base language-model weights remain frozen. Only an `OuterLink`
adapter and explicit diagnostic probes are trained.

## Notebook fleet

Run these in order:

1. `notebooks/00_plumbing_smoke.ipynb`
2. `notebooks/10_train_faithful.ipynb`
3. `notebooks/20_validate_and_probe.ipynb`
4. `notebooks/30_run_arena.ipynb`

Each notebook:

- audits the assigned GPU and refuses an unsafe configuration;
- clones a pinned repository revision;
- uses a unique `L4_JOB_ID`;
- checkpoints to Google Drive;
- resumes after runtime loss;
- uploads compact status/result bundles to the authenticated Oracle receiver;
- never prints Hugging Face or receiver credentials.

Colab Pro improves availability but does not guarantee GPU type, maximum runtime,
or concurrent-runtime count. Do not start duplicate jobs with the same job ID.

## Colab secrets

Add these using the key icon in Colab's left sidebar:

- `HF_TOKEN`: Hugging Face read token for gated models, if needed.
- `L4_RECEIVER_URL`: HTTPS base URL of the Oracle result receiver.
- `L4_RECEIVER_TOKEN`: bearer token generated during receiver deployment.

The notebooks also mount Drive. Checkpoints live below
`MyDrive/rival-arena-l4/<job-id>/`.

## Jobs and parallelism

Parallelize independent work only:

- after smoke passes, faithful training for different model families may run in
  parallel using distinct job IDs;
- bottleneck dimensions may run in parallel after the full link passes validation;
- arena cells may run in parallel after the pre-registration and link hash are
  frozen.

Never parallelize dependent stages (training → validation → confirmatory arena).

## Result receiver

`receiver/server.py` accepts authenticated status JSON and artifact archives. It
writes atomically beneath a configured data directory and rejects traversal,
oversized uploads, duplicate finalization, and invalid bearer tokens.

The VM deployment uses a dedicated unprivileged service and HTTPS reverse proxy.
The receiver stores no model-provider or Hugging Face credentials.
