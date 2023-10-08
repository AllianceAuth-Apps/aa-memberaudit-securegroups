"""
The models
"""

# Standard Library
import datetime
from collections import defaultdict
from typing import Iterable, List

# Third Party
import humanize

# Django
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo

# Member Audit
from memberaudit.app_settings import MEMBERAUDIT_APP_NAME
from memberaudit.models import Character, CharacterAsset, CharacterRole, SkillSet

# Alliance Auth (External Libs)
from eveuniverse.models import EveType

# Memberaudit Securegroups
from memberaudit_securegroups.memberaudit import MemberAuditChecks


def _get_threshold_date(timedelta_in_days: int) -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=timedelta_in_days
    )


class SingletonModel(models.Model):
    """
    SingletonModel
    """

    class Meta:
        """
        Model meta definitions
        """

        abstract = True

    def delete(self, *args, **kwargs):
        """
        delete action
        :param args:
        :param kwargs:
        :return:
        """

        pass

    def set_cache(self):
        """
        Setting cache
        :return:
        """

        cache.set(self.__class__.__name__, self)

    def save(self, *args, **kwargs):
        """
        Save action
        :param args:
        :param kwargs:
        :return:
        """

        self.pk = 1
        super().save(*args, **kwargs)

        self.set_cache()

    @classmethod
    def load(cls):
        """
        Get cache
        :return:
        """

        if cache.get(cls.__name__) is None:
            obj, created = cls.objects.get_or_create(pk=1)

            if not created:
                obj.set_cache()

        return cache.get(cls.__name__)


class BaseFilter(models.Model):
    """
    BaseFilter
    """

    description = models.CharField(
        max_length=500,
        help_text=_("The filter description that is shown to end users."),
    )  # this is what is shown to the user

    class Meta:
        """
        Model meta definitions
        """

        abstract = True

    def __str__(self):
        """
        Model stringified name
        :return:
        """

        return f"{self.name}: {self.description}"

    def process_filter(self, user: User):
        """
        This is the check run against a users characters
        :param user:
        :return:
        """

        raise NotImplementedError("Please create a filter!")

    def audit_filter(self, users):
        """
        Bulk check system that also advises the user with simple messages
        :param users:
        :type users:
        :return:
        :rtype:
        """

        raise NotImplementedError("Please create an audit function!")


class ActivityFilter(BaseFilter):
    """
    ActivityFilter
    """

    inactivity_threshold = models.PositiveIntegerField(
        help_text=_("Maximum allowable inactivity, in <strong>days</strong>.")
    )

    @property
    def name(self):
        """
        Filter name
        :return:
        """

        inactivity_threshold = ngettext(
            f"{self.inactivity_threshold:d} day",
            f"{self.inactivity_threshold:d} days",
            self.inactivity_threshold,
        )

        return _(f"Activity [Last {inactivity_threshold}]")

    def process_filter(self, user: User):
        """
        Processing filter
        :param user:
        :return:
        """

        threshold_date = _get_threshold_date(
            timedelta_in_days=self.inactivity_threshold
        )

        return (
            Character.objects.owned_by_user(user=user)
            .filter(
                Q(online_status__last_login__gt=threshold_date)
                | Q(online_status__last_logout__gt=threshold_date),
            )
            .count()
            > 0
        )

    def audit_filter(self, users):
        """
        Audit Filter
        :param users:
        :type users:
        :return:
        :rtype:
        """

        threshold_date = _get_threshold_date(
            timedelta_in_days=self.inactivity_threshold
        )

        output = defaultdict(lambda: {"message": "", "check": False})

        for user in users:
            characters = Character.objects.owned_by_user(user=user).filter(
                Q(online_status__last_login__gt=threshold_date)
                | Q(online_status__last_logout__gt=threshold_date),
            )

            if characters.count() > 0:
                chars = defaultdict(list)

                for char in characters:
                    chars[char.user.pk].append(char.eve_character.character_name)

                for char_user, char_list in chars.items():
                    message = ngettext(
                        "Active character: ", "Active characters: ", len(char_list)
                    )

                    output[char_user] = {
                        "message": message + ", ".join(sorted(char_list)),
                        "check": True,
                    }

        return output


