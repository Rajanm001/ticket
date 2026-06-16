"""Command-line triage tool.

Satisfies the acceptance-checklist requirement for a CLI that ingests a ticket
and returns category + draft + escalation. Reads a ticket either from JSON (a
file path or '-' for stdin) or from --title/--body flags, and prints the full
triage result as formatted JSON.

Examples:
    python -m app.cli --title "Refund not received" --body "I cancelled but no refund. Urgent."
    python -m app.cli --tier enterprise --title "Outage" --body "Production is down with 503s."
    echo '{"title":"Bug","body":"App crashes on upload"}' | python -m app.cli --json -
    python -m app.cli --json ticket.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.service import TriageService


def _load_from_json(source: str) -> dict:
    raw = sys.stdin.read() if source == "-" else open(source, "r", encoding="utf-8").read()
    return json.loads(raw)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Triage a single support ticket.")
    parser.add_argument("--json", dest="json_source", help="Path to a ticket JSON file, or '-' for stdin.")
    parser.add_argument("--ticket-id", default="", help="Ticket identifier.")
    parser.add_argument("--title", default="", help="Ticket title/subject.")
    parser.add_argument("--body", default="", help="Ticket body.")
    parser.add_argument("--product", default=None, help="Optional product area (web/api/mobile).")
    parser.add_argument("--tier", dest="customer_tier", default=None, help="Optional account tier (free/pro/enterprise).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.json_source:
        ticket = _load_from_json(args.json_source)
    else:
        ticket = {
            "ticket_id": args.ticket_id,
            "title": args.title,
            "body": args.body,
            "product": args.product,
            "customer_tier": args.customer_tier,
        }

    if not ticket.get("title") and not ticket.get("body"):
        print("Error: provide --title/--body or --json with a ticket.", file=sys.stderr)
        return 2

    service = TriageService()
    result = asyncio.run(
        service.triage(
            ticket_id=ticket.get("ticket_id", "") or "CLI_TICKET",
            title=ticket.get("title", ""),
            body=ticket.get("body", ""),
            product=ticket.get("product"),
            customer_tier=ticket.get("customer_tier"),
        )
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
