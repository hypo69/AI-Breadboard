# 📖 System Log Patterns & Diagnostics Reference

This document outlines recognized logging formats, anomaly signatures, clustering heuristics, and remediation patterns for the `log-analyzer` skill.

---

## 🔍 Log Formats

### 1. Standard Plaintext Log
```text
2026-09-08 20:15:30 [ERROR] [src.ai.providers.gemini] Gemini API request failed: Rate limit exceeded (429)
2026-09-08 20:15:31 [INFO] [src.fastapi.server] Uvicorn running on http://127.0.0.1:8000
```

### 2. JSON Lines Structured Log
```json
{"timestamp": "2026-09-08T20:15:30Z", "level": "ERROR", "logger": "src.ai.gemini", "message": "Rate limit exceeded (429)", "exc_info": null}
```

---

## ⚡ Error Severity & Action Classification

| Level | Severity | Urgency | Action Required |
|---|---|---|---|
| `CRITICAL` | Highest | Immediate | Immediate restart, failover, or missing essential secrets (`.env`) |
| `ERROR` | High | High | Investigate exception traceback, network timeouts, or model errors |
| `WARNING` | Medium | Normal | Deprecated flags, non-fatal fallbacks, slow query thresholds |
| `INFO` / `DEBUG` | Low | Low | Normal operational lifecycle tracking |

---

## 🧬 Heuristic Signature Normalization

To avoid noisy duplicate reports, errors are normalized using regex masks:
- Hex memory pointers (`0x7ffc82a1`) $\rightarrow$ `0x...`
- UUID identifiers $\rightarrow$ `<UUID>`
- Port and process IDs $\rightarrow$ `<N>`
- Traceback tail extraction: `Last line of traceback + First line of message`
