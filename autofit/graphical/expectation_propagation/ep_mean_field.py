import logging
from typing import (
    Dict, Tuple, Optional, List
)

import numpy as np

from autofit.graphical.factor_graphs import (
    Factor, FactorGraph
)
from autofit.graphical.mean_field import MeanField, FactorApproximation
from autofit.graphical.utils import Status
from autofit.mapper.variable import Variable
from autofit.messages.abstract import AbstractMessage

logger = logging.getLogger(
    __name__
)


class EPMeanField(FactorGraph):
    '''
    this class encode the EP mean-field approximation to a factor graph


    Attributes
    ----------
    factor_graph: FactorGraph
        the base factor graph being approximated

    factor_mean_field: Dict[Factor, MeanField]
        the mean-field approximation for each factor in the factor graph

    mean_field: MeanField
        the mean-field approximation of the full factor graph
        i.e. the product of the factor mean-field approximations

    variables: Set[Variable]
        the variables of the approximation

    deterministic_variables: Set[Variable]
        the deterministic variables

    log_evidence: float
        the approximate log evidence of the approximation

    is_valid: bool
        returns whether the factor mean-field approximations are all valid

    Methods
    -------
    from_approx_dists(factor_graph, approx_dists)
        create a EPMeanField object from the passed factor_graph
        using approx_dists to initialise the factor mean-field approximations

    factor_approximation(factor)
        create the FactorApproximation for the factor

    project_factor_approx(factor_approximation)
        given the passed FactorApproximation, return a new `EPMeanField`
        object encoding the updated mean-field approximation
    '''

    def __init__(
            self,
            factor_graph: FactorGraph,
            factor_mean_field: Dict[Factor, MeanField]
    ):
        self._factor_graph = factor_graph
        self._factor_mean_field = factor_mean_field

        super().__init__(self.factor_graph.factors)

    @property
    def name(self):
        return f"EP_{self.factor_graph.name}"

    @property
    def variables(self):
        return self.factor_graph.variables

    @property
    def deterministic_variables(self):
        return self.factor_graph.deterministic_variables

    @property
    def factor_mean_field(self) -> Dict[Factor, MeanField]:
        return self._factor_mean_field.copy()

    @property
    def factor_graph(self) -> FactorGraph:
        return self._factor_graph

    @classmethod
    def from_approx_dists(
            cls,
            factor_graph: FactorGraph,
            approx_dists: Dict[Variable, AbstractMessage],
    ) -> "EPMeanField":
        factor_mean_field = {
            factor: MeanField({
                v: approx_dists[v] for v in factor.all_variables
            })
            for factor in factor_graph.factors
        }

        return cls(
            factor_graph,
            factor_mean_field
        )

    from_kws = from_approx_dists

    def factor_approximation(self, factor: Factor) -> FactorApproximation:
        """
        Create an approximation for one factor.

        This comprises:
        - The factor
        - The factor's variable distributions
        - The cavity distribution, which is the product of the distributions
        for each variable for all other factors
        - The model distribution, which is the product of the distributions
        for each variable for all factors

        Parameters
        ----------
        factor
            Some factor

        Returns
        -------
        An object comprising distributions with a specific distribution excluding
        that factor
        """
        factor_mean_field = self._factor_mean_field.copy()
        factor_dist = factor_mean_field.pop(factor)
        cavity_dist = MeanField({
            v: 1. for v
            in factor_dist.all_variables
        }).prod(
            *factor_mean_field.values()
        )

        model_dist = factor_dist.prod(cavity_dist)

        return FactorApproximation(
            factor,
            cavity_dist,
            factor_dist,
            model_dist
        )

    def project_factor_approx(
            self, projection: FactorApproximation, status: Optional[Status] = None,
    ) -> Tuple["EPMeanField", Status]:
        """
        """
        factor_mean_field = self.factor_mean_field
        factor_mean_field[projection.factor] = projection.factor_dist

        new_approx = type(self)(
            factor_graph=self._factor_graph,
            factor_mean_field=factor_mean_field)
        return new_approx, status

    project = project_factor_approx

    @property
    def mean_field(self) -> MeanField:
        return MeanField({
            v: 1. for v in self.all_variables
        }).prod(
            *self._factor_mean_field.values()
        )

    model_dist = mean_field

    @property
    def variable_messages(self) -> Dict[Variable, List[AbstractMessage]]:
        variable_messages = {
            v: [] for v in self.all_variables}
        for meanfield in self.factor_mean_field.values():
            for v, message in meanfield.items():
                variable_messages[v].append(message)

        return variable_messages

    @property
    def variable_evidence(self) -> Dict[Variable, np.ndarray]:
        return {
            v: AbstractMessage.log_normalisation(*ms)
            for v, ms in self.variable_messages.items()
        }

    @property
    def factor_evidence(self) -> Dict[Factor, np.ndarray]:
        return {
            factor: meanfield.log_norm
            for factor, meanfield in self.factor_mean_field.items()
        }

    @property
    def log_evidence(self):
        """
        Calculates evidence for the EP approximation

        Evidence for a variable, xᵢ,

        Zᵢ = ∫ ∏ₐ m_{a → i} (xᵢ) dxᵢ

        Evidence for a factor, f_a,

                ∫ ∏_{j ∈ a} m_{i → a} (xᵢ) fₐ(xₐ) dxₐ
        Zₐ = -----------------------------------------
                             ∏_{j ∈ a} Zⱼ

        Evidence for model

        Z = ∏ᵢ Zᵢ ∏ₐ Zₐ
        """
        variable_evidence = {
            v: np.sum(logz) for v, logz in self.variable_evidence.items()}
        factor_evidence = sum(
            np.sum(meanfield.log_norm)
            - sum(variable_evidence[v] for v in factor.all_variables)
            for factor, meanfield in self.factor_mean_field.items()
        )
        return factor_evidence + sum(variable_evidence.values())

    def __repr__(self) -> str:
        clsname = type(self).__name__
        try:
            log_evidence = self.log_evidence
        except Exception as e:
            logger.exception(e)
            log_evidence = float("nan")
        return (
            f"{clsname}({self.factor_graph}, "
            f"log_evidence={log_evidence})")
