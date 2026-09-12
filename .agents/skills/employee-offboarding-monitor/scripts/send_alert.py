# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Send Admin Offboarding Alert
# =============================================================================
# Description:
#   Formats and dispatches structured security alerts to administrators.
#
# Examples:
#   >>> from send_alert import format_offboarding_alert
#   >>> alert = format_offboarding_alert({'employee_name': 'Test'})
#
# File: send_alert.py
# Package: .agents.skills.employee-offboarding-monitor.scripts
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================
"""Administrator alerting and notification formatter."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict


def format_offboarding_alert(order_data: Dict[str, Any], resources_data: Dict[str, Any] | None = None) -> str:
    """Format high-priority Markdown alert for IT/Security Administrators.

    Args:
        order_data (Dict[str, Any]): Dismissal order extraction result.
        resources_data (Dict[str, Any] | None): Discovered user footprint resources.

    Returns:
        str: Formatted markdown alert message.
    """
    emp = order_data.get('employee_name', 'Не указано')
    ord_num = order_data.get('order_number', 'Б/Н')
    term_date = order_data.get('termination_date', 'Не указана')

    lines = [
        '🚨 **ВНИМАНИЕ: Обнаружен приказ об увольнении сотрудника**',
        '---',
        f'👤 **Сотрудник:** {emp}',
        f'📄 **Приказ:** № {ord_num}',
        f'📅 **Дата увольнения:** {term_date}',
        '',
        '📦 **Обнаруженные ресурсы для вывода из эксплуатации:**'
    ]

    res_list = (resources_data or {}).get('resources', [])
    if res_list:
        for r in res_list:
            lines.append(f"- **{r.get('type')}**: {r.get('identifier')} ➔ _{r.get('action_required')}_")
    else:
        lines.append('- _Требуется ручной аудит корпоративных ресурсов_')

    lines.extend([
        '',
        '🔒 **Действия администратора (Human-in-the-Loop):**',
        '1. [Заблокировать УЗ и отозвать токены]',
        '2. [Запланировать архивацию и удаление данных]',
        '3. [Отклонить (Ложное срабатывание)]'
    ])

    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Format offboarding alert')
    parser.add_argument('--order', required=True, help='Order JSON file or string')
    args = parser.parse_args()

    try:
        data = json.loads(args.order)
    except Exception:
        data = {'employee_name': args.order}

    print(format_offboarding_alert(data))
