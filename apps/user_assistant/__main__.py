# -*- coding: utf-8 -*-
import sys
from apps.user_assistant.tui import render_dashboard


def main() -> None:
    """CLI entry point for User Assistant Desk."""
    user_id = 1
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        user_id = int(sys.argv[1])
    render_dashboard(user_id=user_id)


if __name__ == "__main__":
    main()
