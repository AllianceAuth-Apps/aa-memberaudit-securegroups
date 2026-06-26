"""
Tests for models of the memberaudit_securegroups app
"""

# Standard Library
import datetime as dt

# Django
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.timezone import now

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo

# Member Audit
from memberaudit.app_settings import MEMBERAUDIT_APP_NAME
from memberaudit.models import CharacterRole
from memberaudit.tests.testdata.factories import (
    create_character_asset,
    create_character_corporation_history,
    create_character_role,
    create_character_skill_set_check,
    create_character_title,
    create_skill_set,
    create_skill_set_skill,
)
from memberaudit.tests.testdata.load_entities import load_entities
from memberaudit.tests.testdata.load_eveuniverse import load_eveuniverse
from memberaudit.tests.utils import (
    add_auth_character_to_user,
    add_memberaudit_character_to_user,
    create_memberaudit_character,
    create_user_from_evecharacter_with_access,
)

# Alliance Auth (External Libs)
from eveuniverse.models import EveEntity, EveType

# Memberaudit Securegroups
from memberaudit_securegroups.models import (
    AssetFilter,
    ComplianceFilter,
    SkillSetFilter,
)

from .factories import (
    create_corporation_role_filter,
    create_corporation_title_filter,
    create_time_in_corporation_filter,
)


def make_user_queryset(*users):
    """
    Create a queryset of users from a list of users.

    :param users:
    :type users:
    :return:
    :rtype:
    """

    params = {"pk__in": [obj.pk for obj in users]}

    return User.objects.filter(**params)


class TestAssetFilter(TestCase):
    """
    Tests for the `AssetFilter` model
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Setup for the test case

        :return:
        :rtype:
        """

        super().setUpClass()

        load_entities()
        load_eveuniverse()

        cls.character_1001 = create_memberaudit_character(1001)
        cls.user_1 = cls.character_1001.character_ownership.user

    def test_should_return_name(self):
        """
        Test that the name is returned

        :return:
        :rtype:
        """

        # given
        my_filter = AssetFilter.objects.create()

        # when/then
        self.assertTrue(my_filter.name)

    def test_should_return_false_when_user_does_not_have_asset(self):
        """
        Test that the filter returns False when the user does not have the asset

        :return:
        :rtype:
        """

        # given
        my_filter = AssetFilter.objects.create()
        merlin_type = EveType.objects.get(name="Merlin")
        my_filter.assets.add(merlin_type)
        astrahus_type = EveType.objects.get(name="Astrahus")
        create_character_asset(character=self.character_1001, eve_type=astrahus_type)
        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_true_when_user_has_asset(self):
        """
        Test that the filter returns True when the user has the asset

        :return:
        :rtype:
        """

        # given
        my_filter = AssetFilter.objects.create()
        merlin_type = EveType.objects.get(name="Merlin")
        my_filter.assets.add(merlin_type)
        create_character_asset(character=self.character_1001, eve_type=merlin_type)
        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1))

    def test_should_return_true_when_user_has_at_least_one_asset(self):
        """
        Test that the filter returns True when the user has at least one asset

        :return:
        :rtype:
        """

        # given
        my_filter = AssetFilter.objects.create()
        merlin_type = EveType.objects.get(name="Merlin")
        astrahus_type = EveType.objects.get(name="Astrahus")
        my_filter.assets.add(merlin_type, astrahus_type)
        create_character_asset(character=self.character_1001, eve_type=merlin_type)
        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1))

    def test_should_return_audit_data_for_one_matching_one_not_matching_user(self):
        """
        Test that the audit filter returns the correct data for two users

        :return:
        :rtype:
        """

        # given a filter for Merlins
        my_filter = AssetFilter.objects.create()
        merlin_type = EveType.objects.get(name="Merlin")
        my_filter.assets.add(merlin_type)

        # and main user's character has a Merlin
        create_character_asset(character=self.character_1001, eve_type=merlin_type)

        # and main user's 2nd character also has a Merlin
        character_1002 = add_memberaudit_character_to_user(self.user_1, 1002)
        create_character_asset(character=character_1002, eve_type=merlin_type)

        # and a 2nd user has a registered character, but no Merlin
        character_1003 = create_memberaudit_character(1003)
        user_1002 = character_1003.character_ownership.user
        # and a 3rd user is not registered
        user_2, _ = create_user_from_evecharacter_with_access(1101)

        # when
        users = make_user_queryset(self.user_1, user_1002, user_2)
        result = my_filter.audit_filter(users)

        # then
        self.assertDictEqual(
            result[self.user_1.id],
            {"message": "Bruce Wayne (Merlin), Clark Kent (Merlin)", "check": True},
        )
        self.assertDictEqual(
            result[user_1002.id],
            {"message": "No matching assets found", "check": False},
        )
        self.assertDictEqual(
            result[user_2.id], {"message": "No audit information found", "check": False}
        )
        self.assertEqual(len(result), 3)

    def test_should_return_audit_data_when_no_matches(self):
        """
        Test that the audit filter returns the correct data for a user with no matching assets

        :return:
        :rtype:
        """

        # given
        my_filter = AssetFilter.objects.create()

        # when
        users = make_user_queryset(self.user_1)
        result = my_filter.audit_filter(users)

        # then
        self.assertEqual(len(result), 1)
        self.assertDictEqual(
            result[self.user_1.id],
            {"message": "No matching assets found", "check": False},
        )


