from app_utils.testdata_factories import EveCharacterFactory, UserFactory
from app_utils.testing import NoSocketsTestCase
from memberaudit.tests.testdata.factories_2 import (
    CharacterFactory,
    UserMainBasicAccessFactory,
)

from memberaudit_securegroups.memberaudit import MemberAuditChecks


class MemberAuditChecksTests(NoSocketsTestCase):
    def test_compliance_returns_correct_data_when_user_is_compliant(self):
        # given
        user = UserMainBasicAccessFactory()
        CharacterFactory(user=user)

        # when
        result = MemberAuditChecks.compliance(user)

        # then
        self.assertTrue(result["is_compliant"])
        self.assertEqual(len(result["unregistered_chars"]), 0)

    def test_compliance_returns_correct_data_when_user_is_not_compliant(self):
        # given
        character = EveCharacterFactory(character_name="Test Character")
        user = UserMainBasicAccessFactory(main_character__character=character)

        # when
        result = MemberAuditChecks.compliance(user)

        # then
        self.assertFalse(result["is_compliant"])
        self.assertEqual(len(result["unregistered_chars"]), 1)
        self.assertEqual(
            result["unregistered_chars"][0].character_name, "Test Character"
        )

    def test_compliance_handles_user_with_no_characters(self):
        # given
        user_without_chars = UserFactory()

        # when
        result = MemberAuditChecks.compliance(user_without_chars)

        # then
        self.assertFalse(result["is_compliant"])
        self.assertEqual(len(result["unregistered_chars"]), 0)
