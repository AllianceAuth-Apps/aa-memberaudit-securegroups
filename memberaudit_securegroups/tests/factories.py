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
