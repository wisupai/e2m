from abc import ABC, abstractmethod
from typing import Any


class BaseStrategy(ABC):
    TYPE = None

    @abstractmethod
    def run(self, **kwargs) -> Any:
        pass
