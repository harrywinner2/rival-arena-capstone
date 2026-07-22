import numpy as np
import torch

from l4_arena.validation import continuation, fit_probe, intent_messages, kl_and_agreement


def test_continuation_slice_and_metrics():
    logits = torch.randn(1, 10, 7)
    selected = continuation(logits, prefix=4, target=3)
    assert selected.shape == (1, 3, 7)
    kl, agreement = kl_and_agreement(selected, selected)
    assert abs(kl) < 1e-6
    assert agreement == 1.0


def test_intent_messages_are_balanced_and_probe_runs():
    messages, labels = intent_messages(80, 4)
    assert len(messages) == 80
    assert labels.sum() == 40
    rng = np.random.default_rng(3)
    features = np.column_stack([labels, rng.normal(size=(80, 4))])
    result = fit_probe(features, labels, 2)
    assert result["balanced_accuracy"] > 0.9
