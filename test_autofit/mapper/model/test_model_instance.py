import pytest

import autofit as af
from autofit.mock.mock_model import MockClassx2, MockClassx3TupleFloat, MockComponents

@pytest.fixture(name="mock_components_1")
def make_mock_components_1():
    return MockComponents()


@pytest.fixture(name="mock_components_2")
def make_mock_components_2():
    return MockComponents()


@pytest.fixture(name="instance")
def make_instance(mock_components_1, mock_components_2):
    sub = af.ModelInstance()

    instance = af.ModelInstance()
    sub.mock_components_1 = mock_components_1

    instance.mock_components_2 = mock_components_2
    instance.sub = sub

    sub_2 = af.ModelInstance()
    sub_2.mock_components_1 = mock_components_1

    instance.sub.sub = sub_2

    return instance


class TestModelInstance:
    def test_iterable(self, instance):
        assert len(list(instance)) == 2

    def test_as_model(self, instance):
        model = instance.as_model()
        assert isinstance(model, af.ModelMapper)
        assert isinstance(model.mock_components_2, af.PriorModel)
        assert model.mock_components_2.cls == MockComponents

    def test_object_for_path(self, instance, mock_components_1, mock_components_2):
        assert instance.object_for_path(("mock_components_2",)) is mock_components_2
        assert instance.object_for_path(("sub", "mock_components_1")) is mock_components_1
        assert instance.object_for_path(("sub", "sub", "mock_components_1")) is mock_components_1
        setattr(instance.object_for_path(("mock_components_2",)), "mock_components", mock_components_1)
        assert mock_components_2.mock_components is mock_components_1

    def test_path_instance_tuples_for_class(self, instance, mock_components_1, mock_components_2):
        result = instance.path_instance_tuples_for_class(MockComponents)
        assert result[0] == (("mock_components_2",), mock_components_2)
        assert result[1] == (("sub", "mock_components_1"), mock_components_1)
        assert result[2] == (("sub", "sub", "mock_components_1"), mock_components_1)

    def test_simple_model(self):
        mapper = af.ModelMapper()

        mapper.mock_class = MockClassx2

        model_map = mapper.instance_from_unit_vector([1.0, 1.0])

        assert isinstance(model_map.mock_class, MockClassx2)
        assert model_map.mock_class.one == 1.0
        assert model_map.mock_class.two == 2.0

    def test_two_object_model(self):
        mapper = af.ModelMapper()

        mapper.mock_class_1 = MockClassx2
        mapper.mock_class_2 = MockClassx2

        model_map = mapper.instance_from_unit_vector([1.0, 0.0, 0.0, 1.0])

        assert isinstance(model_map.mock_class_1, MockClassx2)
        assert isinstance(model_map.mock_class_2, MockClassx2)

        assert model_map.mock_class_1.one == 1.0
        assert model_map.mock_class_1.two == 0.0

        assert model_map.mock_class_2.one == 0.0
        assert model_map.mock_class_2.two == 2.0

    def test_swapped_prior_construction(self):
        mapper = af.ModelMapper()

        mapper.mock_class_1 = MockClassx2
        mapper.mock_class_2 = MockClassx2

        # noinspection PyUnresolvedReferences
        mapper.mock_class_2.one = mapper.mock_class_1.one

        model_map = mapper.instance_from_unit_vector([1.0, 0.0, 0.0])

        assert isinstance(model_map.mock_class_1, MockClassx2)
        assert isinstance(model_map.mock_class_2, MockClassx2)

        assert model_map.mock_class_1.one == 1.0
        assert model_map.mock_class_1.two == 0.0

        assert model_map.mock_class_2.one == 1.0
        assert model_map.mock_class_2.two == 0.0

    def test_prior_replacement(self):
        mapper = af.ModelMapper()

        mapper.mock_class = MockClassx2

        mapper.mock_class.one = af.UniformPrior(100, 200)

        model_map = mapper.instance_from_unit_vector([0.0, 0.0])

        assert model_map.mock_class.one == 100.0

    def test_tuple_arg(self):
        mapper = af.ModelMapper()

        mapper.mock_profile = MockClassx3TupleFloat

        model_map = mapper.instance_from_unit_vector([1.0, 0.0, 0.0])

        assert model_map.mock_profile.one_tuple == (1.0, 0.0)
        assert model_map.mock_profile.two == 0.0

    def test_modify_tuple(self):
        mapper = af.ModelMapper()

        mapper.mock_profile = MockClassx3TupleFloat

        # noinspection PyUnresolvedReferences
        mapper.mock_profile.one_tuple.one_tuple_0 = af.UniformPrior(1.0, 10.0)

        model_map = mapper.instance_from_unit_vector([1.0, 1.0, 1.0])

        assert model_map.mock_profile.one_tuple == (10.0, 2.0)

    def test_match_tuple(self):
        mapper = af.ModelMapper()

        mapper.mock_profile = MockClassx3TupleFloat

        # noinspection PyUnresolvedReferences
        mapper.mock_profile.one_tuple.one_tuple_1 = (
            mapper.mock_profile.one_tuple.one_tuple_0
        )

        model_map = mapper.instance_from_unit_vector([1.0, 0.0])

        assert model_map.mock_profile.one_tuple == (1.0, 1.0)
        assert model_map.mock_profile.two == 0.0
