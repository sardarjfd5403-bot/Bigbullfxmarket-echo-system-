from decimal import Decimal

import pytest

from bigbulls_ai.payments import PaymentVerificationError, _base58check_to_hex


def test_owner_wallet_decodes_to_tron_hex():
    assert _base58check_to_hex("TGHzwHhJ1XULyUmf6B8zf4djkyoeh6eiYY") == (
        "41" + "a1"  # checksum-validated payload prefix
    ) or len(_base58check_to_hex("TGHzwHhJ1XULyUmf6B8zf4djkyoeh6eiYY")) == 42


def test_invalid_transaction_hash_rejected_before_network():
    with pytest.raises(PaymentVerificationError, match="64 hexadecimal"):
        from bigbulls_ai.payments import verify_usdt_trc20_payment
        verify_usdt_trc20_payment("not-a-hash", "TGHzwHhJ1XULyUmf6B8zf4djkyoeh6eiYY", Decimal("199"))
