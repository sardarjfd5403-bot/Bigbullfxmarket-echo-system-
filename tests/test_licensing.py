import json
from datetime import UTC, datetime, timedelta

import pytest

from bigbulls_ai.licensing import generate_keypair, issue_license, verify_license


def test_signed_license_round_trip_and_device_binding(tmp_path):
    private = tmp_path / "vendor-private.pem"
    public = tmp_path / "vendor-public.pem"
    license_file = tmp_path / "customer.license.json"
    generate_keypair(private, public)
    issue_license(private, license_file, "client-001", "pro",
                  datetime.now(UTC) + timedelta(days=30), "device-abc", ["signals", "backtest"])
    payload = verify_license(public, license_file, "device-abc")
    assert payload["customer_id"] == "client-001"
    assert payload["tier"] == "pro"
    with pytest.raises(ValueError, match="different device"):
        verify_license(public, license_file, "device-other")


def test_tampered_license_is_rejected(tmp_path):
    private = tmp_path / "private.pem"
    public = tmp_path / "public.pem"
    license_file = tmp_path / "license.json"
    generate_keypair(private, public)
    issue_license(private, license_file, "client", "starter", datetime.now(UTC) + timedelta(days=1))
    data = json.loads(license_file.read_text())
    data["payload"]["tier"] = "enterprise"
    license_file.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="signature"):
        verify_license(public, license_file)


def test_expired_license_is_rejected(tmp_path):
    private = tmp_path / "private.pem"
    public = tmp_path / "public.pem"
    license_file = tmp_path / "license.json"
    generate_keypair(private, public)
    issue_license(private, license_file, "client", "starter", datetime.now(UTC) - timedelta(days=1))
    with pytest.raises(ValueError, match="expired"):
        verify_license(public, license_file)


def test_lifetime_license_has_no_expiry(tmp_path):
    private = tmp_path / "private.pem"
    public = tmp_path / "public.pem"
    license_file = tmp_path / "lifetime.license.json"
    generate_keypair(private, public)
    issue_license(private, license_file, "client-lifetime", "full")
    payload = verify_license(public, license_file)
    assert payload["customer_id"] == "client-lifetime"
    assert payload["expires_at"] is None
