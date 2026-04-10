from __future__ import annotations

from dataclasses import dataclass

from ..cryptojs_compat import decrypt_cryptojs_aes
from .rewrite_engine import rewrite_text


@dataclass(frozen=True)
class DecryptResult:
    plaintext: str


@dataclass(frozen=True)
class RewriteResult:
    plaintext: str
    source: str  # "plain" | "decrypted"


def run_decrypt(ciphertext: str, passphrase: str) -> DecryptResult:
    return DecryptResult(plaintext=decrypt_cryptojs_aes(ciphertext, passphrase))


def run_rewrite_on_plain(plain_text: str) -> RewriteResult:
    return RewriteResult(plaintext=rewrite_text(plain_text), source="plain")


def run_rewrite_encrypted(ciphertext: str, passphrase: str) -> RewriteResult:
    plain = decrypt_cryptojs_aes(ciphertext, passphrase)
    return RewriteResult(plaintext=rewrite_text(plain), source="decrypted")
