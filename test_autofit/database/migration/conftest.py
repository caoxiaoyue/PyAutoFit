import pytest

from autofit.database.migration import Step, Migrator


@pytest.fixture(
    name="step_1"
)
def make_step_1():
    return Step(
        "INSERT INTO test (id) VALUES (1)"
    )


@pytest.fixture(
    name="step_2"
)
def make_step_2():
    return Step(
        "INSERT INTO test (id) VALUES (2)"
    )


@pytest.fixture(
    name="migrator"
)
def make_migrator(
        step_1,
        step_2
):
    return Migrator(
        step_1,
        step_2
    )
