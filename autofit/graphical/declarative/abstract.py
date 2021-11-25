from abc import ABC, abstractmethod
from typing import Set, List, Dict

from autofit.graphical.declarative.factor.prior import PriorFactor
from autofit.graphical.declarative.graph import DeclarativeFactorGraph
from autofit.graphical.expectation_propagation import AbstractFactorOptimiser
from autofit.graphical.expectation_propagation import EPMeanField
from autofit.graphical.expectation_propagation import EPOptimiser
from autofit.mapper.identifier import Identifier
from autofit.mapper.model import ModelInstance
from autofit.mapper.prior.abstract import Prior
from autofit.mapper.prior_model.collection import CollectionPriorModel
from autofit.messages.normal import NormalMessage
from autofit.non_linear.analysis import Analysis
from autofit.non_linear.paths.abstract import AbstractPaths


class AbstractDeclarativeFactor(Analysis, ABC):
    optimiser: AbstractFactorOptimiser

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    def model_factors(self) -> List["AbstractDeclarativeFactor"]:
        return [self]

    @property
    @abstractmethod
    def prior_model(self):
        pass

    @property
    @abstractmethod
    def info(self):
        pass

    @property
    def priors(self) -> Set[Prior]:
        """
        A set of all priors encompassed by the contained likelihood models
        """
        return {
            prior
            for model
            in self.model_factors
            for prior
            in model.prior_model.priors
        }

    @property
    def prior_factors(self) -> List[PriorFactor]:
        """
        A list of factors that act as priors on latent variables. One factor exists
        for each unique prior.
        """
        return list(map(PriorFactor, self.priors))

    @property
    def message_dict(self) -> Dict[Prior, NormalMessage]:
        """
        Dictionary mapping priors to messages.

        TODO: should support more than just GaussianPriors/NormalMessages
        """
        return {
            prior: prior
            for prior
            in self.priors
        }

    @property
    def graph(self) -> DeclarativeFactorGraph:
        """
        The complete graph made by combining all factors and priors
        """
        # noinspection PyTypeChecker
        return DeclarativeFactorGraph(
            [
                model
                for model
                in self.model_factors
            ] + self.prior_factors
        )

    def mean_field_approximation(self) -> EPMeanField:
        """
        Returns a EPMeanField of the factor graph
        """
        return EPMeanField.from_approx_dists(
            self.graph,
            self.message_dict
        )

    def _make_ep_optimiser(
            self,
            optimiser: AbstractFactorOptimiser,
            name=None,
    ) -> EPOptimiser:
        return EPOptimiser(
            self.graph,
            name=name or str(Identifier(self)),
            default_optimiser=optimiser,
            factor_optimisers={
                factor: factor.optimiser
                for factor in self.model_factors
                if factor.optimiser is not None
            },
        )

    def optimise(
            self,
            optimiser: AbstractFactorOptimiser,
            name=None,
            **kwargs
    ) -> CollectionPriorModel:
        """
        Use an EP Optimiser to optimise the graph associated with this collection
        of factors and create a Collection to represent the results.

        Parameters
        ----------
        name
            A name for the optimisation. Defaults to identifier derived from this
            instance.
        optimiser
            An optimiser that acts on graphs

        Returns
        -------
        A collection of prior models
        """
        opt = self._make_ep_optimiser(
            optimiser,
            name=name
        )
        updated_model = opt.run(
            self.mean_field_approximation(),
            **kwargs
        )

        collection = CollectionPriorModel({
            factor.name: factor.prior_model
            for factor
            in self.model_factors
        })
        arguments = {
            prior: updated_model.mean_field[
                prior
            ]
            for prior
            in collection.priors
        }

        return collection.gaussian_prior_model_for_arguments(
            arguments
        )

    def visualize(
            self,
            paths: AbstractPaths,
            instance: ModelInstance,
            during_analysis: bool
    ):
        """
        Visualise the instances provided using each factor.

        Instances in the ModelInstance must have the same order as the factors.

        Parameters
        ----------
        paths
            Object describing where data should be saved to
        instance
            A collection of instances, each corresponding to a factor
        during_analysis
            Is this visualisation during analysis?
        """
        for model_factor, instance in zip(
                self.model_factors,
                instance
        ):
            model_factor.visualize(
                paths,
                instance,
                during_analysis
            )

    @property
    def global_prior_model(self) -> CollectionPriorModel:
        """
        A collection of prior models, with one model for each factor.
        """
        return CollectionPriorModel([
            model_factor.prior_model
            for model_factor
            in self.model_factors
        ])
