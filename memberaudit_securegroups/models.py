"""
The models
"""

# Standard Library
import datetime
from collections import defaultdict

# Third Party
import humanize

# Django
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership

# Member Audit
from memberaudit.app_settings import MEMBERAUDIT_APP_NAME
from memberaudit.models import Character, CharacterAsset, General, SkillSet

# Alliance Auth (External Libs)
from eveuniverse.models import EveType


def _get_threshold_date(timedelta_in_days: int) -> datetime:
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

        raise NotImplementedError(_("Please Create a filter!"))

    def audit_filter(self, users):
        """
        Bulk check system that also advises the user with simple messages
        :param users:
        :type users:
        :return:
        :rtype:
        """

        raise NotImplementedError(_("Please Create an audit function!"))


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
                    active_characters = ", ".join(char_list)
                    output[char_user] = {
                        "message": _(f"Active Characters: {active_characters}"),
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

        return _(f"Character Age [{age_threshold}]")

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
                    output[char_user] = {"message": ", ".join(char_list), "check": True}

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

        characters = Character.objects.owned_by_user(user=user)

        return (
            CharacterAsset.objects.filter(
                character__in=characters, eve_type__in=self.assets.all()
            ).count()
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

        character_ownership = CharacterOwnership.objects.filter(
            user__in=users,
            character__memberaudit_character__assets__eve_type__in=self.assets.all(),
        ).values(
            "user__id",
            "character__character_name",
            "character__memberaudit_character__assets__eve_type__name",
        )

        chars = defaultdict(list)

        for character in character_ownership:
            character_name = character["character__character_name"]
            asset_name = character[
                "character__memberaudit_character__assets__eve_type__name"
            ]

            if self.assets.all().count() > 1:
                chars[character["user__id"]].append(f"{character_name} ({asset_name})")
            else:
                chars[character["user__id"]].append(f"{character_name}")

        output = defaultdict(lambda: {"message": "", "check": False})

        for character, char_list in chars.items():
            output[character] = {"message": ", ".join(char_list), "check": True}

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

        is_compliant = General.compliant_users().filter(pk=user.pk).exists()

        return is_compliant

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
            if General.compliant_users().filter(pk=user.pk).exists():
                output[user.pk] = {
                    "message": _(
                        f"All characters have been added to {MEMBERAUDIT_APP_NAME}"
                    ),
                    "check": True,
                }

        return output


class SkillPointFilter(BaseFilter):
    """
    SkillPointFilter
    """

    skill_point_threshold = models.PositiveBigIntegerField(
        help_text=_("Minimum allowable skillpoints.")
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
                    output[char_user] = {"message": ", ".join(char_list), "check": True}

        return output


class SkillSetFilter(BaseFilter):
    """
    SkillSetFilter
    """

    skill_sets = models.ManyToManyField(
        SkillSet,
        help_text=_(
            "Users must possess all of the skills in <strong>one</strong> of the "
            "selected skillsets."
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
                                "message": ", ".join(char_list),
                                "check": True,
                            }

        return output
