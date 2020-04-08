import pytest

import autofit as af


@pytest.fixture(
    name="phase"
)
def make_phase():
    return af.AbstractPhase(
        phase_name="phase_name",
        phase_tag="phase_tag"
    )


def test_metadata_dictionary(phase):
    phase.pipeline_name = "pipeline_name"
    phase.pipeline_tag = "pipeline_tag"
    assert phase._default_metadata == {
        "phase": "phase_name",
        "phase_tag": "phase_tag",
        "pipeline": "pipeline_name",
        "pipeline_tag": "pipeline_tag",
    }



def test_datset_name_in_metadata_text(phase):
    text = phase.make_metadata_text(
        dataset_name="data"
    )
    assert text == """phase=phase_name
phase_tag=phase_tag
pipeline=
pipeline_tag=
dataset_name=data"""
