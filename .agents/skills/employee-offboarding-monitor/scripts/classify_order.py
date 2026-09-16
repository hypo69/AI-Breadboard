# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Classify Dismissal Order
# =============================================================================
# Description:
#   Classifies HR documents and extracts dismissal metadata using regex heuristics
#   or structured extraction.
#
# Examples:
#   >>> from classify_order import extract_dismissal_order_info
#   >>> res = extract_dismissal_order_info('Приказ об увольнении Иванова И.И.')
#
# File: classify_order.py
# Package: .agents.skills.employee-offboarding-monitor.scripts
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================
"""Dismissal order classification and entity extraction."""

from __future__ import annotations

import argparse
import json
import re
from typing import Any, Dict


def extract_dismissal_order_info(text: str) -> Dict[str, Any]:
    """Analyze document text and extract termination order details.

    Args:
        text (str): Raw document text.

    Returns:
        Dict[str, Any]: Structured dictionary with extraction results.
    """
    if not text:
        return {
            'is_dismissal_order': False,
            'confidence': 0.0,
            'employee_name': None,
            'order_number': None,
            'termination_date': None,
            'reason': None,
        }

    lower_text = text.lower()
    dismissal_keywords = [
        'увольнен', 'расторжен', 'прекращен', 'трудового договора',
        'termination', 'dismissal', 'offboarding', 'resign'
    ]

    match_count = sum(1 for kw in dismissal_keywords if kw in lower_text)
    is_order = match_count >= 1 and any(kw in lower_text for kw in ['приказ', 'распоряжение', 'order', 'notice'])

    order_match = re.search(r'(?:приказ|order|распоряжение)\s*(?:№|no\.?)?\s*([0-9a-zA-Zа-яА-Я\-\/]+)', text, re.IGNORECASE)
    order_num = order_match.group(1) if order_match else None

    date_match = re.search(r'(\d{2}[.\/-]\d{2}[.\/-]\d{4}|\d{4}-\d{2}-\d{2})', text)
    term_date = date_match.group(1) if date_match else None

    name_match = re.search(r'(?:работника|сотрудника|employee|гражданина)\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})', text)
    emp_name = name_match.group(1) if name_match else None

    confidence = 0.95 if (is_order and emp_name) else (0.75 if is_order else 0.0)

    return {
        'is_dismissal_order': is_order,
        'confidence': confidence,
        'employee_name': emp_name,
        'order_number': order_num,
        'termination_date': term_date,
        'reason': 'Heuristic detection' if is_order else None,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Classify order and extract info')
    parser.add_argument('--text', required=True, help='Document text')
    args = parser.parse_args()
    res = extract_dismissal_order_info(args.text)
    print(json.dumps(res, ensure_ascii=False, indent=2))
