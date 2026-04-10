"""
Flask application factory — same behavior as FastAPI routes for teams that prefer WSGI.

Run from repo `backend` folder:

  pip install -r api/requirements.txt
  python -m flask --app api.flask_app:create_app run --host 127.0.0.1 --port 5000
"""

from __future__ import annotations

from flask import Blueprint, Flask, jsonify, request
from flask_cors import CORS
from pydantic import ValidationError

from .schemas import DecryptRequest, RewriteEncryptedRequest, RewritePlainRequest
from .services.content_pipeline import run_decrypt, run_rewrite_encrypted, run_rewrite_on_plain


def _bad(detail, code: int = 400):
    return jsonify({"detail": detail}), code


def _register_v1(bp: Blueprint) -> None:
    @bp.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "flask"})

    @bp.post("/crypto/decrypt")
    def decrypt_body():
        try:
            body = DecryptRequest.model_validate(request.get_json(force=True, silent=False) or {})
        except ValidationError as exc:
            return _bad(exc.errors(), 422)
        try:
            result = run_decrypt(body.ciphertext, body.passphrase)
        except ValueError as exc:
            return _bad(str(exc))
        return jsonify({"plaintext": result.plaintext})

    @bp.post("/content/rewrite")
    def rewrite_plain():
        try:
            body = RewritePlainRequest.model_validate(request.get_json(force=True, silent=False) or {})
        except ValidationError as exc:
            return _bad(exc.errors(), 422)
        result = run_rewrite_on_plain(body.text)
        return jsonify({"plaintext": result.plaintext, "source": result.source})

    @bp.post("/content/rewrite-encrypted")
    def rewrite_encrypted():
        try:
            body = RewriteEncryptedRequest.model_validate(request.get_json(force=True, silent=False) or {})
        except ValidationError as exc:
            return _bad(exc.errors(), 422)
        try:
            result = run_rewrite_encrypted(body.ciphertext, body.passphrase)
        except ValueError as exc:
            return _bad(str(exc))
        return jsonify({"plaintext": result.plaintext, "source": result.source})


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    v1 = Blueprint("v1", __name__, url_prefix="/v1")
    _register_v1(v1)
    app.register_blueprint(v1)

    @app.get("/health")
    def root_health():
        return jsonify({"status": "ok", "service": "flask", "hint": "versioned routes under /v1"})

    return app
