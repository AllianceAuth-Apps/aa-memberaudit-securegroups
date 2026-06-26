# Standard Library
from unittest.mock import patch

# Django
from django.contrib.auth.models import User
from django.test import TestCase

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter

# Memberaudit Securegroups
from memberaudit_securegroups.memberaudit import MemberAuditChecks


class MemberAuditChecksTests(TestCase):
    """
    Test cases for MemberAuditChecks
    """

    def setUp(self):
        """
        Set up test data for MemberAuditChecks tests.

        :return:
        :rtype:
        """

        self.user = User.objects.create(username="testuser")
        self.character = EveCharacter.objects.create(
            character_id=12345,
            character_name="Test Character",
            corporation_id=1234586,
            alliance_id=654321,
        )
        self.ownership = CharacterOwnership.objects.create(
            user=self.user, character=self.character
        )
        self.character.character_ownership = self.ownership
        self.character.save()

    @patch("memberaudit.models.General.compliant_users")
    def test_compliance_returns_correct_data_when_user_is_compliant(
        self, mock_compliant_users
    ):
        """
        Test that the compliance method returns correct data when the user is compliant.

        :param mock_compliant_users:
        :type mock_compliant_users:
        :return:
        :rtype:
        """

        mock_compliant_users.return_value.filter.return_value.exists.return_value = True

        result = MemberAuditChecks.compliance(self.user)

        self.assertTrue(result["is_compliant"])
        self.assertEqual(len(result["unregistered_chars"]), 1)
        self.assertEqual(
            result["unregistered_chars"][0].character_name, "Test Character"
        )

    @patch("memberaudit.models.General.compliant_users")
    def test_compliance_returns_correct_data_when_user_is_not_compliant(
        self, mock_compliant_users
    ):
        """
        Test that the compliance method returns correct data when the user is not compliant.

        :param mock_compliant_users:
        :type mock_compliant_users:
        :return:
        :rtype:
        """

        mock_compliant_users.return_value.filter.return_value.exists.return_value = (
            False
        )

        result = MemberAuditChecks.compliance(self.user)

        self.assertFalse(result["is_compliant"])
        self.assertEqual(len(result["unregistered_chars"]), 1)
        self.assertEqual(
            result["unregistered_chars"][0].character_name, "Test Character"
        )

    @patch("memberaudit.models.General.compliant_users")
    def test_compliance_handles_user_with_no_characters(self, mock_compliant_users):
        """
        Test that the compliance method handles a user with no characters.

        :param mock_compliant_users:
        :type mock_compliant_users:
        :return:
        :rtype:
        """

        mock_compliant_users.return_value.filter.return_value.exists.return_value = True
        user_without_chars = User.objects.create(username="nocharuser")

        result = MemberAuditChecks.compliance(user_without_chars)

        self.assertTrue(result["is_compliant"])
        self.assertEqual(len(result["unregistered_chars"]), 0)
