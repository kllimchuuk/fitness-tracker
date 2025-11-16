from abc import ABC
from abc import abstractmethod
from typing import Generic
from typing import TypeVar

T = TypeVar("T")


class AbstractRepository(ABC, Generic[T]):
    @abstractmethod
    def create(self, **kwargs) -> T:
        pass

    @abstractmethod
    def get(self, **filters) -> T | None:
        pass

    @abstractmethod
    def update(self, instance: T, **fields) -> T:
        pass

    @abstractmethod
    def delete(self, instance: T) -> None:
        pass