class AgeFilter(BaseFilter):
    """
    AgeFilter
    """

    age_threshold = models.PositiveIntegerField(
        help_text=_("Minimum allowable age, in <strong>days</strong>.")
    )

    @property
    def name(self):
        """
        Filter name
        :return:
        """

        age_threshold = ngettext(
            f"{self.age_threshold:d} day",
            f"{self.age_threshold:d} days",
            self.age_threshold,
        )

        return _(f"Character age [{age_threshold}]")

    def process_filter(self, user: User):
        """
        Processing filter
        :param user:
        :return:
        """

        threshold_date = _get_threshold_date(timedelta_in_days=self.age_threshold)

        return (
            Character.objects.owned_by_user(user=user)
            .filter(details__birthday__lt=threshold_date)
            .count()
            > 0
        )

    def audit_filter(self, users):
        """
        Audit Filter
        :param users:
        :type users:
        :return:
        :rtype:
        """

        threshold_date = _get_threshold_date(timedelta_in_days=self.age_threshold)

        output = defaultdict(lambda: {"message": "", "check": False})

        for user in users:
            characters = Character.objects.owned_by_user(user=user).filter(
                details__birthday__lt=threshold_date
            )

            if characters.count() > 0:
                chars = defaultdict(list)

                for char in characters:
                    chars[char.user.pk].append(char.eve_character.character_name)

                for char_user, char_list in chars.items():
                    output[char_user] = {
                        "message": ", ".join(sorted(char_list)),
                        "check": True,
                    }

        return output


class AssetFilter(BaseFilter):
    """
    AssetFilter
    """

    assets = models.ManyToManyField(
        EveType,
        help_text=_("User must possess <strong>one</strong> of the selected assets."),
    )

    @property
    def name(self):
        """
        Filter name
        :return:
        """

        return _("Member Audit Asset")

    def process_filter(self, user: User):
        """
        Processing filter
        :param user:
        :return:
        """
        return CharacterAsset.objects.filter(
            character__eve_character__character_ownership__user=user,
            eve_type__in=self.assets.all(),
        ).exists()

    def audit_filter(self, users):
        """
        Audit Filter
        :param users:
        :type users:
        :return:
        :rtype:
        """
        matching_characters = Character.objects.filter(
            eve_character__character_ownership__user__in=list(users),
            assets__eve_type__in=list(self.assets.all()),
        ).values(
            user_id=F("eve_character__character_ownership__user_id"),
            character_name=F("eve_character__character_name"),
            asset_name=F("assets__eve_type__name"),
        )

        output_characters = defaultdict(list)
        for user_id in matching_characters:
            character_name = user_id["character_name"]
            asset_name = user_id["asset_name"]

            if self.assets.all().count() > 1:
                output_characters[user_id["user_id"]].append(
                    f"{character_name} ({asset_name})"
                )
            else:
                output_characters[user_id["user_id"]].append(f"{character_name}")

        output = {}
        for user_id, characters in output_characters.items():
            output[user_id] = {
                "message": ", ".join(sorted(characters)),
                "check": True,
            }

        return output


class ComplianceFilter(BaseFilter, SingletonModel):
    """
    ComplianceFilter
    """

    @property
    def name(self):
        """
        Filter name
        :return:
        """

        return _("Compliance")

    def process_filter(self, user: User):
        """
        Processing filter
        :param user:
        :return:
        """

        compliance_check = MemberAuditChecks.compliance(user=user)

        return compliance_check["is_compliant"]

    def audit_filter(self, users):
        """
        Audit Filter
        :param users:
        :type users:
        :return:
        :rtype:
        """

        output = defaultdict(
            lambda: {
                "message": _(
                    f"Not all of your characters are added to {MEMBERAUDIT_APP_NAME}"
                ),
                "check": False,
            }
        )

        for user in users:
            compliance_check = MemberAuditChecks.compliance(user=user)

            if compliance_check["is_compliant"]:
                output[user.pk] = {
                    "message": _(
                        f"All characters have been added to {MEMBERAUDIT_APP_NAME}"
                    ),
                    "check": True,
                }
            else:
                unregistered_chars = compliance_check["unregistered_chars"]

                missing_characters_message = ngettext(
                    "Missing character: ",
                    "Missing characters: ",
                    unregistered_chars.count(),
                )

                output[user.pk] = {
                    "message": missing_characters_message
                    + ", ".join(
                        str(char.character_name) for char in unregistered_chars
                    ),
                    "check": False,
                }

        return output


