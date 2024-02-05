# Third Party
from securegroups.models import SmartFilter, SmartGroup
from securegroups.tasks import run_smart_group_update

# Django
from django.contrib.auth.models import Group
from django.test import TestCase

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo

# Member Audit
from memberaudit.tests.testdata.factories import create_character_title
from memberaudit.tests.testdata.load_entities import load_entities
from memberaudit.tests.utils import create_memberaudit_character

from .factories import create_corporation_title_filter


class TestCorporationTitleFilter(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_entities()
        cls.group = Group.objects.create(name="Leadership")
        cls.corporation_2001 = EveCorporationInfo.objects.get(corporation_id=2001)

    def test_should_only_add_user__with_matching_title_to_group(self):
        # given
        character_1001 = create_memberaudit_character(1001)  # in corp 2001
        user_1001 = character_1001.character_ownership.user
        create_character_title(character=character_1001, name="CEO")

        character_1002 = create_memberaudit_character(1002)  # in corp 2001
        user_1002 = character_1002.character_ownership.user
        create_character_title(character=character_1001, name="Diplomat")

        create_corporation_title_filter(
            corporations=[self.corporation_2001], title="CEO"
        )
        smart_group = SmartGroup.objects.create(group=self.group, auto_group=True)
        title_filter = SmartFilter.objects.first()
        smart_group.filters.add(title_filter)

        # when
        run_smart_group_update(smart_group.id)

        # then
        self.assertEqual(
            title_filter.filter_object.name, "Member Audit Corporation Title"
        )
        self.assertIn(user_1001, self.group.user_set.all())
        self.assertNotIn(user_1002, self.group.user_set.all())
