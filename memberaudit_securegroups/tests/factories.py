# Memberaudit Securegroups
from memberaudit_securegroups.models import CorporationTitleFilter


def create_corporation_title_filter(
    corporations=None, **kwargs
) -> CorporationTitleFilter:
    params = {"title": "title"}
    params.update(kwargs)
    obj: CorporationTitleFilter = CorporationTitleFilter.objects.create(**params)
    if corporations:
        obj.corporations.add(*corporations)
    return obj
