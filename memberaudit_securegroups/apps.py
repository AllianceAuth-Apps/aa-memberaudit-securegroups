"""
App's base definitions
"""

# Django
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

# Memberaudit Securegroups
from memberaudit_securegroups import __version__


class MemberAuditSecureGroupsConfig(AppConfig):
    """
    MemberAuditSecureGroupsConfig
    """

    name = "memberaudit_securegroups"
    label = "memberaudit_securegroups"
    verbose_name = _(f"Member Audit Secure Groups Integration v{__version__}")