class TestComplianceFilter(TestCase):
    """
    Tests for the `ComplianceFilter` model
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Setup for the test case

        :return:
        :rtype:
        """

        super().setUpClass()

        load_entities()

        cls.user_1, _ = create_user_from_evecharacter_with_access(1001)
        cls.compliance_filter = ComplianceFilter.objects.create()
        cls.compliance_filter_reversed = ComplianceFilter.objects.create(
            reversed_logic=True
        )

    def test_should_return_name(self):
        """
        Test that the name is returned

        :return:
        :rtype:
        """

        self.assertTrue(self.compliance_filter.name)

    def test_should_return_true_when_user_is_compliant_1(self):
        """
        Test that the filter returns True when the user is compliant with 1 character

        :return:
        :rtype:
        """

        # given a user with 1 registered character
        add_memberaudit_character_to_user(self.user_1, 1001)

        # when/then
        self.assertTrue(self.compliance_filter.process_filter(self.user_1))

    def test_should_return_true_when_user_is_compliant_2(self):
        """
        Test that the filter returns True when the user is compliant with 2 characters

        :return:
        :rtype:
        """

        # given a user with 2 registered character
        add_memberaudit_character_to_user(self.user_1, 1001)
        add_memberaudit_character_to_user(self.user_1, 1002)

        # when/then
        self.assertTrue(self.compliance_filter.process_filter(self.user_1))

    def test_should_return_false_when_user_is_compliant_1_reversed(self):
        """
        Test that the filter returns False when the user is compliant with 1 character and reversed logic

        :return:
        :rtype:
        """

        # given a user with 1 registered character
        add_memberaudit_character_to_user(self.user_1, 1001)

        # when/then
        self.assertFalse(self.compliance_filter_reversed.process_filter(self.user_1))

    def test_should_return_false_when_user_is_compliant_2_reversed(self):
        """
        Test that the filter returns False when the user is compliant with 2 characters and reversed logic

        :return:
        :rtype:
        """

        # given a user with 2 registered character
        add_memberaudit_character_to_user(self.user_1, 1001)
        add_memberaudit_character_to_user(self.user_1, 1002)

        # when/then
        self.assertFalse(self.compliance_filter_reversed.process_filter(self.user_1))

    def test_should_return_false_when_user_is_not_compliant_1(self):
        """
        Test that the filter returns False when the user is not compliant with 1 character

        :return:
        :rtype:
        """

        self.assertFalse(self.compliance_filter.process_filter(self.user_1))

    def test_should_return_false_when_user_is_not_compliant_2(self):
        """
        Test that the filter returns False when the user is not compliant with 2 characters

        :return:
        :rtype:
        """

        # given a user with 1 registered and 1 unregistered character
        add_memberaudit_character_to_user(self.user_1, 1001)
        add_auth_character_to_user(self.user_1, 1002)

        # when/then
        self.assertFalse(self.compliance_filter.process_filter(self.user_1))

    def test_should_return_true_when_user_is_not_compliant_1_reversed(self):
        """
        Test that the filter returns True when the user is not compliant with 1 character and reversed logic

        :return:
        :rtype:
        """

        self.assertTrue(self.compliance_filter_reversed.process_filter(self.user_1))

    def test_should_return_true_when_user_is_not_compliant_2_reversed(self):
        """
        Test that the filter returns True when the user is not compliant with 2 characters and reversed logic

        :return:
        :rtype:
        """

        # given a user with 1 registered and 1 unregistered character
        add_memberaudit_character_to_user(self.user_1, 1001)
        add_auth_character_to_user(self.user_1, 1002)

        # when/then
        self.assertTrue(self.compliance_filter_reversed.process_filter(self.user_1))

    def test_should_return_audit_data_for_users(self):
        """
        Test that the audit filter returns the correct data for two users

        :return:
        :rtype:
        """

        # given
        add_memberaudit_character_to_user(self.user_1, 1001)
        user_2, _ = create_user_from_evecharacter_with_access(1101)

        # when
        users = make_user_queryset(self.user_1, user_2)
        result = self.compliance_filter.audit_filter(users)

        # then
        self.assertEqual(len(result), 2)
        result_user_1001 = result[self.user_1.pk]
        self.assertTrue(result_user_1001["check"])
        self.assertEqual(
            result_user_1001["message"],
            f"All characters have been added to {MEMBERAUDIT_APP_NAME}",
        )
        result_user_1101 = result[user_2.pk]
        self.assertFalse(result_user_1101["check"])
        self.assertIn("Lex Luther", result_user_1101["message"])

    def test_should_return_audit_data_for_users_reversed(self):
        """
        Test that the audit filter returns the correct data for two users with reversed logic

        :return:
        :rtype:
        """

        # given
        add_memberaudit_character_to_user(self.user_1, 1001)
        user_2, _ = create_user_from_evecharacter_with_access(1101)

        # when
        users = make_user_queryset(self.user_1, user_2)
        result = self.compliance_filter_reversed.audit_filter(users)

        # then
        self.assertEqual(len(result), 2)

        result_user_1001 = result[self.user_1.pk]
        self.assertFalse(result_user_1001["check"])
        self.assertEqual(
            result_user_1001["message"],
            f"All characters have been added to {MEMBERAUDIT_APP_NAME}",
        )

        result_user_1101 = result[user_2.pk]
        self.assertTrue(result_user_1101["check"])
        self.assertIn("Lex Luther", result_user_1101["message"])

    def test_should_return_audit_data_for_non_compliant_user_with_1_character(self):
        """
        Test that the audit filter returns the correct data for a non-compliant user with 1 character

        :return:
        :rtype:
        """

        # when
        users = make_user_queryset(self.user_1)
        result = self.compliance_filter.audit_filter(users)

        # then
        expected = {
            self.user_1.pk: {
                "check": False,
                "message": "Missing character: Bruce Wayne",
            },
        }
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_for_non_compliant_user_with_1_character_reversed(
        self,
    ):
        """
        Test that the audit filter returns the correct data for a non-compliant user with 1 character and reversed logic

        :return:
        :rtype:
        """

        # when
        users = make_user_queryset(self.user_1)
        result = self.compliance_filter_reversed.audit_filter(users)

        # then
        expected = {
            self.user_1.pk: {
                "check": True,
                "message": "Missing character: Bruce Wayne",
            },
        }
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_for_non_compliant_user_with_2_characters(self):
        """
        Test that the audit filter returns the correct data for a non-compliant user with 2 characters

        :return:
        :rtype:
        """

        # given
        add_auth_character_to_user(self.user_1, 1002)

        # when
        users = make_user_queryset(self.user_1)
        result = self.compliance_filter.audit_filter(users)

        # then
        expected = {
            self.user_1.pk: {
                "check": False,
                "message": "Missing characters: Bruce Wayne, Clark Kent",
            },
        }
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_for_non_compliant_user_with_2_characters_reversed(
        self,
    ):
        """
        Test that the audit filter returns the correct data for a non-compliant user with 2 characters and reversed logic

        :return:
        :rtype:
        """

        # given
        add_auth_character_to_user(self.user_1, 1002)

        # when
        users = make_user_queryset(self.user_1)
        result = self.compliance_filter_reversed.audit_filter(users)

        # then
        expected = {
            self.user_1.pk: {
                "check": True,
                "message": "Missing characters: Bruce Wayne, Clark Kent",
            },
        }
        self.assertDictEqual(result, expected)


