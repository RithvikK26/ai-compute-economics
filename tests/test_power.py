"""Exact regressions for power inputs that differ under NumPy's X86_V4 dispatch."""

import numpy as np
import pytest

from compute_economics.economics import discount_factors
from compute_economics.numerics import scalar_power
from compute_economics.workload import build_demand


@pytest.mark.parametrize(
    "rate,period,expected_hex",
    [
        (0.10, 12, "0x1.d1745d1745d17p-1"),
        (0.10, 19, "0x1.b84859d385424p-1"),
        (0.05, 6, "0x1.f3a92ca2f4b7cp-1"),
        (0.05, 13, "0x1.e5a3f7082346ap-1"),
        (0.05, 29, "0x1.c70db42de5774p-1"),
        (0.15, 22, "0x1.8c44fa5e58073p-1"),
    ],
)
def test_discount_power_matches_existing_binary64_baseline(rate, period, expected_hex):
    values = discount_factors(rate, 36)
    assert values.dtype == np.float64
    assert float(values[period]).hex() == expected_hex
    assert values[0] == 1.0


def test_growth_power_and_block_demand_match_existing_baseline(run):
    assert scalar_power(1 + 0.005, 26).hex() == "0x1.237215d3ca37fp+0"
    demand = build_demand(run)
    assert float(demand.tokens[52]).hex() == "0x1.46a8a53febae4p+39"
    assert float(demand.tokens[53]).hex() == "0x1.46a8a53febae4p+38"


def test_power_converts_operands_before_evaluation():
    class NonPythonPower(float):
        def __pow__(self, other):
            raise AssertionError("Operand-specific power must not execute")

        def __rpow__(self, other):
            raise AssertionError("Operand-specific power must not execute")

    result = scalar_power(NonPythonPower(1 + 0.005), NonPythonPower(26))
    assert type(result) is float
    assert result.hex() == "0x1.237215d3ca37fp+0"
    assert scalar_power(np.float64(1 + 0.005), np.int64(26)) == result
    assert scalar_power(2, 3) == 8.0


def test_zero_discount_and_custom_demand_preserve_values(run):
    assert np.array_equal(discount_factors(0.0, 36), np.ones(37))
    custom = [[float(i + 1), float(i + 2)] for i in range(run.horizon_months)]
    candidate = type(run).model_validate(dict(run.model_dump(), custom_demand_tokens=custom))
    assert np.array_equal(build_demand(candidate).tokens, np.array(custom).ravel())
