# Evaluation battery v4 (H16 §9) — 110 cases authored BLIND by a separate
# session (developer-authored; NO human validation; labels+rationales frozen
# at authoring, before this runner ever executed). Runs LOCALLY against the
# app via TestClient with external services STUBBED OFF (no LLM narration, no
# TTS, no network; community blocklist = seeded fixtures only) — the verdict
# path is fully deterministic, so this measures the engine, not the mood of
# an API. Failures are preserved verbatim; tuning against this set afterwards
# reclassifies it as development/regression data (note it in docs/EVAL.md).
#
# Grading (pre-declared, same contract as v3):
#   predicted = flag|clean (assessed) · context (needs_context)
#               · unsupported (unsupported_input)
#   pass = predicted class == expected class. No partial credit.
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

for var in ("MONGODB_URI", "ANTHROPIC_API_KEY", "SARVAM_API_KEY",
            "META_APP_SECRET", "WA_ACCESS_TOKEN"):
    os.environ[var] = ""
os.environ["MOCK_MODE"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

os.environ["MOD_KEY"] = ""
c = TestClient(main.app)

HERE = Path(__file__).resolve()
CASES_F = HERE.parent / "heldout_v4_cases.json"
OUT = HERE.parents[2] / "docs" / "heldout_v4.json"

EXPECTED = {("assessed", "flag"): "flag", ("assessed", "clean"): "clean",
            ("needs_context", None): "context",
            ("unsupported_input", None): "unsupported"}


def predicted(d: dict) -> str:
    a = d.get("assessment")
    if a == "needs_context":
        return "context"
    if a == "unsupported_input":
        return "unsupported"
    if a == "assessed":
        return "clean" if d.get("verdict") == "no_known_risk" else "flag"
    return "error"


def scenario(case: dict) -> str:
    rat = case.get("rationale", "").lower()
    for key, words in [
        ("extortion", ("extort", "blackmail", "sextort", "expose", "humiliat")),
        ("advance_fee", ("advance", "fee", "loan", "prize", "refund", "disburs")),
        ("credential", ("otp", "credential", "password", "pin", "code")),
        ("impersonation", ("imperson", "lookalike", "brand", "family", "relative", "new number")),
        ("intent_qr", ("qr", "intent", "collect", "payment request")),
        ("awareness", ("news", "aware", "educat", "report", "discuss", "explain")),
        ("negation", ("negat", "no fee", "do not send")),
    ]:
        if any(w in rat for w in words):
            return key
    return "other"


def main_():
    spec = json.loads(CASES_F.read_text(encoding="utf-8"))
    cases = spec["cases"]
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True,
                            cwd=HERE.parents[2]).stdout.strip()
    rows, t0 = [], time.time()
    for i, case in enumerate(cases, 1):
        exp = EXPECTED.get((case["expect_assessment"], case["expect_risk"]))
        body = {"type": {"qr": "qr_text"}.get(case["type"], case["type"]),
                "payload": case["payload"], "lang": "hi-IN", "fast": True,
                "expected_intent": case.get("expected_intent")}
        d = c.post("/api/check", json=body).json()
        pred = predicted(d)
        p = pred == exp
        rows.append({**{k: case.get(k) for k in
                        ("id", "lang", "type", "payload", "expected_intent",
                         "expect_assessment", "expect_risk", "pair_of",
                         "rationale")},
                     "expected_class": exp, "predicted_class": pred,
                     "assessment": d.get("assessment"),
                     "verdict": d.get("verdict"), "score": d.get("score"),
                     "signals": [s["id"] for s in d.get("signals", [])],
                     "scenario": scenario(case), "pass": p})
        print(f"[{i:3}/110] {case['id']} {case['lang']:8} exp={exp:11} "
              f"got={pred:11} {'ok' if p else 'MISS'}")

    conf = Counter((r["expected_class"], r["predicted_class"]) for r in rows)
    by = lambda cls: [r for r in rows if r["expected_class"] == cls]
    hit = lambda rs: sum(r["pass"] for r in rs)
    flags, cleans = by("flag"), by("clean")
    danger_rows = [r for r in rows if r["verdict"] == "danger"]
    per_lang = {lg: f"{hit([r for r in rows if r['lang'] == lg])}"
                    f"/{len([r for r in rows if r['lang'] == lg])}"
                for lg in ("hi", "en", "hinglish")}
    per_scn = {}
    for r in rows:
        per_scn.setdefault(r["scenario"], [0, 0])
        per_scn[r["scenario"]][1] += 1
        per_scn[r["scenario"]][0] += int(r["pass"])
    pairs = {}
    for r in rows:
        if r.get("pair_of"):
            key = "::".join(sorted([r["id"], r["pair_of"]]))
            pairs.setdefault(key, []).append(r["pass"])
    pair_both = sum(1 for v in pairs.values() if len(v) == 2 and all(v))

    summary = {
        "battery": "v4",
        "authorship": spec.get("authorship", "developer-authored"),
        "labels_frozen_before_run": True, "runs": 1,
        "engine_commit": commit, "environment": "local TestClient",
        "external_services": "STUBBED OFF (no LLM narration, no TTS, no network; "
                             "community blocklist = seeded fixtures only)",
        "total": f"{hit(rows)}/110",
        "metrics": {
            "harmful_recall": f"{hit(flags)}/{len(flags)}",
            "legit_false_positive": f"{sum(1 for r in cleans if r['predicted_class'] == 'flag')}/{len(cleans)}",
            "danger_precision": f"{sum(1 for r in danger_rows if r['expected_class'] == 'flag')}/{len(danger_rows)}",
            "uncertainty_handling": f"{hit(by('context'))}/{len(by('context'))}",
            "unsupported_handling": f"{hit(by('unsupported'))}/{len(by('unsupported'))}",
            "false_reassurance_on_context": f"{sum(1 for r in by('context') if r['predicted_class'] == 'clean')}/{len(by('context'))}",
        },
        "per_language": per_lang,
        "per_scenario": {k: f"{v[0]}/{v[1]}" for k, v in sorted(per_scn.items())},
        "pairs": {"total": len(pairs), "both_members_correct": pair_both},
        "confusion_matrix": {f"{e}->{p}": n for (e, p), n in sorted(conf.items())},
        "seconds": round(time.time() - t0),
    }
    OUT.write_text(json.dumps({"summary": summary, "cases": rows},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n== BATTERY v4 (developer-authored blind; single local run; unedited) ==")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    misses = [r for r in rows if not r["pass"]]
    print(f"\nmisses ({len(misses)}):")
    for r in misses:
        print(f"  {r['id']} [{r['scenario']}] exp={r['expected_class']} "
              f"got={r['predicted_class']} v={r['verdict']} {r['score']} "
              f"{r['signals'][:4]} :: {r['payload'][:70]}")
    print(f"\nraw -> {OUT}")


if __name__ == "__main__":
    main_()
