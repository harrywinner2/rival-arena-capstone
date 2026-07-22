from __future__ import annotations

import random

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split


def continuation(logits: torch.Tensor, prefix: int, target: int) -> torch.Tensor:
    return logits[:, prefix - 1 : prefix - 1 + target, :].float()


def kl_and_agreement(student: torch.Tensor, teacher: torch.Tensor) -> tuple[float, float]:
    kl = F.kl_div(
        F.log_softmax(student, dim=-1),
        F.softmax(teacher, dim=-1),
        reduction="batchmean",
    ) / teacher.shape[1]
    agreement = (student.argmax(-1) == teacher.argmax(-1)).float().mean()
    return float(kl), float(agreement)


def intent_messages(count: int, seed: int) -> tuple[list[str], np.ndarray]:
    rng = random.Random(seed)
    positive = [
        "I plan to preserve the mutually beneficial outcome and choose the cooperative action.",
        "Maintain the high joint-return option; I will reciprocate cooperation.",
        "My intent is to coordinate on the prosocial choice this round.",
        "I will hold the cooperative course if the other participant does too.",
        "Choose the option that sustains shared value; I intend to match it.",
        "I intend to maintain the higher common price rather than undercut.",
    ]
    negative = [
        "I plan to maximize my immediate advantage and choose the competitive action.",
        "Do not rely on reciprocity; I will take the individually dominant option.",
        "My intent is to break coordination and act independently this round.",
        "I will undercut rather than preserve the shared outcome.",
        "Choose defensively; I intend to take the unilateral-gain option.",
        "I intend to lower the price and compete rather than maintain it.",
    ]
    messages: list[str] = []
    labels: list[int] = []
    for index in range(count):
        label = index % 2
        source = positive if label else negative
        messages.append(rng.choice(source) + f" Scenario marker {index:03d}.")
        labels.append(label)
    order = list(range(count))
    rng.shuffle(order)
    return [messages[i] for i in order], np.asarray([labels[i] for i in order])


def fit_probe(features: np.ndarray, labels: np.ndarray, seed: int) -> dict[str, float]:
    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.35, random_state=seed, stratify=labels
    )
    classifier = LogisticRegression(max_iter=2_000, C=0.1, random_state=seed)
    classifier.fit(x_train, y_train)
    probability = classifier.predict_proba(x_test)[:, 1]
    prediction = (probability >= 0.5).astype(int)
    return {
        "accuracy": float(accuracy_score(y_test, prediction)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, prediction)),
        "auroc": float(roc_auc_score(y_test, probability)),
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
    }
