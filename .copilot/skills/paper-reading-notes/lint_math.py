#!/usr/bin/env python3
"""Lint a paper_reading_notes markdown file for GitHub math-rendering hazards.

Usage:
    python3 lint_math.py "<note>.md"

GitHub renders `$...$` inline and `$$...$$` display math (MathJax), but the
inline `$` delimiters are fragile. This linter catches the failures that have
actually broken notes in practice:

  * unbalanced `$` or `$$`
  * a `$$` display block not isolated by blank lines
  * `\\ ` (backslash-space) or similar fragile TeX inside inline `$...$`
  * an inline `$` delimiter *glued* to a parenthesis/bracket/alphanumeric
    (GitHub flanking rule): `($x$)` and `word$x$` do NOT render
  * an inline formula that spans a line break (shows up as an odd `$` count)

Exit code 0 = clean, 1 = hazards found, 2 = usage error.
"""
import re
import sys


def lint(path):
    src = open(path, encoding="utf-8").read()
    issues = []

    if src.count("$$") % 2:
        issues.append(f"odd $$ count: {src.count('$$')} (display delimiters unbalanced)")

    for i, line in enumerate(src.splitlines(), 1):
        if "\\ " in line:
            issues.append(f"L{i}: '\\ ' (backslash-space) inside math breaks the $ delimiter")

    # remove display blocks (may span lines) before checking inline math
    stripped = re.sub(r"\$\$.*?\$\$", "D", src, flags=re.S)
    for i, line in enumerate(stripped.splitlines(), 1):
        if line.count("$") % 2:
            issues.append(
                f"L{i}: odd inline $ count ({line.count('$')}) — unbalanced or spans a line break"
            )
        for m in re.finditer(r"\$([^$\n]+)\$", line):
            s, e = m.start(), m.end()
            before = line[s - 1] if s > 0 else ""
            after = line[e] if e < len(line) else ""
            body = m.group(1)
            if body[0] == " ":
                issues.append(f"L{i}: opening $ followed by a space")
            if body[-1] == " ":
                issues.append(f"L{i}: closing $ preceded by a space")
            if before and (before.isalnum() or before in "(["):
                issues.append(
                    f"L{i}: opening $ glued to '{before}' (add a space) -> {before}${body[:16]}$"
                )
            if after and (after.isalnum() or after in ")]"):
                issues.append(
                    f"L{i}: closing $ glued to '{after}' (add a space) -> ${body[-16:]}${after}"
                )

    for m in re.finditer(r"\$\$.*?\$\$", src, flags=re.S):
        pre, post = src[: m.start()], src[m.end():]
        if pre and not pre.endswith("\n\n") and pre.rstrip(" \t") and not pre.endswith("\n"):
            issues.append("a $$ display block is not preceded by a blank line")
        if post and not post.startswith("\n"):
            issues.append("a $$ display block is not followed by a newline")

    return issues


def main():
    if len(sys.argv) < 2:
        print("usage: python3 lint_math.py '<note>.md'")
        return 2
    problems = lint(sys.argv[1])
    if not problems:
        print("OK: clean — no GitHub math hazards")
        return 0
    print("MATH HAZARDS:")
    for p in problems:
        print(" -", p)
    return 1


if __name__ == "__main__":
    sys.exit(main())