class TestCorporationRoleFilter(TestCase):
    """
    Tests for the `CorporationRoleFilter` model
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Setup for the test case

        :return:
        :rtype:
        """

        super().setUpClass()

        load_entities()

        cls.character_1001 = create_memberaudit_character(1001)
        cls.user_1 = cls.character_1001.character_ownership.user
        cls.corporation_2001 = EveCorporationInfo.objects.get(corporation_id=2001)
        cls.corporation_2101 = EveCorporationInfo.objects.get(corporation_id=2101)

    def test_should_return_name(self):
        """
        Test that the name is returned

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_role_filter(corporations=[])

        # when/then
        self.assertTrue(my_filter.name)

    def test_should_return_false_when_user_does_not_have_role(self):
        """
        Test that the filter returns False when the user does not have the role

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_role_filter(corporations=[self.corporation_2001])

        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_true_when_user_has_character_with_role_in_corp(self):
        """
        Test that the filter returns True when the user has the role

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_role_filter(
            corporations=[self.corporation_2001], role=CharacterRole.Role.DIRECTOR
        )
        create_character_role(
            character=self.character_1001, role=CharacterRole.Role.DIRECTOR
        )
        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1))

    def test_should_return_false_when_user_role_is_not_universal(self):
        """
        Test that the filter returns False when the user has the role, but not in the right location

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_role_filter(
            corporations=[self.corporation_2001], role=CharacterRole.Role.DIRECTOR
        )
        create_character_role(
            character=self.character_1001,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.OTHER,
        )
        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_false_when_character_with_role_is_in_wrong_corp(self):
        """
        Test that the filter returns False when the user has the role, but in the wrong corp

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_role_filter(
            corporations=[self.corporation_2101], role=CharacterRole.Role.DIRECTOR
        )
        my_filter.corporations.add(self.corporation_2101)
        create_character_role(
            character=self.character_1001,
            role=CharacterRole.Role.DIRECTOR,
        )
        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_false_character_with_role_owned_by_other_user(self):
        """
        Test that the filter returns False when the user does not own the character with the role

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_role_filter(
            corporations=[self.corporation_2101], role=CharacterRole.Role.DIRECTOR
        )
        character_1002 = create_memberaudit_character(1002)
        character_1002.character_ownership.user
        create_character_role(
            character=character_1002,
            role=CharacterRole.Role.DIRECTOR,
        )
        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_false_when_character_with_role_is_not_main(self):
        """
        Test that the filter returns False when the character with the role is not the main character

        :return:
        :rtype:
        """

        # given filter for mains only
        my_filter = create_corporation_role_filter(
            corporations=[self.corporation_2001],
            role=CharacterRole.Role.DIRECTOR,
            include_alts=False,
        )
        # and character has role, but is not main
        character_1002 = add_memberaudit_character_to_user(self.user_1, 1002)
        create_character_role(
            character=character_1002, role=CharacterRole.Role.DIRECTOR
        )
        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_true_when_character_with_role_is_not_main_but_allowed(self):
        """
        Test that the filter returns True when the character with the role is not the main character, but allowed

        :return:
        :rtype:
        """

        # given filter for mains only
        my_filter = create_corporation_role_filter(
            corporations=[self.corporation_2001],
            role=CharacterRole.Role.DIRECTOR,
            include_alts=True,
        )
        # and character has role, but is not main
        character_1002 = add_memberaudit_character_to_user(self.user_1, 1002)
        create_character_role(
            character=character_1002, role=CharacterRole.Role.DIRECTOR
        )
        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1))

    def test_should_return_audit_data_for_three_users_and_no_alts(self):
        """
        Test that the audit filter returns the correct data for three users without alts

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_role_filter(
            corporations=[self.corporation_2001, self.corporation_2101],
            role=CharacterRole.Role.DIRECTOR,
            include_alts=False,
        )
        create_character_role(
            character=self.character_1001, role=CharacterRole.Role.DIRECTOR
        )

        character_1101 = create_memberaudit_character(1101)
        user_2 = character_1101.character_ownership.user
        character_1102 = add_memberaudit_character_to_user(user_2, 1102)
        create_character_role(
            character=character_1102, role=CharacterRole.Role.DIRECTOR
        )

        user_3, _ = create_user_from_evecharacter_with_access(1003)

        # when
        users = make_user_queryset(self.user_1, user_2, user_3)
        result = my_filter.audit_filter(users)

        # then
        self.assertEqual(len(result), 3)
        self.assertTrue(result[self.user_1.pk]["check"])
        self.assertFalse(result[user_2.pk]["check"])
        self.assertFalse(result[user_3.pk]["check"])

    def test_should_return_audit_data_for_two_users_with_alts(self):
        """
        Test that the audit filter returns the correct data for two users with alts

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_role_filter(
            corporations=[self.corporation_2001, self.corporation_2101],
            role=CharacterRole.Role.DIRECTOR,
            include_alts=True,
        )
        create_character_role(
            character=self.character_1001, role=CharacterRole.Role.DIRECTOR
        )
        character_1002 = add_memberaudit_character_to_user(self.user_1, 1002)
        create_character_role(
            character=character_1002, role=CharacterRole.Role.DIRECTOR
        )

        character_1101 = create_memberaudit_character(1101)
        user_2 = character_1101.character_ownership.user
        create_character_role(
            character=character_1101, role=CharacterRole.Role.DIRECTOR
        )

        user_3, _ = create_user_from_evecharacter_with_access(1102)

        # when
        users = make_user_queryset(self.user_1, user_2, user_3)
        result = my_filter.audit_filter(users)

        # then
        self.assertEqual(len(result), 3)
        self.assertDictEqual(
            result[self.user_1.id],
            {"message": "Bruce Wayne, Clark Kent", "check": True},
        )
        self.assertDictEqual(
            result[user_2.id], {"message": "Lex Luther", "check": True}
        )
        self.assertDictEqual(
            result[user_3.id],
            {"message": "No matching character found", "check": False},
        )


