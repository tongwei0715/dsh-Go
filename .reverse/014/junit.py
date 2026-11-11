import sys
import xml.etree.ElementTree as ET

# Temporary helper for reverse-014: totals of this run's JUnit XML, named classes' cases, grouped class totals.
FULL = ["LogRedactorTest", "CrashClassifierTest", "RuntimeLogsTest", "PhoneSwitchDispatchTest"]
GROUPS = ["Failure", "SafeMode", "Lkg", "L2s", "Skill", "Update"]

files = sorted(sys.argv[1:])
print("R014: junit files=%d" % len(files))
tot = dict(suites=0, tests=0, failures=0, errors=0, skipped=0)
per = {}
cases = []
for f in files:
    root = ET.parse(f).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    for s in suites:
        tot["suites"] += 1
        for k in ("tests", "failures", "errors", "skipped"):
            tot[k] += int(s.get(k) or 0)
        for c in s.iter("testcase"):
            state = "pass"
            first = ""
            for kind in ("failure", "error", "skipped"):
                n = c.find(kind)
                if n is not None:
                    state = kind
                    txt = (n.get("message") or n.text or "").strip().splitlines()
                    first = txt[0] if txt else ""
                    break
            cls = (c.get("classname") or "").split(".")[-1]
            cases.append((cls, c.get("name"), state, first))
            p = per.setdefault(cls, dict(tests=0, failures=0, errors=0, skipped=0))
            p["tests"] += 1
            if state == "failure":
                p["failures"] += 1
            elif state == "error":
                p["errors"] += 1
            elif state == "skipped":
                p["skipped"] += 1
print("R014: total suites=%(suites)d tests=%(tests)d failures=%(failures)d errors=%(errors)d skipped=%(skipped)d" % tot)
for cls in FULL:
    p = per.get(cls)
    if p is None:
        print("R014: class %s NOT FOUND in XML" % cls)
        continue
    print("R014: class %s tests=%d failures=%d errors=%d skipped=%d" % (cls, p["tests"], p["failures"], p["errors"], p["skipped"]))
    for c, name, state, first in cases:
        if c == cls:
            print("R014: case %s.%s state=%s %s" % (c, name, state, first))
for g in GROUPS:
    names = sorted(c for c in per if g in c)
    t = sum(per[c]["tests"] for c in names)
    fl = sum(per[c]["failures"] + per[c]["errors"] for c in names)
    sk = sum(per[c]["skipped"] for c in names)
    print("R014: group *%s* classes=%s tests=%d failed=%d skipped=%d" % (g, ",".join(names), t, fl, sk))
print("R014: failing cases overall:")
for c, name, state, first in cases:
    if state in ("failure", "error"):
        print("R014: FAIL %s.%s state=%s %s" % (c, name, state, first))
