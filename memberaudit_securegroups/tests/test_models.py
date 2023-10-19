# Django
# Django
from django.test import TestCase

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo

# Member Audit
from memberaudit.app_settings import MEMBERAUDIT_APP_NAME
from memberaudit.models import CharacterRole
from memberaudit.tests.testdata.factories import (
    create_character_asset,
    create_character_role,
    create_character_skill_set_check,
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
from eveuniverse.models import EveType

# Memberaudit Securegroups
from memberaudit_securegroups.models import (
    AssetFilter,
    ComplianceFilter,
    CorporationRoleFilter,
    SkillSetFilter,
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
        my_filter = AssetFilter.objects.create()
        # when/then
        self.assertTrue(my_filter.name)

    def test_should_return_false_when_user_does_not_have_asset(self):
        # given
        my_filter = AssetFilter.objects.create()
        merlin_type = EveType.objects.get(name="Merlin")
        my_filter.assets.add(merlin_type)
        astrahus_type = EveType.objects.get(name="Astrahus")
        create_character_asset(character=self.character, eve_type=astrahus_type)
        # when/then
        self.assertFalse(my_filter.process_filter(self.user))

    def test_should_return_true_when_user_has_asset(self):
        # given
        my_filter = AssetFilter.objects.create()
        merlin_type = EveType.objects.get(name="Merlin")
        my_filter.assets.add(merlin_type)
        create_character_asset(character=self.character, eve_type=merlin_type)
        # when/then
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_true_when_user_has_at_least_one_asset(self):
        # given
        my_filter = AssetFilter.objects.create()
        merlin_type = EveType.objects.get(name="Merlin")
        astrahus_type = EveType.objects.get(name="Astrahus")
        my_filter.assets.add(merlin_type, astrahus_type)
        create_character_asset(character=self.character, eve_type=merlin_type)
        # when/then
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_audit_data_for_two_users(self):
        # given a filter for Merlins
        my_filter = AssetFilter.objects.create()
        merlin_type = EveType.objects.get(name="Merlin")
        my_filter.assets.add(merlin_type)
        # and main user's character has a Merlin
        create_character_asset(character=self.character, eve_type=merlin_type)
        # and main user's 2nd character also has a Merlin
        character_1002 = add_memberaudit_character_to_user(self.user, 1002)
        create_character_asset(character=character_1002, eve_type=merlin_type)
        # and a 2nd user has a character with a Merlin
        character_1003 = create_memberaudit_character(1003)
        user_1002 = character_1003.character_ownership.user
        create_character_asset(character=character_1003, eve_type=merlin_type)
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


class TestComplianceFilter(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_entities()
        cls.user, _ = create_user_from_evecharacter_with_access(1001)

    def test_should_return_name(self):
        # given
        my_filter = ComplianceFilter.objects.create()
        # when/then
        self.assertTrue(my_filter.name)

    def test_should_return_true_when_user_is_compliant_1(self):
        # given a user with 1 registered character
        add_memberaudit_character_to_user(self.user, 1001)
        my_filter = ComplianceFilter.objects.create()
        # when/then
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_true_when_user_is_compliant_2(self):
        # given a user with 2 registered character
        add_memberaudit_character_to_user(self.user, 1001)
        add_memberaudit_character_to_user(self.user, 1002)
        my_filter = ComplianceFilter.objects.create()
        # when/then
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_false_when_user_is_not_compliant_1(self):
        # given a user with 1 unregistered character
        my_filter = ComplianceFilter.objects.create()
        # when/then
        self.assertFalse(my_filter.process_filter(self.user))

    def test_should_return_false_when_user_is_not_compliant_2(self):
        # given a user with 1 registered and 1 unregistered character
        add_memberaudit_character_to_user(self.user, 1001)
        add_auth_character_to_user(self.user, 1002)
        my_filter = ComplianceFilter.objects.create()
        # when/then
        self.assertFalse(my_filter.process_filter(self.user))

    def test_should_return_audit_data_for_compliant_user(self):
        # given
        add_memberaudit_character_to_user(self.user, 1001)
        my_filter = ComplianceFilter.objects.create()
        # when
        result = my_filter.audit_filter([self.user])
        # then
        expected = {
            self.user.pk: {
                "check": True,
                "message": f"All characters have been added to {MEMBERAUDIT_APP_NAME}",
            }
        }
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_for_non_compliant_user_with_1_character(self):
        # given
        my_filter = ComplianceFilter.objects.create()
        # when
        result = my_filter.audit_filter([self.user])
        # then
        expected = {
            self.user.pk: {"check": False, "message": "Missing character: Bruce Wayne"},
        }
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_for_non_compliant_user_with_2_characters(self):
        # given
        add_auth_character_to_user(self.user, 1002)
        my_filter = ComplianceFilter.objects.create()
        # when
        result = my_filter.audit_filter([self.user])
        # then
        expected = {
            self.user.pk: {
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

    def test_should_return_name(self):
        # given
        my_filter = CorporationRoleFilter.objects.create(
            role=CharacterRole.Role.DIRECTOR
        )
        # when/then
        self.assertTrue(my_filter.name)

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


class TestSkillSetFilterBase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_entities()
        load_eveuniverse()
        # user with a main and an alt
        cls.character_1001 = create_memberaudit_character(1001)
        cls.user = cls.character_1001.character_ownership.user
        cls.character_1002 = add_memberaudit_character_to_user(cls.user, 1002)
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
    def test_should_return_name(self):
        # given
        my_filter = SkillSetFilter.objects.create()
        # when/then
        self.assertTrue(my_filter.name)

    def test_should_return_false_when_user_does_not_have_skill_set_check(self):
        # given
        my_filter = SkillSetFilter.objects.create()
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        # when/then
        self.assertFalse(my_filter.process_filter(self.user))

    def test_should_return_false_when_user_did_not_pass_skill_set_check(self):
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
        self.assertFalse(my_filter.process_filter(self.user))

    def test_should_return_true_when_user_passes_skill_set(self):
        # given
        my_filter = SkillSetFilter.objects.create()
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            character=self.character_1001, skill_set=self.amarr_carrier_skill_set
        )
        # when/then
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_true_when_user_passes_skill_set_except_recommended_skills(
        self,
    ):
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
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_false_when_character_is_main_but_alt_required(self):
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
        self.assertFalse(my_filter.process_filter(self.user))

    def test_should_return_false_when_character_is_main_and_main_required(self):
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
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_true_when_character_is_main_and_any_allowed(self):
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
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_false_when_character_is_alt_but_main_required(self):
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
        self.assertFalse(my_filter.process_filter(self.user))

    def test_should_return_true_when_character_is_alt_and_any_allowed(self):
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
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_true_when_character_is_alt_and_alt_required(self):
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
        self.assertTrue(my_filter.process_filter(self.user))


class TestSkillSetFilterAuditFilter(TestSkillSetFilterBase):
    def test_should_return_audit_data_with_two_users(self):
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
        user_1101 = character_1101.character_ownership.user
        create_character_skill_set_check(
            character=character_1101, skill_set=self.amarr_carrier_skill_set
        )
        # when
        result = my_filter.audit_filter([self.user, user_1101])
        # then
        expected = {
            self.user.id: {"check": True, "message": "Bruce Wayne, Clark Kent"},
            user_1101.id: {"check": True, "message": "Lex Luther"},
        }
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_with_no_users(self):
        # given
        my_filter = SkillSetFilter.objects.create()
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        # when
        result = my_filter.audit_filter([self.user])
        # then
        self.assertDictEqual(result, {})

    def test_should_return_audit_data_when_character_is_main_but_alt_required(self):
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
        result = my_filter.audit_filter([self.user])
        # then
        self.assertDictEqual(result, {})

    def test_should_return_audit_data_when_character_is_main_and_main_required(self):
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
        result = my_filter.audit_filter([self.user])
        # then
        expected = {self.user.id: {"check": True, "message": "Bruce Wayne"}}
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_when_character_is_main_and_any_allowed(self):
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
        result = my_filter.audit_filter([self.user])
        # then
        expected = {self.user.id: {"check": True, "message": "Bruce Wayne"}}
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_when_character_is_alt_but_main_required(self):
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
        result = my_filter.audit_filter([self.user])
        # then
        self.assertDictEqual(result, {})

    def test_should_return_audit_data_when_character_is_alt_and_any_allowed(self):
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
        result = my_filter.audit_filter([self.user])
        # then
        expected = {self.user.id: {"check": True, "message": "Clark Kent"}}
        self.assertDictEqual(result, expected)

    def test_should_return_audit_data_when_character_is_alt_and_alt_required(self):
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
        result = my_filter.audit_filter([self.user])
        # then
        expected = {self.user.id: {"check": True, "message": "Clark Kent"}}
        self.assertDictEqual(result, expected)

    def test_should_default_to_any_as_character_type(self):
        # given
        my_filter = SkillSetFilter.objects.create(character_type="")
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        create_character_skill_set_check(
            self.character_1002, skill_set=self.amarr_carrier_skill_set
        )

        self.assertEqual(my_filter.character_type, SkillSetFilter.CharacterType.ANY)
