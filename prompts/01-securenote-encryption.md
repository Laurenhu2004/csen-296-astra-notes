# Session 01 — SecureNote encryption (FR-4 / SEC-1)

## Weaker prompt
> "Write a function to encrypt a note with a password."

Produced a one-liner using `Fernet(Fernet.generate_key())` and storing the key next to
the ciphertext. **Rejected** — that defeats the purpose: anyone with the file gets the
key, and SEC-1 forbids deriving the key from anything but the user's passphrase.

## Stronger prompt
> "Design an EncryptionService for SecureNotes that satisfies SEC-1: authenticated
> symmetric encryption (Fernet) with a key derived from the user's passphrase via a
> memory-hard KDF (scrypt) and a per-note salt. The plaintext body must never be
> persisted. Show how `make_secure` and `unlock` use it, including the wrong-passphrase
> path and failed-attempt auditing (SEC-4)."

## Kept
- `derive_key(passphrase, salt)` → scrypt → urlsafe-base64 → Fernet key.
- Per-note random salt stored alongside the ciphertext (safe to store; useless without
  the passphrase).
- `make_secure` blanks `body` and stores only `encrypted_body` — verified by a test that
  greps the raw `.db` bytes for the plaintext (`test_make_secure_encrypts_body_at_rest`).
- Wrong passphrase → `InvalidToken` → typed `UnlockError`, plus an `unlock.failed` audit
  entry and 3-attempt backoff.

## Refined
- The AI used `hashlib.scrypt` with default `maxmem`, which raised
  `ValueError: memory limit exceeded` for `n=32768` (needs ~32 MB > OpenSSL's default
  cap). **Fixed** by computing `maxmem = 128 * n * r * (p+1) + 1 MB`.
- Kept a `passphrase_hash` fingerprint per the UML, but documented that it is *not* the
  key and never derives one — real authentication is the Fernet auth tag on decrypt.

## Rejected
- A suggestion to add a "password hint" field. **Rejected**: it nudges users toward weak,
  guessable passphrases and erodes the no-recovery guarantee the design deliberately
  makes (consistent with the Week 3.1 rejection of a recovery hint).
