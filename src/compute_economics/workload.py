"""Immutable common demand generated independently of candidate hardware."""

import calendar
from dataclasses import dataclass

import numpy as np

from compute_economics.schemas import RunInput


@dataclass(frozen=True)
class DemandTable:
    period: np.ndarray
    block: np.ndarray
    hours: np.ndarray
    tokens: np.ndarray
    month_hours: np.ndarray
    month_labels: tuple[str, ...]

    def __post_init__(self):
        for name in ("period", "block", "hours", "tokens", "month_hours"):
            value = np.array(getattr(self, name), copy=True)
            value.setflags(write=False)
            object.__setattr__(self, name, value)
        if len(self.tokens) == 0 or not (
            len(self.period) == len(self.block) == len(self.hours) == len(self.tokens)
        ):
            raise ValueError("empty or inconsistent demand arrays")
        if (
            not np.isfinite(self.tokens).all()
            or (self.tokens < 0).any()
            or not np.isfinite(self.hours).all()
            or (self.hours <= 0).any()
        ):
            raise ValueError("invalid demand/duration")
        keys = list(zip(self.period, self.block))
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate demand block")
        if set(self.period) != set(range(1, len(self.month_hours) + 1)):
            raise ValueError("missing calendar period")
        for p, h in enumerate(self.month_hours, 1):
            if not np.isclose(self.hours[self.period == p].sum(), h, rtol=1e-12):
                raise ValueError("calendar hours not conserved")

    def scaled(self, multiplier: float):
        if not np.isfinite(multiplier) or multiplier < 0:
            raise ValueError("invalid demand multiplier")
        return DemandTable(
            self.period,
            self.block,
            self.hours,
            self.tokens * multiplier,
            self.month_hours,
            self.month_labels,
        )


def build_demand(run: RunInput) -> DemandTable:
    labels = []
    month_hours = []
    for index in range(run.horizon_months):
        absolute = run.start_date.year * 12 + run.start_date.month - 1 + index
        year, month = divmod(absolute, 12)
        month += 1
        labels.append(f"{year:04d}-{month:02d}")
        month_hours.append(calendar.monthrange(year, month)[1] * 24.0)
    mh = np.array(month_hours)
    blocks = len(run.block_fractions)
    period = np.repeat(np.arange(1, run.horizon_months + 1), blocks)
    block = np.tile(np.arange(blocks), run.horizon_months)
    hours = (mh[:, None] * np.array(run.block_fractions)).ravel()
    if run.custom_demand_tokens is not None:
        tokens = np.array(run.custom_demand_tokens).ravel()
    else:
        tokens = (
            3600
            * run.demand_scale_tokens_s
            * np.tile(run.demand_base_nodes, run.horizon_months)
            * hours
            * (1 + run.demand_growth_fraction) ** (period - 1)
        )
    tokens = tokens * run.demand_multiplier
    if run.demand_disappointment:
        tokens = tokens * np.where(period >= 7, 0.5, 1.0)
    return DemandTable(period, block, hours, tokens, mh, tuple(labels))
