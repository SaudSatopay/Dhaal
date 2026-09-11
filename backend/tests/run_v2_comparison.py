# Before/after comparison: the held-out v2 set (published unedited at 51/60
# against commit aa7f715) re-run against the NEW engine on the SAME frozen
# dataset. NOT independent evidence for the new engine — its misses were
# development inputs for H14 — which is exactly why it is reported as a
# comparison, separately from the blind v3 battery.
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from run_heldout_v2 import API, CASES  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "docs" / "heldout_v2_on_new_engine.json"


def call(case):
    cid, expect, typ, intent, payload = case
    body = json.dumps({"type": typ, "payload": payload, "lang": "hi",
                       "expected_intent": intent}).encode()
    req = urllib.request.Request(API, data=body,
                                 headers={"Content-Type": "application/json"})
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 2:
                return {"error": str(e)}
            time.sleep(3)


def grade(expect, d):
    """v2's own pre-declared grading, mapped onto the H14 contract:
    flag  -> assessed danger/suspicious
    clean -> assessed no_known_risk
    context -> needs_context assessment (v2 predates unsupported_input)."""
    if "error" in d:
        return False
    a, v = d.get("assessment"), d.get("verdict")
    if expect == "flag":
        return a == "assessed" and v in ("danger", "suspicious")
    if expect == "clean":
        return a == "assessed" and v == "no_known_risk"
    return a in ("needs_context", "unsupported_input")


rows = []
for i, case in enumerate(CASES, 1):
    cid, expect, typ, intent, payload = case
    d = call(case)
    p = grade(expect, d)
    rows.append({"id": cid, "expect": expect, "assessment": d.get("assessment"),
                 "verdict": d.get("verdict"), "score": d.get("score"),
                 "signals": [s["id"] for s in d.get("signals", [])],
                 "error": d.get("error"), "pass": p})
    print(f"[{i:2}/60] {cid} {expect:7} -> {d.get('assessment')}/{d.get('verdict')} "
          f"{'ok' if p else 'MISS'}")

n = lambda e: [r for r in rows if r["expect"] == e]
hit = lambda rs: sum(r["pass"] for r in rs)
summary = {
    "comparison": "heldout_v2 set on NEW engine (NOT independent — v2 misses fed H14 development)",
    "old_engine_published": {"commit": "aa7f715", "total": "51/60",
                             "scam": "24/30", "benign_clean": "21/24",
                             "insufficient": "6/6"},
    "new_engine": {"total": f"{hit(rows)}/60", "scam": f"{hit(n('flag'))}/30",
                   "benign_clean": f"{hit(n('clean'))}/24",
                   "insufficient": f"{hit(n('context'))}/6"},
}
OUT.write_text(json.dumps({"summary": summary, "cases": rows},
                          ensure_ascii=False, indent=1), encoding="utf-8")
print("\n== V2 SET COMPARISON (old vs new engine) ==")
print(json.dumps(summary, indent=2))
misses = [r for r in rows if not r["pass"]]
if misses:
    print(f"\nnew-engine misses on v2 set ({len(misses)}):")
    for r in misses:
        print(f"  {r['id']} [{r['expect']}] {r['assessment']}/{r['verdict']} {r['signals']}")
