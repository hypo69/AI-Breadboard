# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Check User Resources
# =============================================================================
# Description:
#   Scans and discovers associated accounts, folders, and resources for an employee.
#
# Examples:
#   >>> from check_resources import discover_user_resources
#   >>> res = discover_user_resources('Иванов Иван')
#
# File: check_resources.py
# Package: .agents.skills.employee-offboarding-monitor.scripts
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================
"""Enterprise resource discovery for employee offboarding."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List


def discover_user_resources(employee_name: str, username: str | None = None) -> Dict[str, Any]:
    """Find directories, mailboxes, and tokens belonging to an employee.

    Args:
        employee_name (str): Full name of the employee.
        username (str | None): Optional account username or login.

    Returns:
        Dict[str, Any]: Dictionary detailing user resource footprint.
    """
    uname = username or employee_name.lower().replace(' ', '.')

    resources: List[Dict[str, str]] = [
        {
            'type': 'Active Directory / LDAP Account',
            'identifier': f'DOMAIN\\{uname}',
            'action_required': 'Disable Account & Revoke Tokens'
        },
        {
            'type': 'Exchange / Corporate Mailbox',
            'identifier': f'{uname}@company.com',
            'action_required': 'Quarantine & Cold Storage Backup'
        },
        {
            'type': 'User Home Storage / Network Share',
            'identifier': f'\\\\storage\\users\\{uname}',
            'action_required': 'Schedule Deletion (30-day Retention)'
        },
        {
            'type': 'VPN / Remote Access MFA',
            'identifier': f'{uname}-vpn-profile',
            'action_required': 'Revoke Certificate'
        }
    ]

    return {
        'employee_name': employee_name,
        'username': uname,
        'resources_count': len(resources),
        'resources': resources,
        'status': 'ready_for_review'
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Discover user resources')
    parser.add_argument('--name', required=True, help='Employee full name')
    parser.add_argument('--username', default=None, help='User login')
    args = parser.parse_args()
    print(json.dumps(discover_user_resources(args.name, args.username), ensure_ascii=False, indent=2))
