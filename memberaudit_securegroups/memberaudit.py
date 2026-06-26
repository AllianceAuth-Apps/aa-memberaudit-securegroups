"""
Wrapper for checks in AA Member Audit
"""

# Django
from django.contrib.auth.models import User

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# Member Audit
from memberaudit.models import General


class MemberAuditChecks:  # pylint: disable=too-few-public-methods
    """
    Member Audit Checks
    """

    @staticmethod
    def compliance(user: User) -> dict:
        """
        Check user compliance with AA Member Audit and return probably missing characters

        :param user: The user
        :type user: User
        :return: Compliance information
        :rtype: dict
        """

        is_compliant = General.compliant_users().filter(pk=user.pk).exists()
        unregistered_chars = (
            EveCharacter.objects.filter(
                character_ownership__user=user, memberaudit_character__isnull=True
            )
            .order_by("character_name")
            .all()
        )

        return {"is_compliant": is_compliant, "unregistered_chars": unregistered_chars}
