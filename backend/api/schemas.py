from __future__ import annotations

from pydantic import BaseModel, Field


class DecryptRequest(BaseModel):
    ciphertext: str = Field(..., min_length=1, description="CryptoJS.AES.encrypt(...).toString() output")
    passphrase: str = Field(..., min_length=1)


class DecryptResponse(BaseModel):
    plaintext: str


class RewritePlainRequest(BaseModel):
    text: str = Field(..., description="Plain UTF-8 body to rewrite")


class RewriteEncryptedRequest(BaseModel):
    ciphertext: str = Field(..., min_length=1)
    passphrase: str = Field(..., min_length=1)


class RewriteResponse(BaseModel):
    plaintext: str
    source: str = Field(..., description="'plain' or 'decrypted'")


class HealthResponse(BaseModel):
    status: str
    service: str
