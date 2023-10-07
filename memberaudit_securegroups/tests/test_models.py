from memberaudit.models import CharacterAsset
from memberaudit.tests.testdata.load_entities import load_entities
from memberaudit.tests.testdata.load_eveuniverse import load_eveuniverse
from memberaudit.tests.utils import create_memberaudit_character
from memberaudit_securegroups.models import AssetFilter

from django.test import TestCase
from eveuniverse.models import EveType


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
        my_filter = AssetFilter.objects.create(description="dummy")
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
        my_filter = AssetFilter.objects.create(description="dummy")
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
        my_filter = AssetFilter.objects.create(description="dummy")
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
        # given
        my_filter = AssetFilter.objects.create(description="dummy")
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
        character_1002 = create_memberaudit_character(1002)
        user_1002 = character_1002.character_ownership.user
        CharacterAsset.objects.create(
            item_id=2,
            character=character_1002,
            eve_type=merlin_type,
            quantity=1,
            location_flag="dummy",
            is_singleton=False,
        )
        # when
        result = my_filter.audit_filter([self.user, user_1002])
        # then
        expected = {
            self.user.id: {"message": self.character.name, "check": True},
            user_1002.id: {"message": character_1002.name, "check": True},
        }
        self.assertEqual(dict(result), expected)

    def test_should_return_audit_data_when_no_matches(self):
        # given
        my_filter = AssetFilter.objects.create(description="dummy")
        # when
        result = my_filter.audit_filter([self.user])
        # then
        self.assertEqual(result, {})
