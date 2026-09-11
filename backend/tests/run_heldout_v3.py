# Held-out battery v3 — the cases were authored BLIND by a separate session
# (backend/tests/heldout_v3_cases.json) that never read the engine, while the
# engine was rewritten without reading the cases. This runner executes ONCE
# against PROD at the freeze commit; results publish unedited.
#
# Grading (pre-declared):
#   predicted class = "flag"        if assessment==assessed and verdict!=no_known_risk
#                     "clean"       if assessment==assessed and verdict==no_known_risk
#                     "context"     if assessment==needs_context
#                     "unsupported" if assessment==unsupported_input
#   expected  class = flag | clean (from expect_risk) | context | unsupported
#   pass = predicted == expected. No partial credit; labels are never edited
#   to make the implementation pass.
import json
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API = "https://dhaal-api.vercel.app/api/check"
HERE = Path(__file__).resolve()
CASES_F = HERE.parent / "heldout_v3_cases.json"
OUT = HERE.parents[2] / "docs" / "heldout_v3.json"

EXPECTED_CLASS = {
    ("assessed", "flag"): "flag",
    ("assessed", "clean"): "clean",
    ("needs_context", None): "context",
    ("unsupported_input", None): "unsupported",
}


def predicted_class(d: dict) -> str:
    a = d.get("assessment")
    if a == "needs_context":
        return "context"
    if a == "unsupported_input":
        return "unsupported"
    if a == "assessed":
        return "clean" if d.get("verdict") == "no_known_risk" else "flag"
    return "error"


def call(case: dict) -> dict:
    body = json.dumps({
        "type": {"qr": "qr_text"}.get(case["type"], case["type"]),
        "payload": case["payload"], "lang": "hi-IN",
        "expected_intent": case.get("expected_intent"),
    }).encode()
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


def main():
    spec = json.loads(CASES_F.read_text(encoding="utf-8"))
    cases = spec["cases"]
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True,
                            cwd=HERE.parents[2]).stdout.strip()
    rows, t0 = [], time.time()
    for i, case in enumerate(cases, 1):
        exp = EXPECTED_CLASS.get((case["expect_assessment"], case["expect_risk"]))
        d = call(case)
        pred = "error" if "error" in d else predicted_class(d)
        p = pred == exp
        rows.append({
            **{k: case.get(k) for k in ("id", "lang", "type", "payload",
                                        "expected_intent", "expect_assessment",
                                        "expect_risk", "rationale")},
            "expected_class": exp, "predicted_class": pred,
            "assessment": d.get("assessment"), "verdict": d.get("verdict"),
            "score": d.get("score"),
            "signals": [s["id"] for s in d.get("signals", [])],
            "community_data": d.get("community_data"),
            "engine_ms": (d.get("timings") or {}).get("engine_ms"),
            "error": d.get("error"), "pass": p,
        })
        print(f"[{i:2}/{len(cases)}] {case['id']} {case['lang']:8} "
              f"exp={exp:11} got={pred:11} {'ok' if p else 'MISS'}")

    # ---- metrics (pre-declared) ----
    conf = Counter((r["expected_class"], r["predicted_class"]) for r in rows)
    by = lambda cls: [r for r in rows if r["expected_class"] == cls]
    hit = lambda rs: sum(r["pass"] for r in rs)
    flags, cleans = by("flag"), by("clean")
    flag_pred = [r for r in rows if r["predicted_class"] == "flag"]
    danger_pred = [r for r in rows if r["verdict"] == "danger"]
    metrics = {
        "recall_on_flag": f"{hit(flags)}/{len(flags)}",
        "false_warning_rate_on_clean":
            f"{sum(1 for r in cleans if r['predicted_class'] == 'flag')}/{len(cleans)}",
        "strong_warning_precision(danger)":
            f"{sum(1 for r in danger_pred if r['expected_class'] == 'flag')}"
            f"/{len(danger_pred)}",
        "flag_precision(any warning)":
            f"{sum(1 for r in flag_pred if r['expected_class'] == 'flag')}"
            f"/{len(flag_pred)}",
        "abstention_on_assessable":
            f"{sum(1 for r in flags + cleans if r['predicted_class'] in ('context', 'unsupported'))}"
            f"/{len(flags) + len(cleans)}",
        "context_handling": f"{hit(by('context'))}/{len(by('context'))}",
        "unsupported_handling": f"{hit(by('unsupported'))}/{len(by('unsupported'))}",
    }
    per_lang = {}
    for lg in ("hi", "en", "hinglish"):
        sub = [r for r in rows if r["lang"] == lg]
        if sub:
            per_lang[lg] = f"{hit(sub)}/{len(sub)}"

    summary = {
        "battery": "heldout_v3", "authored_blind_by_separate_session": True,
        "run_at": "2026-09-11", "target": API, "engine_commit": commit,
        "runs": 1, "community_data_enabled": rows[0].get("community_data"),
        "llm_narration": "enabled (zero verdict weight)",
        "total": f"{hit(rows)}/{len(rows)}",
        "metrics": metrics, "per_language": per_lang,
        "confusion_matrix": {f"{e}->{p}": n for (e, p), n in sorted(conf.items())},
        "seconds": round(time.time() - t0),
    }
    OUT.write_text(json.dumps({"summary": summary, "cases": rows},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n== HELD-OUT v3 (blind-authored, single run, unedited) ==")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nraw -> {OUT}")
    misses = [r for r in rows if not r["pass"]]
    if misses:
        print(f"\nmisses ({len(misses)}):")
        for r in misses:
            print(f"  {r['id']} exp={r['expected_class']} got={r['predicted_class']} "
                  f"v={r['verdict']} {r['score']} {r['signals']} :: {r['payload'][:70]}")


if __name__ == "__main__":
    main()
