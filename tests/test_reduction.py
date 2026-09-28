import importlib.util
from pathlib import Path

import pytest

from compute_economics.economics import deterministic_dot


@pytest.mark.parametrize(
    "left,right,expected",
    [
        ([1e16, 1.0, -1e16], [1.0, 1.0, 1.0], 1.0),
        ([1.0 + 2**-27, -1.0], [1.0 - 2**-27, 1.0], 0.0),
        ([], [], 0.0),
    ],
)
def test_ordered_float64_dot(left, right, expected):
    # Cancellation and rounded products distinguish this from naive sum or fused multiply-add.
    assert deterministic_dot(left, right) == expected


def test_mismatch_retains_exact_bytes_and_diagnostics(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts/verify_reproduction.py"
    spec = importlib.util.spec_from_file_location("reproduction", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    left, right = tmp_path / "left", tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "annual_costs.csv").write_bytes(b"value\r\n1.0\r\n")
    (right / "annual_costs.csv").write_bytes(b"value\n1.0\n")
    with pytest.raises(AssertionError, match="exact-byte mismatch"):
        module.compare(left, right)
    target = next((tmp_path / "artifacts/reproduction-failures").iterdir())
    assert (target / "expected/annual_costs.csv").read_bytes() == b"value\r\n1.0\r\n"
    assert (target / "generated/annual_costs.csv").read_bytes() == b"value\n1.0\n"
    assert '"parsed_cells_equal": true' in (target / "comparison.json").read_text()
