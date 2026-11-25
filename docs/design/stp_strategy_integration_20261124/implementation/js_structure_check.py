"""A structural check only (not a JavaScript parser): strings, template literals (with ${...}), comments and regex
literals skipped; (), [], {} must balance and every string/comment/template must end."""
import re, sys
def scan(src, name):
    stack, i, n, line = [], 0, len(src), 1
    pairs = {")": "(", "]": "[", "}": "{"}
    prev = ""                         # last significant char, to tell a regex from a division
    tmpl = []                         # brace depth at each open template ${
    while i < n:
        ch = src[i]
        if ch == "\n": line += 1
        if src.startswith("//", i):
            j = src.find("\n", i); i = n if j < 0 else j; continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j < 0: return f"{name}: unterminated comment at line {line}"
            line += src.count("\n", i, j); i = j + 2; continue
        if ch in "'\"":
            j = i + 1
            while j < n and src[j] != ch:
                if src[j] == "\\": j += 1
                if src[j] == "\n": return f"{name}: unterminated string at line {line}"
                j += 1
            if j >= n: return f"{name}: unterminated string at line {line}"
            i = j + 1; prev = "a"; continue
        if ch == "`" or (ch == "}" and tmpl and len(stack) == tmpl[-1]):
            if ch == "}": tmpl.pop()
            j = i + 1
            while j < n and src[j] != "`":
                if src[j] == "\\": j += 1
                elif src.startswith("${", j):
                    tmpl.append(len(stack)); break
                if src[j] == "\n": line += 1
                j += 1
            if j >= n: return f"{name}: unterminated template at line {line}"
            i = j + (2 if src.startswith("${", j) else 1); prev = "a"; continue
        if ch == "/" and (prev in "(,=:[!&|?{};+-*%<>~^" or prev == "" or re.search(r"(return|typeof|case|in|of)\s*$", src[max(0, i-10):i])):
            j = i + 1; cls = False
            while j < n and (src[j] != "/" or cls):
                if src[j] == "\\": j += 1
                elif src[j] == "[": cls = True
                elif src[j] == "]": cls = False
                elif src[j] == "\n": return f"{name}: unterminated regex at line {line}"
                j += 1
            i = j + 1
            while i < n and src[i].isalpha(): i += 1
            prev = "a"; continue
        if ch in "([{": stack.append((ch, line))
        elif ch in ")]}":
            if not stack or stack[-1][0] != pairs[ch]: return f"{name}: unbalanced '{ch}' at line {line}"
            stack.pop()
        if not ch.isspace(): prev = ch if not (ch.isalnum() or ch in "_$") else "a"
        i += 1
    return f"{name}: unclosed '{stack[-1][0]}' from line {stack[-1][1]}" if stack else f"{name}: balanced ({line} lines)"
for path in sys.argv[1:]:
    text = open(path).read()
    if path.endswith(".html"):
        for k, m in enumerate(re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", text, re.S)):
            print(scan(m.group(1), f"{path} inline script {k + 1}"))
    else:
        print(scan(text, path))
