"""Independent TRON USDT (TRC20) payment verification.

Uses the TRON mainnet API. A transaction hash or screenshot alone is never
accepted: contract, recipient, token contract, amount, receipt and confirmations
are all checked before fulfillment.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TRON_API = "https://api.trongrid.io"
USDT_TRC20_CONTRACT_HEX = "41a614f803b6fd780986a42c78ec9c7f77e6ded13c"
USDT_DECIMALS = 6
BIGBULLS_RECEIVING_WALLET = "TGHzwHhJ1XULyUmf6B8zf4djkyoeh6eiYY"


class PaymentVerificationError(ValueError):
    """Raised when a submitted transaction cannot be proven as valid payment."""


@dataclass(frozen=True)
class VerifiedPayment:
    txid: str
    recipient: str
    amount_usdt: Decimal
    confirmations: int
    block_number: int


def _post_json(path: str, payload: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    key = api_key or os.getenv("TRONGRID_API_KEY")
    if key:
        headers["TRON-PRO-API-KEY"] = key
    request = Request(TRON_API + path, data=body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise PaymentVerificationError("TRON explorer unavailable; payment not approved") from exc
    if not isinstance(data, dict):
        raise PaymentVerificationError("Unexpected TRON API response")
    return data


def _base58check_to_hex(address: str) -> str:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    number = 0
    try:
        for char in address:
            number = number * 58 + alphabet.index(char)
    except ValueError as exc:
        raise PaymentVerificationError("Invalid TRON receiving address") from exc
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
    raw = b"\\x00" * (len(address) - len(address.lstrip("1"))) + raw
    if len(raw) != 25:
        raise PaymentVerificationError("Invalid TRON address length")
    payload, checksum = raw[:-4], raw[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected or payload[0] != 0x41:
        raise PaymentVerificationError("Invalid TRON address checksum")
    return payload.hex()


def verify_usdt_trc20_payment(
    txid: str,
    expected_address: str,
    expected_amount_usdt: Decimal = Decimal("199"),
    min_confirmations: int = 20,
    api_key: str | None = None,
) -> VerifiedPayment:
    """Verify exact USDT TRC20 mainnet payment before issuing any product."""
    if not re.fullmatch(r"[0-9a-fA-F]{64}", txid):
        raise PaymentVerificationError("Transaction hash must be 64 hexadecimal characters")
    if min_confirmations < 1:
        raise ValueError("min_confirmations must be at least 1")
    recipient_hex = _base58check_to_hex(expected_address)
    info = _post_json("/wallet/gettransactioninfobyid", {"value": txid.lower()}, api_key)
    if not info or not info.get("id"):
        raise PaymentVerificationError("Transaction not found or not yet indexed")
    receipt = info.get("receipt") or {}
    if receipt.get("result") != "SUCCESS":
        raise PaymentVerificationError("Transaction execution was not successful")
    tx = _post_json("/wallet/gettransactionbyid", {"value": txid.lower()}, api_key)
    contracts = (tx.get("raw_data") or {}).get("contract") or []
    if len(contracts) != 1:
        raise PaymentVerificationError("Expected exactly one transfer contract")
    contract = contracts[0]
    if contract.get("type") != "TriggerSmartContract":
        raise PaymentVerificationError("Transaction is not a TRC20 contract call")
    value = ((contract.get("parameter") or {}).get("value") or {})
    if str(value.get("contract_address", "")).lower() != USDT_TRC20_CONTRACT_HEX:
        raise PaymentVerificationError("Token contract is not official USDT TRC20")
    call_data = str(value.get("data", "")).lower()
    if not call_data.startswith("a9059cbb") or len(call_data) != 136:
        raise PaymentVerificationError("Transaction is not a standard USDT transfer")
    actual_recipient = "41" + call_data[8:48]
    if actual_recipient != recipient_hex:
        raise PaymentVerificationError("Payment was sent to a different wallet")
    raw_amount = int(call_data[72:136], 16)
    actual_amount = Decimal(raw_amount) / (Decimal(10) ** USDT_DECIMALS)
    if actual_amount != expected_amount_usdt:
        raise PaymentVerificationError(
            f"Incorrect payment amount: received {actual_amount} USDT"
        )
    block_number = int(info.get("blockNumber") or 0)
    if block_number <= 0:
        raise PaymentVerificationError("Transaction is not confirmed in a block")
    latest = _post_json("/wallet/getnowblock", {}, api_key)
    latest_number = int((((latest.get("block_header") or {}).get("raw_data") or {}).get("number")) or 0)
    confirmations = max(0, latest_number - block_number + 1)
    if confirmations < min_confirmations:
        raise PaymentVerificationError(
            f"Only {confirmations} confirmations; {min_confirmations} required"
        )
    return VerifiedPayment(
        txid=txid.lower(), recipient=expected_address,
        amount_usdt=actual_amount, confirmations=confirmations,
        block_number=block_number,
    )
