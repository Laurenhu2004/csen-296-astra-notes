"""EncryptionService — at-rest encryption for SecureNote bodies (FR-4 / SEC-1).

Authenticated symmetric encryption via Fernet (AES-128-CBC + HMAC-SHA256). The key is
derived from the user's passphrase with scrypt (a memory-hard KDF) using a per-note
random salt. Plaintext is never returned to or stored by the persistence layer.

NFR-2 / SEC-1: this module is on the View layer's import ban-list. Only services reach it.
"""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken

from ..errors import UnlockError

# Default scrypt parameters (also surfaced in settings.json). Memory-hard work factor.
DEFAULT_KDF = {"n": 32768, "r": 8, "p": 1}


class EncryptionService:
    def __init__(self, kdf_params: dict[str, int] | None = None) -> None:
        self._kdf = dict(kdf_params or DEFAULT_KDF)

    def new_salt(self) -> bytes:
        """A fresh 16-byte random salt for a new SecureNote."""
        return os.urandom(16)

    def derive_key(self, passphrase: str, salt: bytes) -> bytes:
        """Derive a urlsafe-base64 Fernet key from passphrase + salt via scrypt."""
        n, r, p = self._kdf["n"], self._kdf["r"], self._kdf["p"]
        # scrypt needs roughly 128 * n * r bytes; raise OpenSSL's default 32 MB cap so
        # the memory-hard params in settings.json (n=32768) are actually usable.
        maxmem = 128 * n * r * (p + 1) + (1 << 20)
        raw = hashlib.scrypt(
            passphrase.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=32,
            maxmem=maxmem,
        )
        return base64.urlsafe_b64encode(raw)

    def encrypt(self, plaintext: str, key: bytes) -> bytes:
        """Encrypt plaintext under a derived key; output is authenticated ciphertext."""
        return Fernet(key).encrypt(plaintext.encode("utf-8"))

    def decrypt(self, ciphertext: bytes, key: bytes) -> str:
        """Decrypt; raise UnlockError if the key is wrong or the data was tampered with."""
        try:
            return Fernet(key).decrypt(ciphertext).decode("utf-8")
        except InvalidToken as exc:
            raise UnlockError("Incorrect passphrase or corrupted note.") from exc

    @staticmethod
    def passphrase_fingerprint(passphrase: str, salt: bytes) -> bytes:
        """A non-reversible fingerprint stored for a cheap wrong-passphrase pre-check.

        This is *not* the encryption key and never derives one; real authentication is
        the Fernet auth tag on decrypt. SHA-256 over salt+passphrase.
        """
        return hashlib.sha256(salt + passphrase.encode("utf-8")).digest()
