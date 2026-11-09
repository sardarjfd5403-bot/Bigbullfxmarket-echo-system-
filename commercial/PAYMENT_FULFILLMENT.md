# Payment verification and customer fulfillment — deployment checklist

## Current implementation
The repository contains a TRON mainnet USDT TRC20 verifier in `src/bigbulls_ai/payments.py`. It checks the transaction hash, successful receipt, official USDT contract, exact destination wallet, exact amount, and configurable confirmation count. It uses the TRON Grid API; set `TRONGRID_API_KEY` as a server-side environment secret for production reliability. The verifier is not a hosted checkout or public customer portal.

## Fixed commercial terms
- Product: BIGBULLS AI Full Package
- Price: 199 USDT
- Network: TRON (TRC20) only
- Receiving wallet: `TGHzwHhJ1XULyUmf6B8zf4djkyoeh6eiYY`
- License: perpetual for the purchased release
- Screenshot: supporting evidence only; never payment proof
- Wrong network, wrong token, wrong wallet, underpayment, duplicate transaction or insufficient confirmations: do not fulfill.

**Before publishing payment instructions, independently verify the receiving address and TRC20 network from the owner's wallet. Never rely only on a value copied from source control.**

## Required production order
1. Customer submits contact email and transaction hash through an HTTPS form. Do not ask for wallet seed phrases or private keys.
2. Backend calls `verify_usdt_trc20_payment` using the server-side expected wallet and amount. Reject any mismatch and record the txid under a unique database constraint to prevent replay.
3. An authorized operator reviews the verified record and confirms the customer identity/order. Screenshots cannot override a failed chain check.
4. License service issues an Ed25519-signed license with no expiry for the purchased release. Device binding is optional and must be disclosed before purchase.
5. Package is stored in private object storage. Generate a short-lived, single-use signed URL after successful payment and license issuance. Never expose a permanent public package URL or GitHub release asset for paid binaries.
6. Record order ID, txid, confirmation count, license ID, package version, delivery expiry and fulfillment status. Never log secrets or upload customer evidence to the public repository.

## Secrets and hosting still required
- `TRONGRID_API_KEY`: TRON Grid API key, server-side only.
- `BIGBULLS_LICENSE_PRIVATE_KEY`: Ed25519 private signing key, stored in a secret manager or offline signing environment; never commit it.
- `BIGBULLS_LICENSE_PUBLIC_KEY`: safe to distribute with the verifier.
- Private object-storage credentials and a short-lived URL signer.
- HTTPS backend, persistent database with unique txid constraint, admin authentication, rate limiting, audit logs and backups.

## Release gate
Do not announce automated payment-to-download fulfillment as live until the hosted backend, database, secret storage, private package bucket, email delivery and end-to-end tests are deployed. Until then, process orders manually: independently verify on-chain payment, issue the license from a protected machine, and send a one-time private link.

## Local operator command (implemented)
After installing the package, an authorized operator can verify a transaction and issue a signed lifetime license in one command. The SQLite ledger prevents the same transaction hash from being fulfilled twice on that operator machine:

```bash
bigbulls-license fulfill \
  --txid CUSTOMER_TRANSACTION_HASH \
  --amount 199 \
  --confirmations 20 \
  --private-key /secure/vendor-private.pem \
  --output ./issued/customer-001.license.json \
  --customer-id customer-001 \
  --ledger ./private-fulfillment.sqlite
```

Set `TRONGRID_API_KEY` in the server/operator environment where available. Keep the SQLite ledger and license files private and backed up. This is a local operator workflow, not yet a hosted customer portal. It does not itself email customers or mint storage download links. For a distributed multi-operator service, move the unique txid constraint into a shared transactional database before launch.
