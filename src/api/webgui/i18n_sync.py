#!/usr/bin/env python3
"""Utility to auto‑extract hardcoded Russian strings from the web GUI
and inject them into locale JSON files (ru.json, en.json, he.json).
It also rewrites HTML files, wrapping the literals with a <span data-i18n="...">
so that the UI becomes fully internationalised.

The script follows these steps:
1. Load existing locale files from `src/api/webgui/locales/`.
2. Scan all `.html` and `.js` files under `src/api/webgui/` for Cyrillic text.
3. For each found literal that is not already referenced via `data-i18n` or
   `i18n.t(...)`, generate a deterministic key based on a slug of the text.
4. Insert the key/value pair into `ru.json` (value = original Russian text).
   Insert empty placeholder strings into `en.json` and `he.json` if the key is new.
5. Rewrite the source file, replacing the literal with a `<span data-i18n="key"></span>`
   in HTML, or with `i18n.t('key')` in JavaScript (simple string context).

The script is safe to run repeatedly – it will not duplicate keys.
"""
import os, json, re, hashlib, pathlib

ROOT = pathlib.Path(__file__).resolve().parent  # project root (webgui directory)
LOCALES_DIR = ROOT / "locales"

def load_locale(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_locale(data, file_path):
    # Keep formatting compact but sorted for readability
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)

def slugify(text):
    # Create a deterministic short key from the Russian text
    base = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip()).lower()
    # Append hash to avoid collisions for long strings
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:6]
    return f"auto_{base}_{h}" if base else f"auto_{h}"

def is_inside_data_i18n(line, start, end):
    # Simple heuristic: check if the match is within a data-i18n attribute value
    prefix = line[:start]
    return "data-i18n" in prefix

def process_html(filepath, ru, en, he):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    # Regex for Cyrillic sequences of length >=2 (exclude HTML tags)
    pattern = re.compile(r"([\u0400-\u04FF][^<>]*[\u0400-\u04FF])")
    changed = False
    def repl(m):
        nonlocal changed
        start, end = m.span()
        # Skip if already inside a data-i18n attribute
        if is_inside_data_i18n(content, start, end):
            return m.group(0)
        russian = m.group(1).strip()
        key = slugify(russian)
        # Update locales if new key
        if key not in ru:
            ru[key] = russian
            en[key] = ""
            he[key] = ""
            changed = True
        # Replace with span wrapper
        new = f"<span data-i18n=\"{key}\"></span>"
        return new
    new_content = pattern.sub(repl, content)
    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
    return changed

def process_js(filepath, ru, en, he):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    # Find string literals containing Cyrillic: "..." or '...'
    pattern = re.compile(r"(['\"])(?P<txt>[^'\"]*[\u0400-\u04FF][^'\"]*)\1")
    changed = False
    def repl(m):
        nonlocal changed
        txt = m.group('txt')
        if txt.startswith('i18n.t('):
            return m.group(0)
        key = slugify(txt)
        if key not in ru:
            ru[key] = txt
            en[key] = ""
            he[key] = ""
            changed = True
        # Replace literal with i18n.t('key')
        return f"i18n.t('{key}')"
    new_content = pattern.sub(repl, content)
    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
    return changed

def main():
    ru_path = LOCALES_DIR / "ru.json"
    en_path = LOCALES_DIR / "en.json"
    he_path = LOCALES_DIR / "he.json"
    ru = load_locale(ru_path)
    en = load_locale(en_path)
    he = load_locale(he_path)
    # Walk through files
    for root, _, files in os.walk(ROOT):
        for name in files:
            if name.endswith('.html'):
                process_html(pathlib.Path(root) / name, ru, en, he)
            elif name.endswith('.js'):
                process_js(pathlib.Path(root) / name, ru, en, he)
    # Save updated locales
    save_locale(ru, ru_path)
    save_locale(en, en_path)
    save_locale(he, he_path)

if __name__ == "__main__":
    main()
