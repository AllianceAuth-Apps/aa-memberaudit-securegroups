# Standard Library
from typing import Iterable

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo

# Member Audit
from memberaudit.models import CharacterRole

# Memberaudit Securegroups
from memberaudit_securegroups.models import (
    CorporationRoleFilter,
    CorporationTitleFilter,
    MinimumCorporationMembership,
)


def create_corporation_role_filter(
    corporations: Iterable[EveCorporationInfo], **kwargs
) -> CorporationRoleFilter:
    params = {"role": CharacterRole.Role.DIRECTOR}
    params.update(kwargs)
    obj: CorporationRoleFilter = CorporationRoleFilter.objects.create(**params)
    if corporations:
        obj.corporations.add(*list(corporations))
    return obj


def create_corporation_title_filter(
    corporations: Iterable[EveCorporationInfo], **kwargs
) -> CorporationTitleFilter:
    params = {"title": "title"}
    params.update(kwargs)
    obj: CorporationTitleFilter = CorporationTitleFilter.objects.create(**params)
    if corporations:
        obj.corporations.add(*list(corporations))
    return obj


def create_minimum_corporation_membership_filter(
    **kwargs,
) -> MinimumCorporationMembership:
    params = {"days": 30}
    params.update(kwargs)
    obj: MinimumCorporationMembership = MinimumCorporationMembership.objects.create(
        **params
    )
    return obj
