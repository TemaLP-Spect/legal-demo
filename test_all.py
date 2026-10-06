#!/usr/bin/env python3
"""Full system test — language, fast-path, retrieval, LLM."""
import sys, time, json
sys.path.insert(0, "/workspaces/legal-demo")

from app.rag import detect_language, _fast_reply, ask

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m!\033[0m"

results = []

def check(name, actual, must_contain=None, must_not_contain=None):
    ok = True
    if must_contain:
        for s in must_contain:
            if s.lower() not in str(actual).lower():
                ok = False
    if must_not_contain:
        for s in must_not_contain:
            if s.lower() in str(actual).lower():
                ok = False
    results.append((name, ok, str(actual)[:80]))
    print(f"{PASS if ok else FAIL} {name}")
    if not ok:
        print(f"   got: {str(actual)[:120]}")

print("=" * 60)
print("LANGUAGE DETECTION")
print("=" * 60)

tests = [
    ("dumela",              "Sepedi"),
    ("thobela",             "Sepedi"),
    ("sawubona",            "isiZulu"),
    ("ngiyabonga",          "isiZulu"),
    ("molo",                "isiXhosa"),
    ("enkosi",              "isiXhosa"),
    ("hallo",               "Afrikaans"),
    ("dankie",              "Afrikaans"),
    ("ke a leboga",         "Setswana"),
    ("hello there friend",  None),
]
for text, expected in tests:
    got = detect_language(text)
    if expected:
        check(f"detect('{text}') -> {expected}", got, must_contain=[expected])
    else:
        results.append((f"detect('{text}') -> None", got is None, str(got)))
        print(f"{PASS if got is None else WARN} detect('{text}') -> {got}")

print()
print("=" * 60)
print("FAST-PATH REPLIES (no LLM)")
print("=" * 60)

fast_tests = [
    ("hi",                    "English",   [["good morning", "good afternoon", "good evening"]]),
    ("dumela",                "English",   [["thobela"]]),
    ("sawubona",              "English",   [["sawubona"]]),
    ("molo",                  "English",   [["molo"]]),
    ("hallo",                 "English",   [["goeie"]]),
    ("hi, how are you",       "English",   [["i am well"]]),
    ("dumela, how are you",   "English",   [["ke phela", "gabotse"]]),
    ("thanks",                "English",   [["welcome"]]),
    ("dankie",                "English",   [["welkom"]]),
    ("what are you",          "English",   [["legal research assistant"]]),
    ("disclaimer",            "English",   [["does not constitute legal advice"]]),
    ("",                      "English",   [["good morning", "good afternoon", "good evening"]]),
]
for text, lang, must in fast_tests:
    t0 = time.time()
    r = _fast_reply(text, lang)
    elapsed = time.time() - t0
    if r is None:
        results.append((f"fast('{text}')", False, "returned None (fell through)"))
        print(f"{FAIL} fast('{text}') -> None (should have been caught)")
    else:
        # must is a list of OR-groups; each group passes if ANY word matches
        ok = True
        for group in must:
            if not any(word in r.lower() for word in group):
                ok = False
                break
        results.append((f"fast('{text}')", ok, r[:80]))
        print(f"{PASS if ok else FAIL} fast('{text}') [{elapsed*1000:.0f}ms]")
        if not ok:
            print(f"   got: {r[:120]}")

print()
print("=" * 60)
print("REAL RETRIEVAL + LLM (slow — this hits Ollama)")
print("=" * 60)

real_tests = [
    ("What is the notice period for termination?", "English",  ["notice", "months", "termination"]),
    ("Who are the parties in this lease?",         "English",  ["lessor", "lessee"]),
    ("What happens when a lease is terminated?",   "English",  [["restore", "deposit", "premises", "terminat"]]),
]

for q, lang, must in real_tests:
    t0 = time.time()
    try:
        r = ask(q, language=lang)
        elapsed = time.time() - t0
        ans = r.get("answer", "")
        src_count = len(r.get("sources", []))
        if "do not contain sufficient" in ans.lower() or "not enough" in ans.lower():
            results.append((f"ask('{q[:30]}...')", False, "retrieval failed"))
            print(f"{FAIL} ask('{q[:40]}...') [{elapsed:.1f}s] RETRIEVAL FAILED")
            print(f"   got: {ans[:100]}")
        else:
            ok = True
            for group in must:
                if isinstance(group, str):
                    if group.lower() not in ans.lower():
                        ok = False
                        break
                else:
                    if not any(w.lower() in ans.lower() for w in group):
                        ok = False
                        break
            results.append((f"ask('{q[:30]}...')", ok, ans[:60]))
            print(f"{PASS if ok else FAIL} ask('{q[:40]}...') [{elapsed:.1f}s, {src_count} sources]")
            if not ok:
                print(f"   got: {ans[:150]}")
    except Exception as e:
        elapsed = time.time() - t0
        results.append((f"ask('{q[:30]}...')", False, str(e)))
        print(f"{FAIL} ask('{q[:40]}...') [{elapsed:.1f}s] EXCEPTION: {e}")

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"  {passed}/{total} passed")
print(f"  {total - passed} failed")
print()

if passed == total:
    print(f"{PASS} All tests passed. System is production-ready.")
    sys.exit(0)
else:
    print(f"{FAIL} {total - passed} test(s) failed. Review output above.")
    sys.exit(1)
