from pathlib import Path

import pytest

from compute_economics.schemas import RunInput


@pytest.fixture
def run():
    return RunInput.model_validate_json(Path("scenarios/stable_demand.json").read_text())


def changed(run, **updates):
    return RunInput.model_validate(dict(run.model_dump(), **updates))
