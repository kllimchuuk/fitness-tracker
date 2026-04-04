import factory
from factory.django import DjangoModelFactory

from authentication.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@test.com")
    age = 25
    height = 175.0
    goal = "Get fit"
    status = User.Status.CUSTOMER

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        raw = extracted or "testpass123"
        obj.set_password(raw)
        if create:
            obj.save()
