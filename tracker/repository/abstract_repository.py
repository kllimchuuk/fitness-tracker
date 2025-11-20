from abc import ABC
from abc import abstractmethod
from typing import Generic
from typing import TypeVar

T = TypeVar("T")


class AbstractRepository(ABC, Generic[T]):
    @abstractmethod
    def create(self, **kwargs) -> T:
        raise NotImplementedError()

    @abstractmethod
    def get(self, **filters) -> T | None:
        raise NotImplementedError()

    @abstractmethod
    def update(self, instance: T, **fields) -> T:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, instance: T) -> None:
        raise NotImplementedError()
