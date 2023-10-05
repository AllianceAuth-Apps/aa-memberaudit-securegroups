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

    def test_should_return_false_when_asset_not_found(self):
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

    def test_should_return_true_when_asset_is_found(self):
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

    def test_should_return_audit_data_for_one_user_and_character(self):
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
        # when
        result = my_filter.audit_filter([self.user])
        # then
        expected = {self.user.id: {"message": self.character.name, "check": True}}
        self.assertEqual(result, expected)
