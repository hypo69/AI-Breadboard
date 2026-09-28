import pathlib, re, sys
base = pathlib.Path('c:\\\\Users\\\\onela\\\\AppData\\\\Local\\\\AI-Breadboard')
patterns = [(re.compile('from\\s+src\\.logger\\.logger\\s+import\\s+logger'), 'from logger import logger'), (re.compile('from\\s+src\\.logger\\s+import\\s+logger'), 'from logger import logger'), (re.compile('import\\s+src\\.logger\\.logger'), 'from logger import logger'), (re.compile('import\\s+src\\.logger'), 'import logger')]
changed = []
for path in base.rglob('*.py'):
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        continue
    original = text
    for pat, repl in patterns:
        text = pat.sub(repl, text)
    if text != original:
        path.write_text(text, encoding='utf-8')
        changed.append(str(path))
print('Updated files:')
for f in changed:
    print(f)