"""Seed the Dhaal backend with realistic community-intel data — Glue lane (Saud).

Posts reports via the public API and verifies them, building the blocklist and
trends exactly the way real usage would. Works against local or deployed backend.
NOTE: against the serverless deployment the data lives only until a cold start —
durable once Harsh wires MONGODB_URI (then re-run this once).

Usage:
    python scripts/seed.py                                  # localhost:8000, 200 reports
    python scripts/seed.py --base https://dhaal-api.vercel.app --reports 200
    python scripts/seed.py --flywheel-only                  # just the 43-report demo number
"""
import argparse
import random
import sys

import httpx

# demo-safe fake indicators (clearly not real people)
FLYWHEEL_PHONE = "+919876500001"  # must match backend/fixtures.py BLOCKLISTED_PHONE
FLYWHEEL_COUNT = 43

CATEGORY_WEIGHTS = {
    "kyc_expiry": 58, "fake_collect": 41, "digital_arrest": 33,
    "electricity": 26, "lottery": 22, "olx_army": 18, "customer_care": 14,
}
CITY_WEIGHTS = {"Jaipur": 84, "Jodhpur": 47, "Udaipur": 38, "Kota": 24, "Ajmer": 19}

PAYLOAD_MAKERS = {
    "kyc_expiry": lambda i: f"http://kyc-verify-{i}.xyz/update",
    "fake_collect": lambda i: f"refund{i}.support@okpay{i % 7}",
    "digital_arrest": lambda i: f"+9198765{10000 + i}",
    "electricity": lambda i: f"http://bijli-bill-pay{i}.top/now",
    "lottery": lambda i: f"http://kbc-lucky-winner{i}.online/claim",
    "olx_army": lambda i: f"+9187654{20000 + i}",
    "customer_care": lambda i: f"+9176543{30000 + i}",
}
NOTES = [
    "SMS aya tha, link kholte hi bank jaisa page khula",
    "Call karke bola account band ho jayega",
    "QR bheja bola scan karo refund milega",
    "WhatsApp par message aya tha",
    "Pehle 10 rupay maange fir 15000 kat gaye",
]


def weighted_choices(weights: dict, k: int) -> list:
    keys, w = list(weights.keys()), list(weights.values())
    return random.choices(keys, weights=w, k=k)


def post_and_verify(client: httpx.Client, base: str, payload: str, category: str, city: str, note: str) -> bool:
    r = client.post(f"{base}/api/reports", json={
        "payload": payload, "category": category, "note": note, "city": city,
    })
    if r.status_code != 200 or "_id" not in r.json():
        return False
    rid = r.json()["_id"]
    v = client.post(f"{base}/api/reports/{rid}/verify", json={"action": "verify"})
    return v.status_code == 200


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--reports", type=int, default=200)
    ap.add_argument("--flywheel-only", action="store_true")
    args = ap.parse_args()
    base = args.base.rstrip("/")
    random.seed(4)  # deterministic demo data

    with httpx.Client(timeout=30) as client:
        health = client.get(f"{base}/api/health").json()
        print(f"target {base} · store={health.get('store')} · mock={health.get('mock_mode')}")

        ok = 0
        print(f"flywheel number {FLYWHEEL_PHONE} × {FLYWHEEL_COUNT} verified reports…")
        for _ in range(FLYWHEEL_COUNT):
            ok += post_and_verify(client, base, FLYWHEEL_PHONE, "digital_arrest",
                                  "Jaipur", "Fake police call, parcel scam")
        print(f"  done ({ok} verified)")

        if not args.flywheel_only:
            cats = weighted_choices(CATEGORY_WEIGHTS, args.reports)
            cities = weighted_choices(CITY_WEIGHTS, args.reports)
            ok2 = 0
            for i, (cat, city) in enumerate(zip(cats, cities)):
                ok2 += post_and_verify(client, base, PAYLOAD_MAKERS[cat](i), cat,
                                       city, random.choice(NOTES))
            print(f"intel reports: {ok2}/{args.reports} verified")

        trends = client.get(f"{base}/api/intel/trends").json()
        print(f"trends now: total={trends.get('total_reports')} live={trends.get('live_reports')} "
              f"top={[t['value'] for t in trends.get('top_indicators', [])[:3]]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
