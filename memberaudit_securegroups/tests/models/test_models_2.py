import datetime as dt

from django.contrib.auth.models import User
from django.utils.timezone import now
from eveuniverse.tests.testdata.factories_2 import EveEntityCorporationFactory

from app_utils.testdata_factories import EveCharacterFactory, EveCorporationInfoFactory
from app_utils.testing import NoSocketsTestCase
from memberaudit.tests.testdata.factories_2 import (
    CharacterCorporationHistoryFactory,
    CharacterFactory,
    CharacterSkillSetCheckFactory,
    NavigationSkillTypeFactory,
    SkillSetFactory,
    SkillSetSkillFactory,
    UserMainBasicAccessFactory,
)

from memberaudit_securegroups.models import SkillSetFilter
from memberaudit_securegroups.tests.factories_2 import TimeInCorporationFilterFactory
from memberaudit_securegroups.tests.helpers import make_user_queryset


class TestSkillSetFilterBase(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        # user with a main and an alt
        main = EveCharacterFactory(character_name="Bruce Wayne")
        cls.user = UserMainBasicAccessFactory(main_character__character=main)
        cls.character_11 = CharacterFactory(user=cls.user)
        alt = EveCharacterFactory(character_name="Clark Kent")
        cls.character_12 = CharacterFactory(
            user=cls.user, is_main=False, alt_character=alt
        )
        # amarr carrier skill set
        cls.amarr_carrier_skill_type = NavigationSkillTypeFactory(name="Amarr Carrier")
        cls.amarr_carrier_skill_set = SkillSetFactory()
        cls.amarr_carrier_skill_set_skill = SkillSetSkillFactory(
            skill_set=cls.amarr_carrier_skill_set,
            eve_type=cls.amarr_carrier_skill_type,
            required_level=3,
            recommended_level=5,
        )
        # caldari carrier skill set
        cls.caldari_carrier_skill_type = NavigationSkillTypeFactory(
            name="Caldari Carrier"
        )
        cls.caldari_carrier_skill_set = SkillSetFactory()


class TestSkillSetFilter_ProcessFilter(TestSkillSetFilterBase):
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
        skill_set_check = CharacterSkillSetCheckFactory(
            character=self.character_11, skill_set=self.amarr_carrier_skill_set
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
        CharacterSkillSetCheckFactory(
            character=self.character_11, skill_set=self.amarr_carrier_skill_set
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
        skill_set_check = CharacterSkillSetCheckFactory(
            character=self.character_11, skill_set=self.amarr_carrier_skill_set
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
        CharacterSkillSetCheckFactory(
            character=self.character_11, skill_set=self.amarr_carrier_skill_set
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
        CharacterSkillSetCheckFactory(
            character=self.character_11, skill_set=self.amarr_carrier_skill_set
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
        CharacterSkillSetCheckFactory(
            character=self.character_11, skill_set=self.amarr_carrier_skill_set
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
        CharacterSkillSetCheckFactory(
            character=self.character_12, skill_set=self.amarr_carrier_skill_set
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
        CharacterSkillSetCheckFactory(
            character=self.character_12, skill_set=self.amarr_carrier_skill_set
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
        CharacterSkillSetCheckFactory(
            character=self.character_12, skill_set=self.amarr_carrier_skill_set
        )
        # when/then
        self.assertTrue(my_filter.process_filter(self.user))


class TestSkillSetFilter_AuditFilter(TestSkillSetFilterBase):
    def test_should_return_audit_data_with_several_users(self):
        # given
        my_filter = SkillSetFilter.objects.create()
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        CharacterSkillSetCheckFactory(
            character=self.character_11, skill_set=self.amarr_carrier_skill_set
        )
        CharacterSkillSetCheckFactory(
            character=self.character_12, skill_set=self.amarr_carrier_skill_set
        )

        user_2 = UserMainBasicAccessFactory()
        character_3 = CharacterFactory(user=user_2)

        CharacterSkillSetCheckFactory(
            character=character_3, skill_set=self.amarr_carrier_skill_set
        )

        user_3 = UserMainBasicAccessFactory()

        # when
        users = make_user_queryset(self.user, user_2, user_3)
        result = my_filter.audit_filter(users)

        # then
        self.assertEqual(len(result), 3)
        self.assertTrue(result[self.user.id]["check"])
        self.assertTrue(result[user_2.id]["check"])
        self.assertFalse(result[user_3.id]["check"])

    def test_should_return_audit_data_when_character_is_main_but_alt_required(self):
        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.ALTS_ONLY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        CharacterSkillSetCheckFactory(
            character=self.character_11, skill_set=self.amarr_carrier_skill_set
        )

        # when
        users = make_user_queryset(self.user)
        result = my_filter.audit_filter(users)

        # then
        self.assertEqual(len(result), 1)
        self.assertFalse(result[self.user.id]["check"])

    def test_should_return_audit_data_when_character_is_main_and_main_required(self):
        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.MAINS_ONLY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        CharacterSkillSetCheckFactory(
            character=self.character_11, skill_set=self.amarr_carrier_skill_set
        )

        # when
        users = make_user_queryset(self.user)
        result = my_filter.audit_filter(users)

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
        CharacterSkillSetCheckFactory(
            character=self.character_11, skill_set=self.amarr_carrier_skill_set
        )
        # when
        users = make_user_queryset(self.user)
        result = my_filter.audit_filter(users)

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
        CharacterSkillSetCheckFactory(
            character=self.character_12, skill_set=self.amarr_carrier_skill_set
        )
        # when
        users = make_user_queryset(self.user)
        result = my_filter.audit_filter(users)

        # then
        self.assertEqual(len(result), 1)
        self.assertFalse(result[self.user.id]["check"])

    def test_should_return_audit_data_when_character_is_alt_and_any_allowed(self):
        # given
        my_filter = SkillSetFilter.objects.create(
            character_type=SkillSetFilter.CharacterType.ANY
        )
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        CharacterSkillSetCheckFactory(
            character=self.character_12, skill_set=self.amarr_carrier_skill_set
        )

        # when
        users = make_user_queryset(self.user)
        result = my_filter.audit_filter(users)

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
        CharacterSkillSetCheckFactory(
            character=self.character_12, skill_set=self.amarr_carrier_skill_set
        )

        # when
        users = make_user_queryset(self.user)
        result = my_filter.audit_filter(users)

        # then
        expected = {self.user.id: {"check": True, "message": "Clark Kent"}}
        self.assertDictEqual(result, expected)

    def test_should_default_to_any_as_character_type(self):
        # given
        my_filter = SkillSetFilter.objects.create(character_type="")
        my_filter.skill_sets.add(
            self.amarr_carrier_skill_set, self.caldari_carrier_skill_set
        )
        CharacterSkillSetCheckFactory(
            character=self.character_12, skill_set=self.amarr_carrier_skill_set
        )

        self.assertEqual(my_filter.character_type, SkillSetFilter.CharacterType.ANY)


class TestTimeInCorporationFilter_AuditFilter(NoSocketsTestCase):
    def test_should_return_audit_data_with_one_user_passing_and_one_not_passing(self):
        # given
        my_filter = TimeInCorporationFilterFactory(minimum_days=30)
        eve_corporation = EveCorporationInfoFactory()
        user_1 = UserMainBasicAccessFactory(
            main_character__character=EveCharacterFactory(corporation=eve_corporation)
        )
        character_1 = CharacterFactory(user=user_1)
        corporation = EveEntityCorporationFactory(id=eve_corporation.corporation_id)

        CharacterCorporationHistoryFactory(
            character=character_1,
            corporation=corporation,
            start_date=now() - dt.timedelta(days=30),
        )

        user_2 = UserMainBasicAccessFactory()
        character_2 = CharacterFactory(user=user_2)

        CharacterCorporationHistoryFactory(
            record_id=1,
            character=character_2,
            start_date=now() - dt.timedelta(days=100),
        )
        CharacterCorporationHistoryFactory(
            record_id=2,
            character=character_2,
            corporation=corporation,
            start_date=now() - dt.timedelta(days=29),
        )
        users = User.objects.filter(pk__in=[user_1.pk, user_2.pk])

        # when
        result = my_filter.audit_filter(users)

        # then
        expected = {
            user_1.id: {"message": "30 days", "check": True},
            user_2.id: {"message": "29 days", "check": False},
        }
        self.assertDictEqual(dict(result), expected)


class TestTimeInCorporationFilter_ProcessFilter(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        corporation = EveCorporationInfoFactory()
        cls.user = UserMainBasicAccessFactory(
            main_character__character=EveCharacterFactory(corporation=corporation)
        )
        cls.character = CharacterFactory(user=cls.user)
        cls.corporation = EveEntityCorporationFactory(id=corporation.corporation_id)

    def test_should_return_name(self):
        # given
        my_filter = TimeInCorporationFilterFactory()

        # when/then
        self.assertTrue(my_filter.name)

    def test_should_return_true_when_main_membership_was_long_enough(self):
        # given
        CharacterCorporationHistoryFactory(
            character=self.character,
            corporation=self.corporation,
            start_date=now() - dt.timedelta(days=30),
        )
        my_filter = TimeInCorporationFilterFactory(minimum_days=30)

        # when/then
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_false_when_main_membership_was_not_long_enough(self):
        # given
        CharacterCorporationHistoryFactory(
            character=self.character,
            corporation=self.corporation,
            start_date=now() - dt.timedelta(days=29),
        )
        my_filter = TimeInCorporationFilterFactory(minimum_days=30)

        # when/then
        self.assertFalse(my_filter.process_filter(self.user))

    def test_should_return_false_when_main_membership_was_longer_than_defined(self):
        # given
        CharacterCorporationHistoryFactory(
            character=self.character,
            corporation=self.corporation,
            start_date=now() - dt.timedelta(days=30),
        )
        my_filter = TimeInCorporationFilterFactory(minimum_days=30, reversed_logic=True)

        # when/then
        self.assertFalse(my_filter.process_filter(self.user))

    def test_should_return_true_when_main_membership_was_not_long_enough(self):
        # given
        CharacterCorporationHistoryFactory(
            character=self.character,
            corporation=self.corporation,
            start_date=now() - dt.timedelta(days=29),
        )
        my_filter = TimeInCorporationFilterFactory(minimum_days=30, reversed_logic=True)

        # when/then
        self.assertTrue(my_filter.process_filter(self.user))

    def test_should_return_false_when_no_membership_data_for_main(self):
        # given
        my_filter = TimeInCorporationFilterFactory(minimum_days=30)

        # when/then
        self.assertFalse(my_filter.process_filter(self.user))

    def test_should_return_false_when_user_has_no_memberaudit_character(self):
        # given
        my_filter = TimeInCorporationFilterFactory(minimum_days=30)
        user = UserMainBasicAccessFactory()

        # when/then
        self.assertFalse(my_filter.process_filter(user))
