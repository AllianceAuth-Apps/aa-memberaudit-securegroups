"""
Admin pages
"""

# Standard Library
from typing import Any

# Third Party
import humanize

# Django
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.utils.translation import ngettext

# Memberaudit Securegroups
from memberaudit_securegroups.models import (
    ActivityFilter,
    AgeFilter,
    AssetFilter,
    ComplianceFilter,
    CorporationRoleFilter,
    SkillPointFilter,
    SkillSetFilter,
)


class SingletonModelAdmin(admin.ModelAdmin):
    """
    Prevents Django admin users deleting the singleton or adding extra rows.
    """

    actions = None  # Removes the default delete action.

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return self.model.objects.all().count() == 0


@admin.register(ActivityFilter)
class ActivityFilterAdmin(admin.ModelAdmin):
    """
    ActivityFilterAdmin
    """

    list_display = ("description", "_inactivity_threshold")

    def _inactivity_threshold(self, obj):
        inactivity_threshold = obj.inactivity_threshold

        return_value = ngettext(
            f"{inactivity_threshold:d} day",
            f"{inactivity_threshold:d} days",
            inactivity_threshold,
        )

        return return_value


@admin.register(AgeFilter)
class AgeFilterAdmin(admin.ModelAdmin):
    """
    AgeFilterAdmin
    """

    list_display = ("description", "_age_threshold")

    def _age_threshold(self, obj):
        return f"{obj.age_threshold:d} days"


@admin.register(AssetFilter)
class AssetFilterAdmin(admin.ModelAdmin):
    """
    AssetFilterAdmin
    """

    list_display = ("description", "_assets")
    autocomplete_fields = ["assets"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request)
        return qs.prefetch_related("assets")

    @admin.display()
    def _assets(self, obj) -> str:
        objs = obj.assets.all()
        return ", ".join(sorted([obj.name for obj in objs]))


@admin.register(ComplianceFilter)
class ComplianceFilterAdmin(SingletonModelAdmin):
    """
    ComplianceFilterAdmin
    """

    list_display = ("description",)


@admin.register(CorporationRoleFilter)
class CorporationRoleFilterAdmin(admin.ModelAdmin):
    list_display = ("description", "role", "_corporations", "mains_only")
    filter_horizontal = ("corporations",)
    fields = ("description", "role", "corporations", "mains_only")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request)
        return qs.prefetch_related("corporations")

    @admin.display()
    def _corporations(self, obj) -> str:
        objs = obj.corporations.all()
        return ", ".join(sorted([obj.corporation_name for obj in objs]))


@admin.register(SkillPointFilter)
class SkillPointFilterAdmin(admin.ModelAdmin):
    """
    SkillPointFilterAdmin
    """

    list_display = ("description", "_skill_point_threshold")

    def _skill_point_threshold(self, obj):
        skillpoints = humanize.intword(obj.skill_point_threshold)

        return f"{skillpoints} skill points"


@admin.register(SkillSetFilter)
class SkillSetFilterAdmin(admin.ModelAdmin):
    """
    SkillSetFilterAdmin
    """

    list_display = ("description",)
    filter_horizontal = ("skill_sets",)
