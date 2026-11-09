"""Ed25519-signed offline license verification for BIGBULLS AI.

The private signing key must remain with the vendor. Customer installations
receive only the public verification key and signed license files.
"""
from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

PRODUCT_ID = "BIGBULLS_AI"


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def generate_keypair(private_path: str | Path, public_path: str | Path) -> None:
    """Generate vendor signing keys. Never distribute the private key."""
    private_key = Ed25519PrivateKey.generate()
    Path(private_path).write_bytes(private_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    Path(public_path).write_bytes(private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    Path(private_path).chmod(0o600)


def issue_license(
    private_key_path: str | Path,
    output_path: str | Path,
    customer_id: str,
    tier: str,
    expires_at: datetime,
    device_id: str | None = None,
    features: list[str] | None = None,
) -> dict[str, Any]:
    if not customer_id.strip() or not tier.strip():
        raise ValueError("customer_id and tier are required")
    if expires_at.tzinfo is None:
        raise ValueError("expires_at must be timezone-aware")
    private_key = serialization.load_pem_private_key(
        Path(private_key_path).read_bytes(), password=None
    )
    if not isinstance(private_key, Ed25519PrivateKey):
        raise TypeError("Expected an Ed25519 private key")
    payload: dict[str, Any] = {
        "product": PRODUCT_ID,
        "customer_id": customer_id.strip(),
        "tier": tier.strip().lower(),
        "issued_at": datetime.now(UTC).isoformat(),
        "expires_at": expires_at.astimezone(UTC).isoformat(),
        "device_id": device_id.strip() if device_id else None,
        "features": sorted(set(features or [])),
    }
    signature = private_key.sign(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode())
    data = {"payload": payload, "signature": base64.b64encode(signature).decode("ascii"),
            "algorithm": "Ed25519"}
    Path(output_path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data


def verify_license(
    public_key_path: str | Path,
    license_path: str | Path,
    device_id: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Verify signature, product, expiry and optional device binding."""
    data = json.loads(Path(license_path).read_text(encoding="utf-8"))
    payload = data.get("payload")
    if not isinstance(payload, dict) or data.get("algorithm") != "Ed25519":
        raise ValueError("Invalid license envelope")
    signature = base64.b64decode(data["signature"], validate=True)
    public_key = serialization.load_pem_public_key(Path(public_key_path).read_bytes())
    if not isinstance(public_key, Ed25519PublicKey):
        raise TypeError("Expected an Ed25519 public key")
    try:
        public_key.verify(signature, json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode())
    except InvalidSignature as exc:
        raise ValueError("License signature is invalid") from exc
    if payload.get("product") != PRODUCT_ID:
        raise ValueError("License is for a different product")
    expires_at = datetime.fromisoformat(str(payload["expires_at"]))
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if expires_at <= current.astimezone(UTC):
        raise ValueError("License has expired")
    if payload.get("device_id") and payload["device_id"] != device_id:
        raise ValueError("License is bound to a different device")
    return payload
