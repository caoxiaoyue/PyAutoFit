import os

from autofit.mapper.prior_model.collection import CollectionPriorModel

path = os.path.dirname(os.path.realpath(__file__))


class ModelMapper(CollectionPriorModel):
    """
    A mapper of priors formed by passing in classes to be reconstructed

    @DynamicAttrs

    The ModelMapper converts a set of classes whose input attributes may be
    modeled using a non-linear search, to parameters with priors attached.

    A config is passed into the model mapper to provide default setup values for
    the priors:

    mapper = ModelMapper(config)

    All class instances that are to be generated by the model mapper are
    specified by adding classes to it:

    mapper = ModelMapper()

    mapper.sersic = al.lp.AbstractEllSersic
    mapper.gaussian = al.lp.EllGaussian
    mapper.any_class = SomeClass

    A `PriorModel` instance is created each time we add a class to the mapper. We
    can access those models using # the mapper attributes:

    sersic_model = mapper.sersic

    This allows us to replace the default priors:

    mapper.sersic.normalization = GaussianPrior(mean=2., sigma=5.)

    Or maybe we want to tie two priors together:

    mapper.sersic.two = mapper.other_sersic.two

    This statement reduces the number of priors by one and means that the two
    sersic instances will always share # the same rotation two two.

    We can then create instances of every class for a unit hypercube vector
    with length equal to # len(mapper.priors):

    model_instance = mapper.model_instance_for_vector([.4, .2, .3, .1])

    The attributes of the model_instance are named the same as those of the mapper:

    sersic_1 = mapper.sersic_1

    But this attribute is an instance of the actual AbstractEllSersic:P
    class

    A ModelMapper can be concisely constructed using keyword arguments:

    mapper = prior.ModelMapper(
        source_light_profile=light_profile.AbstractEllSersic,
        lens_mass_profile=mass_profile.EllIsothermalCored,
        lens_light_profile=light_profile.EllSersicCore
    )
    """

    @property
    def prior_prior_model_dict(self):
        """

        Returns
        -------
        prior_prior_model_dict: {Prior: PriorModel}
            A dictionary mapping priors to associated prior models. Each prior will only
            have one prior model; if a prior is shared by two prior models then one of
            those prior models will be in this dictionary.
        """
        return {
            prior: prior_model[1]
            for prior_model in self.prior_model_tuples
            for _, prior in prior_model[1].prior_tuples
        }
