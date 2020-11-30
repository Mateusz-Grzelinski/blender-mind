from abc import abstractmethod, ABCMeta
from typing import NoReturn, List


class PredictionModel(metaclass=ABCMeta):
    @abstractmethod
    def update(self, current_command: str) -> NoReturn:
        pass

    @abstractmethod
    def predict(self, current_command: str, n: int) -> List[str]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass
