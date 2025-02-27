import logging
import os
import pickle
from os import path

import dill

from autofit.non_linear import abstract_search

original_create_file_handle = dill._dill._create_filehandle


def _create_file_handle(*args, **kwargs):
    """
    Handle FileNotFoundError when attempting to deserialize pickles
    using dill and return None instead.
    """
    try:
        return original_create_file_handle(
            *args, **kwargs
        )
    except pickle.UnpicklingError as e:
        if not isinstance(
                e.args[0],
                FileNotFoundError
        ):
            raise e
        logging.warning(
            f"Could not create a handler for {e.args[0].filename} as it does not exist"
        )
        return None


dill._dill._create_filehandle = _create_file_handle


class SearchOutput:
    """
    @DynamicAttrs
    """

    def __init__(self, directory: str):
        """
        Represents the output of a single search. Comprises a metadata file and other dataset files.

        Parameters
        ----------
        directory
            The directory of the search
        """
        self.directory = directory
        self.__search = None
        self.__model = None
        self.file_path = os.path.join(directory, "metadata")
        with open(self.file_path) as f:
            self.text = f.read()
            pairs = [
                line.split("=")
                for line
                in self.text.split("\n")
                if "=" in line
            ]
            self.__dict__.update({pair[0]: pair[1] for pair in pairs})

    @property
    def pickle_path(self):
        return path.join(self.directory, "pickles")

    @property
    def model_results(self) -> str:
        """
        Reads the model.results file
        """
        with open(os.path.join(self.directory, "model.results")) as f:
            return f.read()

    @property
    def mask(self):
        """
        A pickled mask object
        """
        with open(
                os.path.join(self.pickle_path, "mask.pickle"), "rb"
        ) as f:
            return dill.load(f)

    def __getattr__(self, item):
        """
        Attempt to load a pickle by the same name from the search output directory.

        dataset.pickle, meta_dataset.pickle etc.
        """
        try:
            with open(
                    os.path.join(self.pickle_path, f"{item}.pickle"), "rb"
            ) as f:
                return pickle.load(f)
        except FileNotFoundError:
            pass

    @property
    def header(self) -> str:
        """
        A header created by joining the search name
        """
        phase = self.phase or ""
        dataset_name = self.dataset_name or ""
        return path.join(phase, dataset_name)

    @property
    def search(self) -> abstract_search.NonLinearSearch:
        """
        The search object that was used in this phase
        """
        if self.__search is None:
            try:
                with open(os.path.join(self.pickle_path, "search.pickle"), "r+b") as f:
                    self.__search = pickle.loads(f.read())
            except FileNotFoundError as e:
                logging.exception(e)
        return self.__search

    @property
    def model(self):
        """
        The model that was used in this phase
        """
        if self.__model is None:
            with open(os.path.join(self.pickle_path, "model.pickle"), "r+b") as f:
                self.__model = pickle.loads(f.read())
        return self.__model

    def __str__(self):
        return self.text

    def __repr__(self):
        return "<PhaseOutput {}>".format(self)
