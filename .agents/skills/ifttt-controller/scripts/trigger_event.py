# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CLI Event Trigger for IFTTT Skill
# =============================================================================
# Description:
#   CLI script for triggering IFTTT events directly from terminal or agent workflows.
#
# Examples:
#   python trigger_event.py --event movie_mode --value1 "active"
#
# File: trigger_event.py
# Package: skills.ifttt-controller.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to sys.path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from plugins.ifttt import send_ifttt_event


async def main():
    parser = argparse.ArgumentParser(description="Trigger an IFTTT Smart Home Event via Maker Webhooks.")
    parser.add_argument("--event", "-e", required=True, help="Name of the IFTTT Webhook event.")
    parser.add_argument("--value1", "-v1", default="", help="Optional value1 parameter.")
    parser.add_argument("--value2", "-v2", default="", help="Optional value2 parameter.")
    parser.add_argument("--value3", "-v3", default="", help="Optional value3 parameter.")
    parser.add_argument("--payload", "-p", default="", help="Optional JSON string payload.")
    parser.add_argument("--key", "-k", default="", help="Optional override IFTTT Webhook Maker Key.")

    args = parser.parse_args()

    json_payload = {}
    if args.payload:
        try:
            json_payload = json.loads(args.payload)
        except Exception as err:
            print(f"Error parsing JSON payload: {err}", file=sys.stderr)
            sys.exit(1)

    result = await send_ifttt_event(
        event_name=args.event,
        value1=args.value1,
        value2=args.value2,
        value3=args.value3,
        json_payload=json_payload,
        webhook_key=args.key,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