class TestCorporationTitleFilter(TestCase):
    """
    Tests for the `CorporationTitleFilter` model
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Setup for the test case

        :return:
        :rtype:
        """

        super().setUpClass()

        load_entities()

        cls.character_1001 = create_memberaudit_character(1001)
        cls.user_1 = cls.character_1001.character_ownership.user
        cls.corporation_2001 = EveCorporationInfo.objects.get(corporation_id=2001)
        cls.corporation_2101 = EveCorporationInfo.objects.get(corporation_id=2101)

    def test_should_return_name(self):
        """
        Test that the name is returned

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_title_filter(corporations=[])

        # when/then
        self.assertTrue(my_filter.name)

    def test_should_return_false_when_user_does_not_have_title(self):
        """
        Test that the filter returns False when the user does not have the title

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_title_filter(corporations=[])

        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_true_when_user_has_character_with_title_in_corp(self):
        """
        Test that the filter returns True when the user has a character with the title in corp

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_title_filter(
            corporations=[self.corporation_2001], title="Alpha"
        )
        create_character_title(character=self.character_1001, name="Alpha")

        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1))

    def test_should_not_return_true_when_user_has_character_with_title_but_corp_not_defined(
        self,
    ):
        """
        Test that the filter returns True when the user has a character with the title but no corp is defined

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_title_filter(corporations=[], title="Alpha")
        create_character_title(character=self.character_1001, name="Alpha")

        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_false_when_character_with_title_is_in_wrong_corp(self):
        """
        Test that the filter returns False when the character with the title is in the wrong corp

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_title_filter(
            corporations=[self.corporation_2101], title="Alpha"
        )
        create_character_title(character=self.character_1001, name="Alpha")

        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_false_character_with_title_is_owned_by_other_user(self):
        """
        Test that the filter returns False when the character with the title is owned by another user

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_title_filter(
            corporations=[self.corporation_2001], title="Alpha"
        )
        character_1002 = create_memberaudit_character(1002)
        character_1002.character_ownership.user
        create_character_title(character=character_1002, name="Alpha")

        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_false_when_character_with_title_is_not_main(self):
        """
        Test that the filter returns False when the character with the title is not the main character

        :return:
        :rtype:
        """

        # given filter for mains only
        my_filter = create_corporation_title_filter(
            corporations=[self.corporation_2001], title="Alpha", include_alts=False
        )
        # and owned character has title, but is not main
        character_1002 = add_memberaudit_character_to_user(self.user_1, 1002)
        create_character_title(character=character_1002, name="Alpha")

        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_true_when_character_with_title_is_not_main_but_allowed(self):
        """
        Test that the filter returns True when the character with the title is not the main character, but allowed

        :return:
        :rtype:
        """

        # given filter for mains only
        my_filter = create_corporation_title_filter(
            corporations=[self.corporation_2001], title="Alpha", include_alts=True
        )

        # and character has title, but is not main
        character_1002 = add_memberaudit_character_to_user(self.user_1, 1002)
        create_character_title(character=character_1002, name="Alpha")

        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1))

    def test_should_return_audit_data_for_users_and_mains_only(self):
        """
        Test that the audit filter returns the correct data for two users with mains only

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_title_filter(
            corporations=[self.corporation_2001, self.corporation_2101],
            title="Alpha",
            include_alts=False,
        )
        create_character_title(character=self.character_1001, name="Alpha")
        character_1002 = add_memberaudit_character_to_user(self.user_1, 1002)
        create_character_title(character=character_1002, name="Alpha")

        character_1101 = create_memberaudit_character(1101)
        user_2 = character_1101.character_ownership.user
        character_1102 = add_memberaudit_character_to_user(user_2, 1102)
        create_character_title(character=character_1102, name="Alpha")

        user_3, _ = create_user_from_evecharacter_with_access(1104)

        # when
        users = make_user_queryset(self.user_1, user_2, user_3)
        result = my_filter.audit_filter(users)

        # then
        self.assertEqual(len(result), 3)
        self.assertDictEqual(
            result[self.user_1.id], {"message": "Bruce Wayne", "check": True}
        )
        self.assertFalse(result[user_2.id]["check"])
        self.assertFalse(result[user_3.id]["check"])

    def test_should_return_audit_data_for_three_users_and_including_alts(self):
        """
        Test that the audit filter returns the correct data for three users with alts

        :return:
        :rtype:
        """

        # given
        my_filter = create_corporation_title_filter(
            corporations=[self.corporation_2001, self.corporation_2101],
            title="Alpha",
            include_alts=True,
        )
        character_1002 = add_memberaudit_character_to_user(self.user_1, 1002)
        create_character_title(character=character_1002, name="Alpha")

        character_1101 = create_memberaudit_character(1101)
        user_2 = character_1101.character_ownership.user
        create_character_title(character=character_1101, name="Alpha")

        user_3, _ = create_user_from_evecharacter_with_access(1104)

        # when
        users = make_user_queryset(self.user_1, user_2, user_3)
        result = my_filter.audit_filter(users)

        # then
        self.assertEqual(len(result), 3)
        self.assertTrue(result[self.user_1.id]["check"])
        self.assertTrue(result[user_2.id]["check"])
        self.assertFalse(result[user_3.id]["check"])


class TestSkillSetFilterBase(TestCase):
    """
    Base class for the `SkillSetFilter` tests
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Setup for the test case

        :return:
        :rtype:
        """

        super().setUpClass()

        load_entities()
        load_eveuniverse()

        # user with a main and an alt
        cls.character_1001 = create_memberaudit_character(1001)
        cls.user_1 = cls.character_1001.character_ownership.user
        cls.character_1002 = add_memberaudit_character_to_user(cls.user_1, 1002)
        # amarr carrier skill set
        cls.amarr_carrier_skill_type = EveType.objects.get(name="Amarr Carrier")
        cls.amarr_carrier_skill_set = create_skill_set()
        cls.amarr_carrier_skill_set_skill = create_skill_set_skill(
            skill_set=cls.amarr_carrier_skill_set,
            eve_type=cls.amarr_carrier_skill_type,
            required_level=3,
            recommended_level=5,
        )
        # caldari carrier skill set
        cls.caldari_carrier_skill_type = EveType.objects.get(name="Caldari Carrier")
        cls.caldari_carrier_skill_set = create_skill_set()
        cls.caldari_carrier_skill_set_skill = create_skill_set_skill(
            skill_set=cls.caldari_carrier_skill_set,
            eve_type=cls.caldari_carrier_skill_type,
            required_level=3,
            recommended_level=5,
        )


class TestSkillSetFilterProcessFilter(TestSkillSetFilterBase):
    """
    Tests for the `SkillSetFilter.process_filter` method
    """

    def test_should_return_name(self):
        """
        Test that the name is returned

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create()

        # when/then
        self.assertTrue(my_filter.name)

    def test_should_return_false_when_user_does_not_have_skill_set_check(self):
        """
        Test that the filter returns False when the user does not have a skill set check

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create()
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_false_when_user_did_not_pass_skill_set_check(self):
        """
        Test that the filter returns False when the user did not pass the skill set check

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create()
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        skill_set_check = create_character_skill_set_check(
            character=self.character_1001, skill_set=self.amarr_carrier_skill_set
        )
        skill_set_check.failed_required_skills.add(self.amarr_carrier_skill_set_skill)
        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_true_when_user_passes_skill_set(self):
        """
        Test that the filter returns True when the user passes the skill set check

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create()
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            character=self.character_1001, skill_set=self.amarr_carrier_skill_set
        )
        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1))

    def test_should_return_true_when_user_passes_skill_set_except_recommended_skills(
        self,
    ):
        """
        Test that the filter returns True when the user passes the skill set check except for recommended skills

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create()
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        skill_set_check = create_character_skill_set_check(
            character=self.character_1001, skill_set=self.amarr_carrier_skill_set
        )
        skill_set_check.failed_recommended_skills.add(
            self.amarr_carrier_skill_set_skill
        )
        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1))

    def test_should_return_false_when_character_is_main_but_alt_required(self):
        """
        Test that the filter returns False when the character is main but alt is required

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.ALTS_ONLY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            character=self.character_1001, skill_set=self.amarr_carrier_skill_set
        )
        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_false_when_character_is_main_and_main_required(self):
        """
        Test that the filter returns False when the character is main but main is required

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.MAINS_ONLY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            character=self.character_1001, skill_set=self.amarr_carrier_skill_set
        )
        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1))

    def test_should_return_true_when_character_is_main_and_any_allowed(self):
        """
        Test that the filter returns True when the character is main and any is allowed

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.ANY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            character=self.character_1001, skill_set=self.amarr_carrier_skill_set
        )
        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1))

    def test_should_return_false_when_character_is_alt_but_main_required(self):
        """
        Test that the filter returns False when the character is alt but main is required

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.MAINS_ONLY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            self.character_1002, skill_set=self.amarr_carrier_skill_set
        )
        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1))

    def test_should_return_true_when_character_is_alt_and_any_allowed(self):
        """
        Test that the filter returns True when the character is alt and any is allowed

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.ANY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            self.character_1002, skill_set=self.amarr_carrier_skill_set
        )
        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1))

    def test_should_return_true_when_character_is_alt_and_alt_required(self):
        """
        Test that the filter returns True when the character is alt and alt is required

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.ALTS_ONLY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            self.character_1002, skill_set=self.amarr_carrier_skill_set
        )
        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1))


