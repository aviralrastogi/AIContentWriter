"""
FastAPI application: versioning, OpenAPI tags, shared decrypt/rewrite pipeline.
Run from repo `backend` folder:

  pip install -r api/requirements.txt
  python -m uvicorn api.fastapi_app:app --host 127.0.0.1 --port 8000 --reload
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    DecryptRequest,
    DecryptResponse,
    HealthResponse,
    RewriteEncryptedRequest,
    RewritePlainRequest,
    RewriteResponse,
)
from .services.content_pipeline import run_decrypt, run_rewrite_encrypted, run_rewrite_on_plain


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Content Writer API",
        version="1.1.0",
        description="Decrypt CryptoJS AES payloads and run deterministic rewrite. "
        "Matches `CryptoJS.AES.encrypt(plain, passphrase).toString()` on the client.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse, tags=["meta"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="fastapi")

    @app.post(
        "/v1/crypto/decrypt",
        response_model=DecryptResponse,
        tags=["crypto"],
        summary="Decrypt CryptoJS OpenSSL salted ciphertext",
    )
    def decrypt_body(body: DecryptRequest) -> DecryptResponse:
        try:
            result = run_decrypt(body.ciphertext, body.passphrase)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return DecryptResponse(plaintext=result.plaintext)

    @app.post(
        "/v1/content/rewrite",
        response_model=RewriteResponse,
        tags=["content"],
        summary="Rewrite plain text (no decryption)",
    )
    def rewrite_plain(body: RewritePlainRequest) -> RewriteResponse:
        result = run_rewrite_on_plain(body.text)
        return RewriteResponse(plaintext=result.plaintext, source=result.source)

    @app.post(
        "/v1/content/rewrite-encrypted",
        response_model=RewriteResponse,
        tags=["content"],
        summary="Decrypt CryptoJS payload, then rewrite (plaintext never required client-side)",
    )
    def rewrite_encrypted(body: RewriteEncryptedRequest) -> RewriteResponse:
        try:
            result = run_rewrite_encrypted(body.ciphertext, body.passphrase)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return RewriteResponse(plaintext=result.plaintext, source=result.source)

    return app


app = create_app()
