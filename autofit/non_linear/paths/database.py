from sqlalchemy.orm.exc import NoResultFound

from .abstract import AbstractPaths
from ...database import Fit


class DatabasePaths(AbstractPaths):
    def __init__(
            self,
            session,
            name="",
            path_prefix=""
    ):
        super().__init__(
            name=name,
            path_prefix=path_prefix,
        )
        self.session = session

    def save_object(self, name: str, obj: object):
        self._fit[name] = obj

    def load_object(self, name: str):
        return self._fit[name]

    def remove_object(self, name: str):
        del self._fit[name]

    def is_object(self, name: str) -> bool:
        return name in self._fit

    @property
    def _fit(self) -> Fit:
        try:
            return self.session.query(
                Fit
            ).filter(
                Fit.id == self.identifier
            ).one()
        except NoResultFound:
            fit = Fit(
                id=self.identifier,
                is_complete=False
            )
            self.session.add(
                fit
            )
            return fit

    @property
    def is_complete(self) -> bool:
        return self._fit.is_complete

    def completed(self):
        self._fit.is_complete = True

    def load_samples(self):
        pass

    def load_samples_info(self):
        pass

    def save_summary(self, samples, log_likelihood_function_time):
        pass

    def save_all(self, info, pickle_files):
        pass
