"""Byte comparison of two replays' records; the order sender's deal references (a random part by design) are
replaced by their order of first appearance, nothing else is changed."""
import json, re, sys
a, b = (json.load(open(p)) for p in sys.argv[1:3])
REF = re.compile(r"\b[A-Z]{1,4}\d{12}-[0-9a-f]{8}\b")
def norm(files):
    seen = {}
    def sub(m):
        return seen.setdefault(m.group(0), f"REF{len(seen) + 1}")
    return {k: [REF.sub(sub, line) for line in v] for k, v in files.items()}
na, nb = norm(a), norm(b)
same = True
for k in sorted(set(na) | set(nb)):
    x, y = na.get(k), nb.get(k)
    if x == y:
        print(f"identical  {k}  ({len(x)} lines)")
    else:
        same = False
        print(f"DIFFERENT  {k}  ({len(x or [])} vs {len(y or [])} lines)")
        for i, (l1, l2) in enumerate(zip(x or [], y or [])):
            if l1 != l2:
                print("   first difference at line", i + 1); print("   A:", l1[:300]); print("   B:", l2[:300]); break
print("BYTE-IDENTICAL (deal references normalised)" if same else "NOT IDENTICAL")
sys.exit(0 if same else 1)
