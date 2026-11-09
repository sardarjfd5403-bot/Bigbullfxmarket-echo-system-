"""Command-line tools for BIGBULLS AI commercial license administration."""
from __future__ import annotations

import argparse
import sqlite3
from datetime import UTC, datetime
from decimal import Decimal

from bigbulls_ai.licensing import generate_keypair, issue_license, verify_license
from bigbulls_ai.payments import BIGBULLS_RECEIVING_WALLET, verify_usdt_trc20_payment


def main() -> None:
    parser = argparse.ArgumentParser(prog="bigbulls-license")
    commands = parser.add_subparsers(dest="command", required=True)
    keygen = commands.add_parser("keygen", help="Generate vendor Ed25519 keys")
    keygen.add_argument("--private-key", required=True)
    keygen.add_argument("--public-key", required=True)
    issue = commands.add_parser("issue", help="Issue a signed customer license")
    issue.add_argument("--private-key", required=True)
    issue.add_argument("--output", required=True)
    issue.add_argument("--customer-id", required=True)
    issue.add_argument("--tier", required=True)
    issue.add_argument("--expires", help="Optional ISO-8601 expiry; omit for lifetime access to this release")
    issue.add_argument("--device-id")
    issue.add_argument("--features", default="")
    fulfill = commands.add_parser("fulfill", help="Verify a USDT TRC20 payment and issue a lifetime license")
    fulfill.add_argument("--txid", required=True)
    fulfill.add_argument("--amount", default="199")
    fulfill.add_argument("--confirmations", type=int, default=20)
    fulfill.add_argument("--private-key", required=True)
    fulfill.add_argument("--output", required=True)
    fulfill.add_argument("--ledger", required=True, help="Local SQLite ledger to prevent duplicate transaction fulfillment")
    fulfill.add_argument("--customer-id", required=True)
    fulfill.add_argument("--tier", default="full")
    fulfill.add_argument("--device-id")
    fulfill.add_argument("--features", default="analysis,backtesting,paper-trading,risk-controls,monitoring")
    verify = commands.add_parser("verify", help="Verify a signed license")
    verify.add_argument("--public-key", required=True)
    verify.add_argument("--license", required=True)
    verify.add_argument("--device-id")
    args = parser.parse_args()
    if args.command == "keygen":
        generate_keypair(args.private_key, args.public_key)
        print("Vendor keys generated. Keep the private key offline and secret.")
    elif args.command == "issue":
        data = issue_license(
            args.private_key, args.output, args.customer_id, args.tier,
            datetime.fromisoformat(args.expires) if args.expires else None, args.device_id,
            [item.strip() for item in args.features.split(",") if item.strip()],
        )
        expiry = data["payload"]["expires_at"] or "lifetime (purchased release)"
        print(f"Issued {data['payload']['tier']} license for {data['payload']['customer_id']} — {expiry}")
    elif args.command == "fulfill":
        payment = verify_usdt_trc20_payment(
            args.txid, BIGBULLS_RECEIVING_WALLET, Decimal(args.amount), args.confirmations
        )
        with sqlite3.connect(args.ledger) as ledger:
            ledger.execute(
                "CREATE TABLE IF NOT EXISTS fulfilled_payments ("
                "txid TEXT PRIMARY KEY, customer_id TEXT NOT NULL, "
                "license_path TEXT NOT NULL, verified_at TEXT NOT NULL)"
            )
            ledger.execute("BEGIN IMMEDIATE")
            try:
                ledger.execute(
                    "INSERT INTO fulfilled_payments VALUES (?, ?, ?, ?)",
                    (payment.txid, args.customer_id, args.output, datetime.now(UTC).isoformat()),
                )
                data = issue_license(
                    args.private_key, args.output, args.customer_id, args.tier,
                    None, args.device_id,
                    [item.strip() for item in args.features.split(",") if item.strip()],
                )
                ledger.commit()
            except Exception:
                ledger.rollback()
                raise
        print(
            f"PAYMENT VERIFIED: {payment.amount_usdt} USDT / "
            f"{payment.confirmations} confirmations / tx {payment.txid}"
        )
        print(
            f"LICENSE ISSUED: {data['payload']['customer_id']} / "
            f"{data['payload']['tier']} / lifetime for purchased release"
        )
    else:
        payload = verify_license(args.public_key, args.license, args.device_id)
        expiry = payload["expires_at"] or "lifetime (purchased release)"
        print(f"VALID: {payload['customer_id']} / {payload['tier']} / {expiry}")


if __name__ == "__main__":
    main()
