import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from compute_economics.schemas import Policy, Workload
from compute_economics.units import ceil_tolerant, cents_to_usd, node_to_gpu_rate, watts_to_kw


def test_dimensions():
    assert node_to_gpu_rate(68.8, 8) == 8.6
    assert watts_to_kw(1000) == 1
    assert cents_to_usd(10) == 0.1
    assert ceil_tolerant(5 + 1e-12) == 5
    assert ceil_tolerant(5.1) == 6


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, 0, "1000"])
def test_strict_performance(value):
    with pytest.raises(ValidationError):
        Workload(
            workload_id="x",
            model="gpt-oss-120b",
            revision="x",
            quality="x",
            dataset="x",
            precision="fp4",
            runtime="x",
            topology="x",
            benchmark_id="x",
            performance_tokens_s=value,
            transfer_differences="assumed",
        )


@pytest.mark.parametrize("nodes", [1.5, "2", True, -1, 129])
def test_whole_nodes(nodes):
    with pytest.raises(ValidationError):
        Policy(family="own", nodes=nodes)


def test_engine_has_no_ui_imports():
    for path in Path("src/compute_economics").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(not a.name.startswith("streamlit") for a in node.names)
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("streamlit")
