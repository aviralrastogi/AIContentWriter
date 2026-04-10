"""
Decrypt payloads produced by CryptoJS AES defaults:
OpenSSL salted format (Base64): "Salted__" + 8-byte salt + ciphertext (AES-CBC, PKCS7).

Compatible with:
  CryptoJS.AES.encrypt(plain, passphrase).toString()
"""

from __future__ import annotations

import base64
import hashlib
from typing import Final

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

_SALTED_PREFIX: Final[bytes] = b"Salted__"


def evp_bytes_to_key(password: bytes, salt: bytes, key_len: int, iv_len: int) -> tuple[bytes, bytes]:
    """OpenSSL EVP_BytesToKey (MD5, one block per iteration) — matches CryptoJS."""
    derived = b""
    prev = b""
    total = key_len + iv_len
    while len(derived) < total:
        prev = hashlib.md5(prev + password + salt).digest()
        derived += prev
    return derived[:key_len], derived[key_len : key_len + iv_len]


def decrypt_cryptojs_aes(ciphertext_b64: str, passphrase: str) -> str:
    """
    Decrypt a Base64 string from CryptoJS.AES.encrypt(...).toString().

    Raises:
        ValueError: bad format, wrong passphrase, or corrupt data.
    """
    if not passphrase:
        raise ValueError("Passphrase is required.")

    raw = base64.b64decode(ciphertext_b64.strip())
    if len(raw) < 16 or not raw.startswith(_SALTED_PREFIX):
        raise ValueError("Invalid ciphertext: expected CryptoJS OpenSSL salted format.")

    salt = raw[8:16]
    enc = raw[16:]
    if len(enc) % AES.block_size != 0:
        raise ValueError("Invalid ciphertext length.")

    key, iv = evp_bytes_to_key(passphrase.encode("utf-8"), salt, 32, 16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    try:
        plain = unpad(cipher.decrypt(enc), AES.block_size)
    except ValueError as exc:
        raise ValueError("Decryption failed (wrong passphrase or corrupted data).") from exc

    return plain.decode("utf-8")