class TestSkillSetFilterAuditFilter(TestSkillSetFilterBase):
    """
    Tests for the `SkillSetFilter.audit_filter` method
    """

    def test_should_return_audit_data_with_several_users(self):
        """
        Test that the audit filter returns the correct data for several users

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create()
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            character=self.character_1001, skill_set=self.amarr_carrier_skill_set
        )
        create_character_skill_set_check(
            character=self.character_1002, skill_set=self.amarr_carrier_skill_set
        )

        character_1101 = create_memberaudit_character(1101)
        user_2 = character_1101.character_ownership.user
        create_character_skill_set_check(
            character=character_1101, skill_set=self.amarr_carrier_skill_set
        )

        user_3, _ = create_user_from_evecharacter_with_access(1102)

        # when
        users = make_user_queryset(self.user_1, user_2, user_3)
        result = my_filter.audit_filter(users)

        # then
        self.assertEqual(len(result), 3)
        self.assertTrue(result[self.user_1.id]["check"])
        self.assertTrue(result[user_2.id]["check"])
        self.assertFalse(result[user_3.id]["check"])

    def test_should_return_audit_data_when_character_is_main_but_alt_required(self):
        """
        Test that the audit filter returns the correct data when the character is main but alt is required

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.ALTS_ONLY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            character=self.character_1001, skill_set=self.amarr_carrier_skill_set
        )

        # when
        users = make_user_queryset(self.user_1)
        result = my_filter.audit_filter(users)

        # then
        self.assertEqual(len(result), 1)
        self.assertFalse(result[self.user_1.id]["check"])

    def test_should_return_audit_data_when_character_is_main_and_main_required(self):
        """
        Test that the audit filter returns the correct data when the character is main and main is required

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.MAINS_ONLY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            character=self.character_1001, skill_set=self.amarr_carrier_skill_set
        )

        # when
        users = make_user_queryset(self.user_1)
        result = my_filter.audit_filter(users)

        # then
        expected = {self.user_1.id: {"check": True, "message": "Bruce Wayne"}}
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_when_character_is_main_and_any_allowed(self):
        """
        Test that the audit filter returns the correct data when the character is main and any is allowed

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.ANY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            character=self.character_1001, skill_set=self.amarr_carrier_skill_set
        )
        # when
        users = make_user_queryset(self.user_1)
        result = my_filter.audit_filter(users)

        # then
        expected = {self.user_1.id: {"check": True, "message": "Bruce Wayne"}}
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_when_character_is_alt_but_main_required(self):
        """
        Test that the audit filter returns the correct data when the character is alt but main is required

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.MAINS_ONLY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            self.character_1002, skill_set=self.amarr_carrier_skill_set
        )
        # when
        users = make_user_queryset(self.user_1)
        result = my_filter.audit_filter(users)

        # then
        self.assertEqual(len(result), 1)
        self.assertFalse(result[self.user_1.id]["check"])

    def test_should_return_audit_data_when_character_is_alt_and_any_allowed(self):
        """
        Test that the audit filter returns the correct data when the character is alt and any is allowed

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.ANY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            self.character_1002, skill_set=self.amarr_carrier_skill_set
        )

        # when
        users = make_user_queryset(self.user_1)
        result = my_filter.audit_filter(users)

        # then
        expected = {self.user_1.id: {"check": True, "message": "Clark Kent"}}
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_when_character_is_alt_and_alt_required(self):
        """
        Test that the audit filter returns the correct data when the character is alt and alt is required

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.ANY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            self.character_1002, skill_set=self.amarr_carrier_skill_set
        )

        # when
        users = make_user_queryset(self.user_1)
        result = my_filter.audit_filter(users)

        # then
        expected = {self.user_1.id: {"check": True, "message": "Clark Kent"}}
        self.assertDictEqual(result, expected)

    def test_should_default_to_any_as_character_type(self):
        """
        Test that the filter defaults to ANY as the character type

        :return:
        :rtype:
        """

        # given
        my_filter = SkillSetFilter.objects.create(character_type="")
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            self.character_1002, skill_set=self.amarr_carrier_skill_set
        )

        self.assertEqual(my_filter.character_type, SkillSetFilter.CharacterType.ANY)


class TestTimeInCorporationFilter(TestCase):
    """
    Tests for the `TimeInCorporationFilter` model
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Set up the test case with some initial data.

        :return:
        :rtype:
        """

        super().setUpClass()
        load_entities()

        cls.character = create_memberaudit_character(1002)
        cls.user_1002 = cls.character.character_ownership.user
        cls.corporation_2001 = EveEntity.objects.get(id=2001)
        cls.corporation_2002 = EveEntity.objects.get(id=2002)

    def test_should_return_name(self):
        """
        Test that the filter has a name.

        :return:
        :rtype:
        """

        # given
        my_filter = create_time_in_corporation_filter()

        # when/then
        self.assertTrue(my_filter.name)

    def test_should_return_true_when_main_membership_was_long_enough(self):
        """
        Test that the filter returns True when the main character has been in the corporation longer than the defined minimum days.

        :return:
        :rtype:
        """

        # given
        create_character_corporation_history(
            character=self.character,
            corporation=self.corporation_2001,
            start_date=now() - dt.timedelta(days=30),
        )
        my_filter = create_time_in_corporation_filter(minimum_days=30)

        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1002))

    def test_should_return_false_when_main_membership_was_not_long_enough(self):
        """
        Test that the filter returns False when the main character has been in the corporation shorter than the defined minimum days.

        :return:
        :rtype:
        """

        # given
        create_character_corporation_history(
            character=self.character,
            corporation=self.corporation_2001,
            start_date=now() - dt.timedelta(days=29),
        )
        my_filter = create_time_in_corporation_filter(minimum_days=30)

        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1002))

    def test_should_return_false_when_main_membership_was_longer_than_defined(self):
        """
        Test that the filter returns False when the main character has been in the corporation longer than the defined minimum days.

        :return:
        :rtype:
        """

        # given
        create_character_corporation_history(
            character=self.character,
            corporation=self.corporation_2001,
            start_date=now() - dt.timedelta(days=30),
        )
        my_filter = create_time_in_corporation_filter(
            minimum_days=30, reversed_logic=True
        )

        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1002))

    def test_should_return_true_when_main_membership_was_not_long_enough(self):
        """
        Test that the filter returns True when the main character has been in the corporation shorter than the defined minimum days.

        :return:
        :rtype:
        """

        # given
        create_character_corporation_history(
            character=self.character,
            corporation=self.corporation_2001,
            start_date=now() - dt.timedelta(days=29),
        )
        my_filter = create_time_in_corporation_filter(
            minimum_days=30, reversed_logic=True
        )

        # when/then
        self.assertTrue(my_filter.process_filter(self.user_1002))

    def test_should_return_false_when_no_membership_data_for_main(self):
        """
        Test that the filter returns False when there is no membership data for the main character.

        :return:
        :rtype:
        """

        # given
        my_filter = create_time_in_corporation_filter(minimum_days=30)

        # when/then
        self.assertFalse(my_filter.process_filter(self.user_1002))

    def test_should_return_false_when_user_has_no_memberaudit_character(self):
        """
        Test that the filter returns False when the user has no memberaudit character.

        :return:
        :rtype:
        """

        # given
        my_filter = create_time_in_corporation_filter(minimum_days=30)
        user, _ = create_user_from_evecharacter_with_access(1002)

        # when/then
        self.assertFalse(my_filter.process_filter(user))

    def test_should_return_audit_data_with_one_user_passing_and_one_not_passing(self):
        """
        Test that the filter returns the correct audit data for two users.

        :return:
        :rtype:
        """

        # given
        my_filter = create_time_in_corporation_filter(minimum_days=30)
        create_character_corporation_history(
            character=self.character,
            corporation=self.corporation_2001,
            start_date=now() - dt.timedelta(days=30),
        )
        character_1101 = create_memberaudit_character(1101)
        user_1101 = character_1101.user
        create_character_corporation_history(
            record_id=1,
            character=character_1101,
            corporation=self.corporation_2002,
            start_date=now() - dt.timedelta(days=100),
        )
        create_character_corporation_history(
            record_id=2,
            character=character_1101,
            corporation=self.corporation_2001,
            start_date=now() - dt.timedelta(days=29),
        )
        users = User.objects.filter(pk__in=[self.user_1002.pk, user_1101.pk])

        # when
        result = my_filter.audit_filter(users)

        # then
        expected = {
            self.user_1002.id: {"message": "30 days", "check": True},
            user_1101.id: {"message": "29 days", "check": False},
        }
        self.assertDictEqual(dict(result), expected)
