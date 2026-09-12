## \file .agents/skills/gdrive-organizer/scripts/main.py
# -*- coding: utf-8 -*-
#! venv/Scripts/python.exe

"""
Google Drive Intelligent Auditor & Organizer CLI.
=================================================

CLI entry point for scanning Google Drive, auditing structural disorganization,
generating restructuring proposals, and applying safe reorganization plans.
"""

from pathlib import Path
from typing import Optional
import argparse
import json
import sys

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Ensure current script folder is on sys.path
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from src.logger.logger import logger
from gdrive_scanner import GDriveScanner
from audit_engine import GDriveAuditEngine
from proposal_generator import GDriveProposalGenerator
from reorganize_executor import GDriveReorganizeExecutor


def cmd_audit(args: argparse.Namespace) -> int:
    """Scan and print health audit report."""
    print("🔍 Scanning Google Drive hierarchy...")
    scanner = GDriveScanner(account_name=args.account)
    if not scanner.service:
        print("❌ Could not authenticate with Google Drive. Check credentials.json or .env.")
        return 1

    items = scanner.fetch_all_items(folder_id=args.folder_id)
    hierarchy = scanner.build_hierarchy(items)

    engine = GDriveAuditEngine(hierarchy)
    audit = engine.run_full_audit()

    generator = GDriveProposalGenerator(audit, hierarchy)
    report = generator.generate_markdown_report()

    print("\n" + report)

    if args.report_out:
        out_p = Path(args.report_out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(report, encoding="utf-8")
        print(f"\n💾 Saved full report to {out_p.resolve()}")

    return 0


def cmd_propose(args: argparse.Namespace) -> int:
    """Generate restructuring plan JSON and markdown report."""
    print("🔍 Scanning and generating reorganization plan...")
    scanner = GDriveScanner(account_name=args.account)
    if not scanner.service:
        print("❌ Could not authenticate with Google Drive. Check credentials.json or .env.")
        return 1

    items = scanner.fetch_all_items(folder_id=args.folder_id)
    hierarchy = scanner.build_hierarchy(items)

    engine = GDriveAuditEngine(hierarchy)
    audit = engine.run_full_audit()

    generator = GDriveProposalGenerator(audit, hierarchy)
    plan = generator.generate_plan()
    report = generator.generate_markdown_report(plan)

    # Save plan JSON
    plan_path = Path(args.out or "gdrive_reorganize_plan.json")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated plan with {plan['total_actions']} actions saved to: {plan_path.resolve()}")

    if args.report_out:
        out_p = Path(args.report_out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(report, encoding="utf-8")
        print(f"💾 Report saved to: {out_p.resolve()}")

    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    """Apply plan actions to Google Drive."""
    plan_path = Path(args.plan)
    if not plan_path.exists():
        print(f"❌ Plan file not found: {plan_path}")
        return 1

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    executor = GDriveReorganizeExecutor(account_name=args.account)
    if not args.dry_run and not executor.service:
        print("❌ Could not authenticate with Google Drive. Check credentials.json or .env.")
        return 1

    log_path = Path(args.log_out or "gdrive_execution_log.json")
    result = executor.execute_plan(plan, dry_run=args.dry_run, log_output_path=log_path)

    print("\n🏁 Execution Summary:")
    print(f"  - Dry-Run: {result['dry_run']}")
    print(f"  - Total Actions: {result['total_actions']}")
    print(f"  - Successful: {result['successful']}")
    print(f"  - Failed: {result['failed']}")
    print(f"  - Log Saved: {log_path.resolve()}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Google Drive Auditor & Organizer")
    parser.add_argument("--account", help="Specific Google account name from pool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit command
    audit_p = subparsers.add_parser("audit", help="Audit Drive health and print report")
    audit_p.add_argument("--folder-id", help="Optional subfolder ID to constrain scan")
    audit_p.add_argument("--report-out", help="Path to save markdown report")
    audit_p.set_defaults(func=cmd_audit)

    # Propose command
    prop_p = subparsers.add_parser("propose", help="Generate restructuring plan and report")
    prop_p.add_argument("--folder-id", help="Optional subfolder ID")
    prop_p.add_argument("--out", "-o", default="gdrive_plan.json", help="Output plan JSON file")
    prop_p.add_argument("--report-out", help="Output markdown report file")
    prop_p.set_defaults(func=cmd_propose)

    # Apply command
    app_p = subparsers.add_parser("apply", help="Execute restructuring plan")
    app_p.add_argument("--plan", "-p", required=True, help="Input plan JSON file")
    app_p.add_argument("--dry-run", action="store_true", default=False, help="Simulate without changes")
    app_p.add_argument("--log-out", help="Output log JSON file")
    app_p.set_defaults(func=cmd_apply)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
