# docs

MkDocs-based documentation site for AI Breadboard.

## Structure

```
docs/
├── ru/              — Russian documentation (primary)
│   ├── index.md     — Project overview and quick navigation
│   ├── ARCHITECTURE.md — Cross-platform architecture description
│   ├── ported.md    — Porting summary
│   ├── cook-book/   — 8-chapter practical guide on AI model prototyping
│   └── code/        — Module and CLI reference
├── en/              — English documentation
│   ├── index.md
│   ├── cook-book/   — English edition of the practical guide
│   ├── code/        — CLI and engine startup reference
│   ├── developer/   — Developer guide
│   ├── tester/      — Testing guide
│   └── user/        — End-user guide
├── assets/          — Images and diagrams
├── stylesheets/     — Custom MkDocs CSS
└── changelog.md     — Project changelog
```

## Building the docs

```bash
pip install -r requirements-docs.txt
mkdocs serve          # local preview at http://127.0.0.1:8000
mkdocs build          # static site output to site/
```

## Language policy

- `docs/ru/` — Russian only (canonical documentation)
- `docs/en/` — English only
- All new documentation pages must be placed in the appropriate language subdirectory
