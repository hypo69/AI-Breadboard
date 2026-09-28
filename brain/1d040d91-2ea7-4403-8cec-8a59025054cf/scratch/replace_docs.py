import pathlib, re
base = pathlib.Path('c:\\\\Users\\\\onela\\\\AppData\\\\Local\\\\AI-Breadboard\\\\docs')
patterns = [(re.compile('src\\.logger\\.logger'), 'logger'), (re.compile('src\\.logger'), 'logger')]
changed = []
for path in base.rglob('*.md'):
    text = path.read_text(encoding='utf-8', errors='ignore')
    original = text
    for pat, repl in patterns:
        text = pat.sub(repl, text)
    if text != original:
        path.write_text(text, encoding='utf-8')
        changed.append(str(path))
print('Updated docs:')
for f in changed:
    print(f)