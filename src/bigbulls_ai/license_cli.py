"""Command-line tools for BIGBULLS AI commercial license administration."""
from __future__ import annotations

import argparse
from datetime import datetime

from bigbulls_ai.licensing import generate_keypair, issue_license, verify_license


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
    issue.add_argument("--expires", required=True, help="ISO-8601 timestamp with timezone")
    issue.add_argument("--device-id")
    issue.add_argument("--features", default="")
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
            datetime.fromisoformat(args.expires), args.device_id,
            [item.strip() for item in args.features.split(",") if item.strip()],
        )
        print(f"Issued {data['payload']['tier']} license for {data['payload']['customer_id']}")
    else:
        payload = verify_license(args.public_key, args.license, args.device_id)
        print(f"VALID: {payload['customer_id']} / {payload['tier']} / expires {payload['expires_at']}")


if __name__ == "__main__":
    main()
