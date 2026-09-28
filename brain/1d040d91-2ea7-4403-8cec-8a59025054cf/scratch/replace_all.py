import pathlib, re, sys

base = pathlib.Path(r"c:\\Users\\onela\\AppData\\Local\\AI-Breadboard")
patterns = [
    # import statements
    (re.compile(r"from\\s+src\\.logger\\.logger\\s+import\\s+logger"), "from logger import logger"),
    (re.compile(r"from\\s+src\\.logger\\s+import\\s+logger"), "from logger import logger"),
    (re.compile(r"import\\s+src\\.logger\\.logger"), "from logger import logger"),
    (re.compile(r"import\\s+src\\.logger"), "import logger"),
    # usage
    (re.compile(r"src\\.logger\\.logger"), "logger"),
    (re.compile(r"src\\.logger"), "logger"),
]
changed = []
for path in base.rglob("*.py"):
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # skip binary or non‑utf8 files
        continue
    original = text
    for pat, repl in patterns:
        text = pat.sub(repl, text)
    if text != original:
        path.write_text(text, encoding="utf-8")
        changed.append(str(path))

print("Python files updated:")
for f in changed:
    print(f)

# Update markdown documentation
md_patterns = [
    (re.compile(r"src\\.logger\\.logger"), "logger"),
    (re.compile(r"src\\.logger"), "logger"),
]
md_changed = []
for md_path in base.rglob("*.md"):
    try:
        md_text = md_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    original_md = md_text
    for pat, repl in md_patterns:
        md_text = pat.sub(repl, md_text)
    if md_text != original_md:
        md_path.write_text(md_text, encoding="utf-8")
        md_changed.append(str(md_path))

print("Markdown files updated:")
for f in md_changed:
    print(f)
