# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Accounts & Identity TUI Formatter
# =============================================================================
# Description:
#   Консольный форматировщик и визуализатор досье субъектов безопасности
#   Windows, контекста процессов (explain-pid) и графа учетных записей.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity.tui import print_principal_dossier, print_pid_dossier
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:51:00
# =============================================================================

"""Форматирование и визуализация Identity Graph и процессов в терминале."""

from __future__ import annotations

from typing import Any, Dict, List
from apps.windows.modules.accounts_identity.models import Principal, TokenDetails


def format_principal_tree(principal: Principal) -> str:
    """Форматирует Principal в виде дерева ASCII."""
    lines = [
        f"Principal ({principal.name})",
        "│",
        f"├── SID: {principal.sid}",
        f"├── Domain: {principal.domain}",
        f"├── Type: {principal.principal_type.value}",
        f"├── Source: {principal.source.value}",
        f"├── Elevated/Admin: {'YES (🟢)' if principal.is_admin else 'NO'}",
        f"├── Built-in: {'YES' if principal.is_built_in else 'NO'}",
        f"├── Orphaned: {'YES (⚠️)' if principal.is_orphaned else 'NO'}",
        "│",
        "├── Account State",
    ]
    if principal.account:
        acc = principal.account
        lines.append(f"│   ├── Enabled: {'YES' if acc.enabled else 'NO (Disabled)'}")
        lines.append(f"│   ├── Full Name: {acc.full_name or 'N/A'}")
        lines.append(f"│   ├── Password Expires: {acc.password_expires or 'Never'}")
        lines.append(f"│   └── Last Logon: {acc.last_logon or 'N/A'}")
    else:
        lines.append("│   └── N/A")

    lines.append("│")
    lines.append(f"├── Groups ({len(principal.groups)})")
    if principal.groups:
        for i, g in enumerate(principal.groups):
            prefix = "└──" if i == len(principal.groups) - 1 else "├──"
            admin_badge = " [ADMIN]" if g.is_admin else ""
            lines.append(f"│   {prefix} {g.name}{admin_badge} ({g.sid or 'SID N/A'})")
    else:
        lines.append("│   └── None")

    lines.append("│")
    lines.append(f"├── LSA Rights & Privileges ({len(principal.rights)})")
    if principal.rights:
        for i, r in enumerate(principal.rights[:10]):
            prefix = "└──" if i == min(len(principal.rights), 10) - 1 else "├──"
            lines.append(f"│   {prefix} {r}")
        if len(principal.rights) > 10:
            lines.append(f"│   └── ... (+{len(principal.rights) - 10} more)")
    else:
        lines.append("│   └── None")

    lines.append("│")
    lines.append(f"├── Profile: {principal.profile.profile_path if principal.profile else 'None'}")
    lines.append(f"├── Active Sessions: {len(principal.sessions)}")
    lines.append(f"└── Running Processes: {len(principal.processes)}")

    return "\n".join(lines)


def format_pid_tree(pid_info: Dict[str, Any]) -> str:
    """Форматирует контекст безопасности процесса в виде дерева ASCII."""
    acc = pid_info.get("account", {})
    privs = pid_info.get("privileges", [])
    groups = pid_info.get("groups", [])
    elevated_str = "YES (🟢)" if pid_info.get("elevated") else "NO"

    lines = [
        f"PID {pid_info.get('pid')}",
        "│",
        f"├── Process: {pid_info.get('process_name')}",
        f"├── Parent: {pid_info.get('parent_name')} (PID {pid_info.get('parent_pid')})",
        "│",
        "├── Account",
        f"│   ├── {acc.get('domain')}\\{acc.get('user')}",
        f"│   └── SID: {acc.get('sid')}",
        "│",
        "├── Groups",
    ]
    if groups:
        for i, g in enumerate(groups):
            prefix = "└──" if i == len(groups) - 1 else "├──"
            lines.append(f"│   {prefix} {g}")
    else:
        lines.append("│   └── None")

    lines.append("│")
    lines.append(f"├── Integrity: {pid_info.get('integrity')}")
    lines.append(f"├── Elevated: {elevated_str}")
    lines.append("│")
    lines.append("├── Privileges")
    if privs:
        for i, p in enumerate(privs[:8]):
            prefix = "└──" if i == min(len(privs), 8) - 1 else "├──"
            lines.append(f"│   {prefix} {p}")
        if len(privs) > 8:
            lines.append(f"│   └── ... (+{len(privs) - 8} more)")
    else:
        lines.append("│   └── None")

    lines.append("│")
    lines.append("└── Session")
    lines.append("    ├── Console")
    lines.append(f"    └── Session ID: {pid_info.get('session_id')}")

    return "\n".join(lines)
