"""Meta WhatsApp Cloud API client (H15) — the successor to the parked Twilio
sandbox: the Cloud API test number allows custom webhooks on the free tier.

Contract with callers: never raise. send_text returns True/False; failures
log a [latency] line and the caller records the outcome. Replies here are
"service" messages inside Meta's 24-hour customer-service window (we only
ever reply to an inbound user message, so no template approval is needed).

Env:
  WA_ACCESS_TOKEN     — system-user / temporary token from the Meta app
  WA_PHONE_NUMBER_ID  — the *Phone number ID* (numeric), NOT the phone number
  META_APP_SECRET     — app secret; enables X-Hub-Signature-256 validation
  WA_VERIFY_TOKEN     — any string we choose; echoed in the GET handshake
"""

import hashlib
import hmac
import os
import time

import httpx

GRAPH = "https://graph.facebook.com/v21.0"
_client = httpx.Client(timeout=httpx.Timeout(8.0, connect=4.0))


def configured() -> bool:
    return bool(os.getenv("WA_ACCESS_TOKEN", "").strip()
                and os.getenv("WA_PHONE_NUMBER_ID", "").strip())


def verify_signature(raw_body: bytes, header: str) -> bool:
    """X-Hub-Signature-256: 'sha256=' + HMAC-SHA256(app_secret, raw body).
    No secret configured -> treated as valid (local/test); the webhook route
    decides policy. Meta signs every delivery, so prod sets the secret."""
    secret = os.getenv("META_APP_SECRET", "").strip()
    if not secret:
        return True
    if not header.startswith("sha256="):
        return False
    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, header[len("sha256="):])


def send_text(to_wa_id: str, body: str) -> int:
    """POST /{phone_number_id}/messages — plain text reply to a user.
    Returns the HTTP status so the outbox can classify: 2xx sent · 4xx
    (not 429) permanent/config · 429/5xx transient · 0 = transport error or
    TIMEOUT. A timeout is AMBIGUOUS — the message may or may not have been
    delivered; the outbox retries, which makes delivery at-least-once (a rare
    duplicate reply is the accepted cost of never silently dropping one)."""
    if not configured():
        print("[latency] wa_send skipped=not_configured")
        return 503  # config missing — retryable once env is fixed
    t0 = time.perf_counter()
    try:
        r = _client.post(
            f"{GRAPH}/{os.getenv('WA_PHONE_NUMBER_ID').strip()}/messages",
            headers={"Authorization": f"Bearer {os.getenv('WA_ACCESS_TOKEN').strip()}"},
            json={"messaging_product": "whatsapp", "to": to_wa_id,
                  "type": "text", "text": {"preview_url": False,
                                           "body": body[:4000]}},
        )
        ms = (time.perf_counter() - t0) * 1000
        # never log message bodies or tokens — status + latency only
        print(f"[latency] wa_send_ms={ms:.0f} status={r.status_code}")
        return r.status_code
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000
        print(f"[latency] wa_send_ms={ms:.0f} error={type(e).__name__}")
        return 0


def mark_read(message_id: str) -> None:
    """Best-effort read receipt — the ✓✓ turns blue while we compute."""
    if not configured():
        return
    try:
        _client.post(
            f"{GRAPH}/{os.getenv('WA_PHONE_NUMBER_ID').strip()}/messages",
            headers={"Authorization": f"Bearer {os.getenv('WA_ACCESS_TOKEN').strip()}"},
            json={"messaging_product": "whatsapp", "status": "read",
                  "message_id": message_id},
        )
    except Exception:
        pass
