# Django
from django.test import TestCase

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo

# Member Audit
from memberaudit.models import CharacterAsset, CharacterRole
from memberaudit.tests.testdata.factories import create_character_role
from memberaudit.tests.testdata.load_entities import load_entities
from memberaudit.tests.testdata.load_eveuniverse import load_eveuniverse
from memberaudit.tests.utils import (
    add_auth_character_to_user,
    add_memberaudit_character_to_user,
    create_memberaudit_character,
    create_user_from_evecharacter_with_access,
)

# Alliance Auth (External Libs)
from eveuniverse.models import EveType

# Memberaudit Securegroups
from memberaudit_securegroups.models import (
    AssetFilter,
    ComplianceFilter,
    CorporationRoleFilter,
)


class TestAssetFilter(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_entities()
        load_eveuniverse()
        cls.character = create_memberaudit_character(1001)
        cls.user = cls.character.character_ownership.user

    def test_should_return_name(self):
        # given
        my_filter = AssetFilter.objects.create(description="dummy")
        # when/then
        self.assertTrue(my_filter.name)

    def test_should_return_false_when_user_does_not_have_asset(self):
        # given
        my_filter = AssetFilter.objects.create()
        merlin_type = EveType.objects.get(name="Merlin")
        my_filter.assets.add(merlin_type)
        astrahus_type = EveType.objects.get(name="Astrahus")
        CharacterAsset.objects.create(
            item_id=1,
            character=self.character,
            eve_type=astrahus_type,
            quantity=1,
            location_flag="dummy",
            is_singleton=False,
        )
        # when/then
        self.assertFalse(my_filter.process_filter(self.user))

    def test_should_return_true_when_user_has_asset(self):
        # given
        my_filter = AssetFilter.objects.create()
        merlin_type = EveType.objects.get(name="Merlin")
        my_filter.assets.add(merlin_type)
        CharacterAsset.objects.create(
            item_id=1,
            character=self.character,
            eve_type=merlin_type,
            quantity=1,
            location_flag="dummy",
            is_singleton=False,
        )
        # when/then
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_true_when_user_has_at_least_one_asset(self):
        # given
        my_filter = AssetFilter.objects.create()
        merlin_type = EveType.objects.get(name="Merlin")
        astrahus_type = EveType.objects.get(name="Astrahus")
        my_filter.assets.add(merlin_type, astrahus_type)
        CharacterAsset.objects.create(
            item_id=1,
            character=self.character,
            eve_type=merlin_type,
            quantity=1,
            location_flag="dummy",
            is_singleton=False,
        )
        # when/then
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_audit_data_for_two_users(self):
        # given a filter for Merlins
        my_filter = AssetFilter.objects.create()
        merlin_type = EveType.objects.get(name="Merlin")
        my_filter.assets.add(merlin_type)
        # and main user's character has a Merlin
        CharacterAsset.objects.create(
            item_id=1,
            character=self.character,
            eve_type=merlin_type,
            quantity=1,
            location_flag="dummy",
            is_singleton=False,
        )
        # and main user's 2nd character also has a Merlin
        character_1002 = add_memberaudit_character_to_user(self.user, 1002)
        CharacterAsset.objects.create(
            item_id=2,
            character=character_1002,
            eve_type=merlin_type,
            quantity=1,
            location_flag="dummy",
            is_singleton=False,
        )
        # and a 2nd user has a character with a Merlin
        character_1003 = create_memberaudit_character(1003)
        user_1002 = character_1003.character_ownership.user
        CharacterAsset.objects.create(
            item_id=2,
            character=character_1003,
            eve_type=merlin_type,
            quantity=1,
            location_flag="dummy",
            is_singleton=False,
        )
        # when
        result = my_filter.audit_filter([self.user, user_1002])
        # then
        expected = {
            self.user.id: {"message": "Bruce Wayne, Clark Kent", "check": True},
            user_1002.id: {"message": "Peter Parker", "check": True},
        }
        self.assertEqual(dict(result), expected)

    def test_should_return_audit_data_when_no_matches(self):
        # given
        my_filter = AssetFilter.objects.create()
        # when
        result = my_filter.audit_filter([self.user])
        # then
        self.assertEqual(result, {})


class TestComplianceFilterProcess(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_entities()

    def test_should_return_true_when_user_is_compliant_1(self):
        # given a user with 1 registered character
        character = create_memberaudit_character(1001)
        user = character.character_ownership.user
        my_filter = ComplianceFilter.objects.create()
        # when/then
        self.assertTrue(my_filter.process_filter(user))

    def test_should_return_true_when_user_is_compliant_2(self):
        # given a user with 2 registered character
        character = create_memberaudit_character(1001)
        user = character.character_ownership.user
        add_memberaudit_character_to_user(user, 1002)
        my_filter = ComplianceFilter.objects.create()
        # when/then
        self.assertTrue(my_filter.process_filter(user))

    def test_should_return_false_when_user_is_not_compliant_1(self):
        # given a user with 1 unregistered character
        user, _ = create_user_from_evecharacter_with_access(1001)
        my_filter = ComplianceFilter.objects.create()
        # when/then
        self.assertFalse(my_filter.process_filter(user))

    def test_should_return_false_when_user_is_not_compliant_2(self):
        # given a user with 1 registered and 1 unregistered character
        character = create_memberaudit_character(1001)
        user = character.character_ownership.user
        add_auth_character_to_user(user, 1002)
        my_filter = ComplianceFilter.objects.create()
        # when/then
        self.assertFalse(my_filter.process_filter(user))


class TestComplianceFilterAssert(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_entities()

    def test_should_return_data_for_compliant_user(self):
        # given
        character = create_memberaudit_character(1001)
        user_1001 = character.character_ownership.user
        my_filter = ComplianceFilter.objects.create()
        # when
        result = my_filter.audit_filter([user_1001])
        # then
        expected = {
            user_1001.pk: {
                "check": True,
                "message": "All characters have been added to Member Audit",
            }
        }
        self.assertDictEqual(result, expected)

    def test_should_return_data_for_non_compliant_user_with_1_character(self):
        # given
        user, _ = create_user_from_evecharacter_with_access(1001)
        my_filter = ComplianceFilter.objects.create()
        # when
        result = my_filter.audit_filter([user])
        # then
        expected = {
            user.pk: {"check": False, "message": "Missing character: Bruce Wayne"},
        }
        self.assertDictEqual(result, expected)

    def test_should_return_data_for_non_compliant_user_with_2_characters(self):
        # given
        user, _ = create_user_from_evecharacter_with_access(1001)
        add_auth_character_to_user(user, 1002)
        my_filter = ComplianceFilter.objects.create()
        # when
        result = my_filter.audit_filter([user])
        # then
        expected = {
            user.pk: {
                "check": False,
                "message": "Missing characters: Bruce Wayne, Clark Kent",
            },
        }
        self.assertDictEqual(result, expected)


class TestCorporationRoleFilter(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_entities()
        cls.character = create_memberaudit_character(1001)
        cls.user = cls.character.character_ownership.user
        cls.corporation_2001 = EveCorporationInfo.objects.get(corporation_id=2001)
        cls.corporation_2101 = EveCorporationInfo.objects.get(corporation_id=2101)

    def test_should_return_false_when_user_does_not_have_role(self):
        # given
        filter = CorporationRoleFilter.objects.create(role=CharacterRole.Role.DIRECTOR)
        filter.corporations.add(self.corporation_2001)
        # when/then
        self.assertFalse(filter.process_filter(self.user))

    def test_should_return_true_when_user_has_character_with_role_in_corp(self):
        # given
        filter = CorporationRoleFilter.objects.create(role=CharacterRole.Role.DIRECTOR)
        filter.corporations.add(self.corporation_2001)
        filter.corporations.add(self.corporation_2101)
        create_character_role(
            character=self.character,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.UNIVERSAL,
        )
        # when/then
        self.assertTrue(filter.process_filter(self.user))

    def test_should_return_false_when_user_role_is_not_universal(self):
        # given
        filter = CorporationRoleFilter.objects.create(role=CharacterRole.Role.DIRECTOR)
        filter.corporations.add(self.corporation_2001)
        create_character_role(
            character=self.character,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.OTHER,
        )
        # when/then
        self.assertFalse(filter.process_filter(self.user))

    def test_should_return_false_when_character_with_role_is_in_wrong_corp(self):
        # given
        filter = CorporationRoleFilter.objects.create(role=CharacterRole.Role.DIRECTOR)
        filter.corporations.add(self.corporation_2101)
        create_character_role(
            character=self.character,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.UNIVERSAL,
        )
        # when/then
        self.assertFalse(filter.process_filter(self.user))

    def test_should_return_false_character_with_role_owned_by_other_user(self):
        # given
        filter = CorporationRoleFilter.objects.create(role=CharacterRole.Role.DIRECTOR)
        filter.corporations.add(self.corporation_2001)
        character_1002 = create_memberaudit_character(1002)
        character_1002.character_ownership.user
        create_character_role(
            character=character_1002,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.UNIVERSAL,
        )
        # when/then
        self.assertFalse(filter.process_filter(self.user))

    def test_should_return_false_when_character_with_role_is_not_main(self):
        # given filter for mains only
        filter = CorporationRoleFilter.objects.create(
            role=CharacterRole.Role.DIRECTOR, include_alts=False
        )
        filter.corporations.add(self.corporation_2001)
        # and character has role, but is not main
        character_1002 = add_memberaudit_character_to_user(self.user, 1002)
        create_character_role(
            character=character_1002,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.UNIVERSAL,
        )
        # when/then
        self.assertFalse(filter.process_filter(self.user))

    def test_should_return_true_when_character_with_role_is_not_main_but_allowed(self):
        # given filter for mains only
        filter = CorporationRoleFilter.objects.create(
            role=CharacterRole.Role.DIRECTOR, include_alts=True
        )
        filter.corporations.add(self.corporation_2001)
        # and character has role, but is not main
        character_1002 = add_memberaudit_character_to_user(self.user, 1002)
        create_character_role(
            character=character_1002,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.UNIVERSAL,
        )
        # when/then
        self.assertTrue(filter.process_filter(self.user))

    def test_should_return_audit_data_for_two_matching_users_but_mains_only(self):
        # given
        filter = CorporationRoleFilter.objects.create(
            role=CharacterRole.Role.DIRECTOR, include_alts=False
        )
        filter.corporations.add(self.corporation_2001)
        filter.corporations.add(self.corporation_2101)
        create_character_role(
            character=self.character,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.UNIVERSAL,
        )
        character_1002 = add_memberaudit_character_to_user(self.user, 1002)
        create_character_role(
            character=character_1002,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.UNIVERSAL,
        )
        character_1101 = create_memberaudit_character(1101)
        user_2 = character_1101.character_ownership.user
        create_character_role(
            character=character_1101,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.UNIVERSAL,
        )
        # when
        result = filter.audit_filter([self.user, user_2])
        # then
        expected = {
            self.user.id: {"message": "Bruce Wayne", "check": True},
            user_2.id: {"message": "Lex Luther", "check": True},
        }
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_for_two_matching_users_no_mains_allowed(self):
        # given
        filter = CorporationRoleFilter.objects.create(
            role=CharacterRole.Role.DIRECTOR, include_alts=True
        )
        filter.corporations.add(self.corporation_2001)
        filter.corporations.add(self.corporation_2101)
        create_character_role(
            character=self.character,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.UNIVERSAL,
        )
        character_1002 = add_memberaudit_character_to_user(self.user, 1002)
        create_character_role(
            character=character_1002,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.UNIVERSAL,
        )
        character_1101 = create_memberaudit_character(1101)
        user_2 = character_1101.character_ownership.user
        create_character_role(
            character=character_1101,
            role=CharacterRole.Role.DIRECTOR,
            location=CharacterRole.Location.UNIVERSAL,
        )
        # when
        result = filter.audit_filter([self.user, user_2])
        # then
        expected = {
            self.user.id: {"message": "Bruce Wayne, Clark Kent", "check": True},
            user_2.id: {"message": "Lex Luther", "check": True},
        }
        self.assertDictEqual(result, expected)
