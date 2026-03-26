import hmac
import hashlib
import base64

from app.config import Config


def verify_signature(body, signature):
    digest = hmac.new(
        Config.LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected_signature, signature or "")