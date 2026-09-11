"""Exotel client (H15) — the dumbphone lane: a caller explains their problem
to an IVR number; Dhaal listens, checks, and answers in spoken Hindi + SMS.

Contract with callers: never raise. Helpers return None/False on failure and
log a [latency] line; the IVR endpoints degrade gracefully (Exotel's flow
falls back to its static branch on a non-200 from us).

Env:
  EXOTEL_SID        — account SID (the subdomain part of my.exotel.com/<sid>)
  EXOTEL_API_KEY    — API key (basic-auth username)
  EXOTEL_API_TOKEN  — API token (basic-auth password)
  EXOTEL_SUBDOMAIN  — api.exotel.com (Mumbai) or api.in.exotel.com — per account
  EXOTEL_SMS_FROM   — the ExoPhone/sender to send result SMS from (optional)
"""

import os
import time

import httpx

_client = httpx.Client(timeout=httpx.Timeout(15.0, connect=5.0),
                       follow_redirects=True)


def _cfg():
    return (os.getenv("EXOTEL_SID", "").strip(),
            os.getenv("EXOTEL_API_KEY", "").strip(),
            os.getenv("EXOTEL_API_TOKEN", "").strip(),
            os.getenv("EXOTEL_SUBDOMAIN", "api.exotel.com").strip())


def available() -> bool:
    sid, key, token, _ = _cfg()
    return bool(sid and key and token)


_RECORDING_HOSTS = (".exotel.com", ".exotel.in")  # recordings live here, only here


def _recording_host_ok(url: str) -> bool:
    from urllib.parse import urlparse
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return bool(host) and any(host == h.lstrip(".") or host.endswith(h)
                              for h in _RECORDING_HOSTS)


def fetch_recording(url: str) -> tuple[bytes, str] | None:
    """Download a call recording. H15 hardening (external review): the URL is
    attacker-influencable webhook input, so (a) https only, (b) the host MUST
    be Exotel's own recording domain — this is not a generic fetcher and must
    never become an SSRF primitive, and (c) our basic-auth credentials are
    attached ONLY to that allow-listed host, never sprayed at arbitrary URLs.
    -> (bytes, content_type) or None."""
    if not url.lower().startswith("https://") or not _recording_host_ok(url):
        return None
    _, key, token, _ = _cfg()
    t0 = time.perf_counter()
    for auth in ((key, token) if key and token else None, None):
        try:
            r = _client.get(url, auth=auth)
            if r.status_code < 300 and r.content:
                ms = (time.perf_counter() - t0) * 1000
                print(f"[latency] exotel_recording_ms={ms:.0f} bytes={len(r.content)}")
                ctype = r.headers.get("content-type", "audio/mpeg").split(";")[0]
                return r.content, ctype
        except Exception as e:
            print(f"[latency] exotel_recording error={type(e).__name__}")
    return None


def send_sms(to: str, body: str) -> bool:
    """Result SMS so a dumbphone user keeps the guidance in hand."""
    sid, key, token, sub = _cfg()
    sender = os.getenv("EXOTEL_SMS_FROM", "").strip()
    if not (available() and sender and to):
        print("[latency] exotel_sms skipped=not_configured")
        return False
    t0 = time.perf_counter()
    try:
        r = _client.post(
            f"https://{sub}/v1/Accounts/{sid}/Sms/send.json",
            auth=(key, token),
            data={"From": sender, "To": to, "Body": body[:1000]},
        )
        ms = (time.perf_counter() - t0) * 1000
        print(f"[latency] exotel_sms_ms={ms:.0f} status={r.status_code}")
        return r.status_code < 300
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000
        print(f"[latency] exotel_sms_ms={ms:.0f} error={type(e).__name__}")
        return False
