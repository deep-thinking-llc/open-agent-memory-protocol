# OAMP Security Guide

## Encryption at Rest

### Recommended Ciphers
- **AES-256-GCM** (recommended) — authenticated encryption with associated data
- **ChaCha20-Poly1305** — alternative for platforms without AES hardware acceleration
- **XChaCha20-Poly1305** — extended nonce variant for high-volume scenarios

### Key Management
- Use per-user encryption keys where possible
- Derive keys using Argon2id (for password-derived) or HKDF (for key-derived)
- Rotate keys periodically (recommended: annually)
- Store key material in a hardware security module (HSM) or platform keychain when available

## Secure Deletion

When a user requests deletion:
1. Remove all database records
2. Zeroize any in-memory copies (use `zeroize` crate in Rust, `sodium_memzero` in C)
3. If using FTS indexes, rebuild the index after deletion
4. Verify deletion by attempting to retrieve — must return 404

## GDPR Compliance

OAMP's mandatory requirements map to GDPR articles:

| OAMP Requirement | GDPR Article |
|-----------------|--------------|
| Full export | Article 20 (Data Portability) |
| Full deletion | Article 17 (Right to Erasure) |
| Provenance tracking | Article 30 (Records of Processing) |
| Encryption at rest | Article 32 (Security of Processing) |

## CCPA Compliance

| OAMP Requirement | CCPA Section |
|-----------------|-------------|
| Full export | Section 1798.100 (Right to Know) |
| Full deletion | Section 1798.105 (Right to Delete) |
| No content logging | Section 1798.150 (Data Breach Liability) |

## Threat Model

| Threat | Mitigation |
|--------|-----------|
| Export file intercepted in transit | Encrypt export files; use HTTPS for all API calls |
| Import of poisoned data | Validate against JSON Schema; apply confidence caps on imported data |
| Backend compromise | Encryption at rest protects content; audit logs detect unauthorized access |
| Replay of old exports | Include `exported_at` timestamp; backends MAY reject stale exports |
| Cross-user data leakage | Enforce user_id scoping on all queries; never return data for other users |
