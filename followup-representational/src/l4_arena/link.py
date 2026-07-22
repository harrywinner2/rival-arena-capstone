from __future__ import annotations

import torch
from torch import nn


class OuterLink(nn.Module):
    """Residual map from sender hidden states to receiver token embeddings."""

    def __init__(
        self,
        source_dim: int,
        target_dim: int,
        hidden_dim: int | None = None,
        bottleneck_dim: int | None = None,
    ) -> None:
        super().__init__()
        if source_dim <= 0 or target_dim <= 0:
            raise ValueError("source_dim and target_dim must be positive")
        hidden_dim = hidden_dim or min(max(source_dim, target_dim), 4096)
        inner_dim = bottleneck_dim or hidden_dim
        if inner_dim <= 0:
            raise ValueError("bottleneck_dim must be positive")

        self.source_dim = source_dim
        self.target_dim = target_dim
        self.bottleneck_dim = bottleneck_dim
        self.residual = nn.Linear(source_dim, target_dim, bias=False)
        self.up = nn.Linear(source_dim, inner_dim, bias=False)
        self.down = nn.Linear(inner_dim, target_dim, bias=False)
        self.norm = nn.LayerNorm(target_dim)
        self.gate = nn.Parameter(torch.tensor(-2.0))

        nn.init.zeros_(self.down.weight)
        if source_dim == target_dim:
            nn.init.eye_(self.residual.weight)
        else:
            nn.init.orthogonal_(self.residual.weight)

    def forward(self, hidden: torch.Tensor) -> torch.Tensor:
        if hidden.ndim != 3 or hidden.shape[-1] != self.source_dim:
            raise ValueError(
                f"expected [batch, sequence, {self.source_dim}], got {tuple(hidden.shape)}"
            )
        residual = self.residual(hidden)
        update = self.down(torch.nn.functional.gelu(self.up(hidden)))
        return self.norm(residual + torch.sigmoid(self.gate) * update)

    @property
    def trainable_parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters() if parameter.requires_grad)
