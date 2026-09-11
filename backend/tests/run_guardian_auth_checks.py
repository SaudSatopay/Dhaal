"""Guardian authorization suite (H14) — every bypass path from the external
security review, exercised against an ISOLATED in-memory store (no Atlas, no
keys, no production data):
    cd backend && python tests/run_guardian_auth_checks.py

The old model let anyone with a request id read link_id and decide for a
family. The new model must make request-id + everything publicly obtainable
insufficient, separate ward from guardian authority, and kill legacy pairings.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

for var in ("MONGODB_URI", "ANTHROPIC_API_KEY", "SARVAM_API_KEY"):
    os.environ[var] = ""
os.environ["MOCK_MODE"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

os.environ["MOD_KEY"] = ""
c = TestClient(main.app)
P = 0


def ok(name, cond, detail=""):
    global P
    print(("ok  " if cond else "FAIL"), name, detail if not cond else "")
    if not cond:
        sys.exit(f"FAILED: {name} {detail}")
    P += 1


def gh(tok):
    return {"X-Guardian-Token": tok}


def wh(tok):
    return {"X-Ward-Token": tok}


# ---- pairing A: guardian creates, ward claims -------------------------------
a = c.post("/api/guardian/links", json={
    "ward_name": "Amma", "guardian_name": "Meera", "guardian_phone": "+919812300001"}).json()
ok("create returns guardian token once", a.get("guardian_token", "").startswith("dgt_"))
ok("create response carries no token hashes",
   "guardian_token_sha256" not in a and "ward_token_sha256" not in a)
ok("pair code format is high-entropy", len(a["pair_code"]) == len("DHAAL-") + 8)

cl = c.post("/api/guardian/links/claim", json={"pair_code": a["pair_code"]}).json()
ok("claim returns ward token once", cl.get("ward_token", "").startswith("dwt_"))
ok("claim gives ward the trusted phone, not guardian credentials",
   cl.get("guardian_phone") == "+919812300001" and "guardian_token" not in cl
   and "pair_code" not in cl)

reuse = c.post("/api/guardian/links/claim", json={"pair_code": a["pair_code"]})
ok("pair code is single-use", reuse.status_code == 409)

# ward submits a risky check -> guardian request created
chk = c.post("/api/check", json={
    "type": "text", "payload": "आपका SBI खाता 24 घंटे में बंद हो जाएगा। तुरंत KYC करें: http://sbi-kyc-update.xyz",
    "ward_token": cl["ward_token"]}).json()
rid = chk.get("guardian_request_id")
ok("ward check reaches guardian inbox", bool(rid) and chk["guardian_delivery"] == "sent")

# ---- the published bypass, step by step -------------------------------------
r_anon = c.get(f"/api/guardian/requests/{rid}")
ok("BYPASS STEP 1 dead: unauthenticated request read -> 401", r_anon.status_code == 401)

r_ward = c.get(f"/api/guardian/requests/{rid}", headers=wh(cl["ward_token"]))
ok("ward may read own request status", r_ward.status_code == 200)
ok("BYPASS STEP 2 dead: no link_id/credential in any request view",
   "link_id" not in r_ward.json() and "guardian_token" not in r_ward.json())

d_anon = c.post(f"/api/guardian/requests/{rid}/decision",
                json={"decision": "blocked", "note": "x"})
ok("no credentials -> cannot decide", d_anon.status_code == 401)

d_ward = c.post(f"/api/guardian/requests/{rid}/decision",
                json={"decision": "blocked", "note": "x"}, headers=wh(cl["ward_token"]))
ok("ward credentials -> cannot decide", d_ward.status_code == 401)

d_linkid = c.post(f"/api/guardian/requests/{rid}/decision",
                  json={"decision": "blocked", "note": "x", "link_id": a["link_id"]})
ok("request id + link_id (old bypass payload) -> still cannot decide",
   d_linkid.status_code == 401)

inbox_anon = c.get("/api/guardian/requests")
ok("inbox listing requires guardian token", inbox_anon.status_code == 401)
inbox_qs = c.get(f"/api/guardian/requests?link_id={a['link_id']}")
ok("inbox never trusts a link_id query param", inbox_qs.status_code == 401)

# ---- cross-pairing isolation ------------------------------------------------
b = c.post("/api/guardian/links", json={
    "ward_name": "Kaka", "guardian_name": "Ravi", "guardian_phone": ""}).json()
d_cross = c.post(f"/api/guardian/requests/{rid}/decision",
                 json={"decision": "allowed"}, headers=gh(b["guardian_token"]))
ok("guardian B cannot decide for pairing A (404, existence hidden)",
   d_cross.status_code == 404)
r_cross = c.get(f"/api/guardian/requests/{rid}", headers=gh(b["guardian_token"]))
ok("guardian B cannot read pairing A's request", r_cross.status_code == 404)
inbox_b = c.get("/api/guardian/requests", headers=gh(b["guardian_token"])).json()
ok("guardian B inbox does not contain A's requests",
   all(r["_id"] != rid for r in inbox_b["requests"]))

# ---- the right guardian works ----------------------------------------------
d_good = c.post(f"/api/guardian/requests/{rid}/decision",
                json={"decision": "blocked", "note": "ruk ja"},
                headers=gh(a["guardian_token"]))
ok("correct guardian CAN decide", d_good.status_code == 200
   and d_good.json()["status"] == "blocked")
ok("decision response reports durability", "durable" in d_good.json())
inbox_a = c.get("/api/guardian/requests", headers=gh(a["guardian_token"])).json()
ok("guardian A sees the decided request",
   any(r["_id"] == rid and r["status"] == "blocked" for r in inbox_a["requests"]))

# ---- invitation lifecycle ---------------------------------------------------
bad = c.post("/api/guardian/links/claim", json={"pair_code": "DHAAL-ZZZZZZZZ"})
ok("unknown code -> 404", bad.status_code == 404)

expired = c.post("/api/guardian/links", json={"ward_name": "W", "guardian_name": "G"}).json()
main.STORE.update("guardian_links", expired["link_id"],
                  {"pair_code_expires_at": "2020-01-01T00:00:00+00:00"})
e = c.post("/api/guardian/links/claim", json={"pair_code": expired["pair_code"]})
ok("expired code -> 410", e.status_code == 410)

legacy_resolve = c.get("/api/guardian/links/resolve?pair_code=DHAAL-1234")
ok("legacy resolve endpoint is dead (410, no data)", legacy_resolve.status_code == 410
   and "_id" not in legacy_resolve.json())

# legacy pre-token link (as exists in old data): no hashes stored -> nothing works
legacy = {"_id": "gl_legacy1", "ward_name": "Old", "guardian_name": "Older",
          "pair_code": "DHAAL-AB12", "created_at": "2026-09-11T00:00:00+00:00"}
main.STORE.insert("guardian_links", legacy)
lc = c.post("/api/guardian/links/claim", json={"pair_code": "DHAAL-AB12"})
ok("legacy (no-expiry) pair code cannot be claimed", lc.status_code == 410)
chk_legacy = c.post("/api/check", json={
    "type": "text", "payload": "kal milte hain bhai", "ward_link_id": "gl_legacy1"}).json()
ok("legacy ward_link_id no longer reaches an inbox (no silent migration)",
   chk_legacy.get("guardian_delivery") == "unlinked"
   and "guardian_request_id" not in chk_legacy)

# ---- revocation -------------------------------------------------------------
rv_anon = c.post("/api/guardian/links/revoke", json={})
ok("revoke requires a pairing token", rv_anon.status_code == 401)
rv = c.post("/api/guardian/links/revoke", json={"reason": "phone lost"},
            headers=wh(cl["ward_token"]))
ok("ward can revoke own pairing (consent both ways)", rv.status_code == 200)
d_after = c.post(f"/api/guardian/requests/{rid}/decision",
                 json={"decision": "allowed"}, headers=gh(a["guardian_token"]))
ok("revoked pairing: guardian token stops working", d_after.status_code == 401)
chk_after = c.post("/api/check", json={
    "type": "text", "payload": "aaj match dekhna hai kya", "ward_token": cl["ward_token"]}).json()
ok("revoked pairing: ward token stops working",
   chk_after.get("guardian_delivery") == "unlinked")

# ---- clean ward check lands as 'noted', unassessed as 'noted' ---------------
c2 = c.post("/api/guardian/links", json={"ward_name": "N", "guardian_name": "M"}).json()
cl2 = c.post("/api/guardian/links/claim", json={"pair_code": c2["pair_code"]}).json()
clean = c.post("/api/check", json={"type": "text",
                                   "payload": "Bhai kal match ke tickets book kar liye, tera hissa 850 hua, jab time mile bhej dena.",
                                   "ward_token": cl2["ward_token"]}).json()
nc = c.post("/api/check", json={"type": "text", "payload": "9812345678",
                                "ward_token": cl2["ward_token"]}).json()
inbox2 = c.get("/api/guardian/requests", headers=gh(c2["guardian_token"])).json()
st = {r["check_id"]: r["status"] for r in inbox2["requests"]}
ok("clean ward check -> noted (no false alarm to family)",
   st.get(clean["_id"]) == "noted")
ok("needs-context ward check -> noted, never a pending decision",
   st.get(nc["_id"]) == "noted")

print(f"\nALL {P} GUARDIAN AUTH CHECKS PASSED")