class CorporationRoleFilter(BaseFilter):
    """Filter for corporation roles."""

    corporations = models.ManyToManyField(
        EveCorporationInfo,
        related_name="+",
        help_text=_("The character with the role must be in one of these corporation."),
    )
    role = models.CharField(
        max_length=3,
        choices=CharacterRole.Role.choices,
        db_index=True,
        help_text=_("User must have a character with this role."),
    )
    mains_only = models.BooleanField(
        default=True, help_text=_("When True only main characters are considered.")
    )

    @property
    def name(self):
        """Return name of this filter."""
        return _("Member Audit Corporation Role")

    def process_filter(self, user: User) -> bool:
        """Return True when filter applies to the user, else False."""
        qs = CharacterRole.objects.filter(
            character__eve_character__character_ownership__user=user,
            character__eve_character__corporation_id__in=self._corporation_ids(),
            role=self.role,
            location=CharacterRole.Location.UNIVERSAL,
        )
        if self.mains_only:
            qs = qs.filter(character__eve_character__userprofile__isnull=False)
        return qs.exists()

    def audit_filter(self, users: Iterable[User]) -> dict:
        """Return result of filter audit for given users."""
        qs = Character.objects.filter(
            eve_character__character_ownership__user__in=list(users),
            eve_character__corporation_id__in=self._corporation_ids(),
            roles__role=self.role,
            roles__location=(CharacterRole.Location.UNIVERSAL),
        )
        if self.mains_only:
            qs = qs.filter(eve_character__userprofile__isnull=False)

        matching_characters = qs.values(
            user_id=F("eve_character__character_ownership__user_id"),
            character_name=F("eve_character__character_name"),
        )

        user_with_characters = defaultdict(list)
        for user_id in matching_characters:
            character_name = user_id["character_name"]
            user_with_characters[user_id["user_id"]].append(f"{character_name}")

        output = {}
        for user_id, character_names in user_with_characters.items():
            output[user_id] = {
                "message": ", ".join(sorted(character_names)),
                "check": True,
            }

        return output

    def _corporation_ids(self) -> List[int]:
        """Return Eve IDs of corporations in this filter."""
        return list(self.corporations.values_list("corporation_id", flat=True))


class SkillPointFilter(BaseFilter):
    """
    SkillPointFilter
    """

    skill_point_threshold = models.PositiveBigIntegerField(
        help_text=_("Minimum allowable skill points.")
    )

    @property
    def name(self):
        """
        Filter name
        :return:
        """

        sp_threshold = humanize.intword(self.skill_point_threshold)

        skill_point_threshold = ngettext(
            f"{sp_threshold} skill point",
            f"{sp_threshold} skill points",
            self.skill_point_threshold,
        )

        return _(f"Member Audit Skill Points [{skill_point_threshold}]")

    def process_filter(self, user: User):
        """
        Processing filter
        :param user:
        :return:
        """

        return (
            Character.objects.owned_by_user(user=user)
            .filter(skillpoints__total__gt=self.skill_point_threshold)
            .count()
            > 0
        )

    def audit_filter(self, users):
        """
        Audit Filter
        :param users:
        :type users:
        :return:
        :rtype:
        """

        output = defaultdict(lambda: {"message": "", "check": False})

        for user in users:
            characters = Character.objects.owned_by_user(user=user).filter(
                skillpoints__total__gt=self.skill_point_threshold
            )

            if characters.count() > 0:
                chars = defaultdict(list)

                for char in characters:
                    chars[char.user.pk].append(char.eve_character.character_name)

                for char_user, char_list in chars.items():
                    output[char_user] = {
                        "message": ", ".join(sorted(char_list)),
                        "check": True,
                    }

        return output


class SkillSetFilter(BaseFilter):
    """
    SkillSetFilter
    """

    skill_sets = models.ManyToManyField(
        SkillSet,
        help_text=_(
            "Users must possess all of the skills in <strong>one</strong> of the "
            "selected skill sets."
        ),
    )

    @property
    def name(self):
        """
        Filter name
        :return:
        """

        return _("Member Audit Skill Set")

    def process_filter(self, user: User):
        """
        Processing filter
        :param user:
        :return:
        """

        characters = Character.objects.owned_by_user(user=user)

        for character in characters:
            for check in character.skill_set_checks.filter(
                skill_set__in=self.skill_sets.all()
            ):
                if check.failed_required_skills.count() == 0:
                    return True

        return False

    def audit_filter(self, users):
        """
        Audit Filter
        :param users:
        :type users:
        :return:
        :rtype:
        """

        output = defaultdict(lambda: {"message": "", "check": False})

        for user in users:
            chars = defaultdict(list)
            characters = Character.objects.owned_by_user(user=user)

            for character in characters:
                for check in character.skill_set_checks.filter(
                    skill_set__in=self.skill_sets.all()
                ):
                    if check.failed_required_skills.count() == 0:
                        chars[character.user.pk].append(
                            character.eve_character.character_name
                        )

                        for char_user, char_list in chars.items():
                            output[char_user] = {
                                "message": ", ".join(sorted(char_list)),
                                "check": True,
                            }

        return output
