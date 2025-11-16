from typing import Type
from typing import TypeVar

from django.db import models

from .base_repository import AbstractRepository

T = TypeVar("T", bound=models.Model)


class BaseRepository(AbstractRepository[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def create(self, **kwargs) -> T:
        return self.model.objects.create(**kwargs)

    def get(self, **filters) -> T | None:
        return self.model.objects.filter(**filters).first()

    def update(self, instance: T, **fields) -> T:
        for key, value in fields.items():
            setattr(instance, key, value)
        instance.save(update_fields=list(fields.keys()))
        return instance

    def delete(self, instance: T) -> None:
        instance.delete()
