from typing import Generic, TypeVar

import factory

from memberaudit.models import CharacterRole
from memberaudit.tests.testdata.factories_2 import LocationStationFactory

from memberaudit_securegroups.models import (
    CorporationRoleFilter,
    CorporationTitleFilter,
    HomeStationFilter,
    TimeInCorporationFilter,
)

T = TypeVar("T")


class BaseMetaFactory(Generic[T], factory.base.FactoryMetaClass):
    def __call__(cls, *args, **kwargs) -> T:
        return super().__call__(*args, **kwargs)


class CorporationRoleFilterFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[CorporationRoleFilter]
):
    class Meta:
        model = CorporationRoleFilter

    role = CharacterRole.Role.DIRECTOR

    @factory.post_generation
    def corporations(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.corporations.add(*extracted)


class CorporationTitleFilterFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CorporationTitleFilter],
):
    class Meta:
        model = CorporationTitleFilter

    title = "title"

    @factory.post_generation
    def corporations(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.corporations.add(*extracted)


class TimeInCorporationFilterFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[TimeInCorporationFilter],
):
    class Meta:
        model = TimeInCorporationFilter

    minimum_days = 30


class HomeStationFilterFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[HomeStationFilter]
):
    class Meta:
        model = HomeStationFilter

    home_station = factory.SubFactory(LocationStationFactory)
    include_alts = False
