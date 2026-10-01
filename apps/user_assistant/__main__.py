# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps User_Assistant -   Main  
# =============================================================================
# Description:
#   CLI entry point for User Assistant Desk.
#
# Usage Examples:
#   CLI:
#     python -m apps.user_assistant.__main__
#   Python API:
#     from apps.user_assistant.__main__ import main
#
#     res = main()
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.user_assistant
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""CLI entry point for User Assistant Desk."""

import sys
from apps.user_assistant.tui import render_dashboard

def main() -> None:
    """CLI entry point for User Assistant Desk."""
    user_id = 1
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        user_id = int(sys.argv[1])
    render_dashboard(user_id=user_id)
if __name__ == '__main__':
    main()