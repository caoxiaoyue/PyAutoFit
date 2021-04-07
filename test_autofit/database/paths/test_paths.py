import pytest

import autofit as af
from autofit import database as m
from autofit.mock.mock import Gaussian


@pytest.fixture(
    name="paths"
)
def make_paths(session):
    paths = af.DatabasePaths(
        session
    )
    assert paths.is_complete is False
    return paths


@pytest.fixture(
    name="fit"
)
def query_fit(session, paths):
    fit, = m.Fit.all(session)
    return fit


def test_identifier(
        paths,
        fit
):
    assert fit.id == paths.identifier


def test_completion(
        paths,
        fit
):
    paths.completed()

    assert fit.is_complete
    assert paths.is_complete


def test_object(paths):
    gaussian = Gaussian(
        intensity=2.1
    )

    assert paths.is_object(
        "gaussian"
    ) is False

    paths.save_object(
        "gaussian",
        gaussian
    )

    assert paths.is_object(
        "gaussian"
    ) is True
    assert paths.load_object(
        "gaussian"
    ) == gaussian

    paths.remove_object(
        "gaussian"
    )
    assert paths.is_object(
        "gaussian"
    ) is False
