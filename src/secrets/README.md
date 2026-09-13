# src/secrets — Secret Keys Directory

This directory stores **private credential files** that must **never** be committed to version control.

The entire `src/secrets/` directory is listed in `.gitignore` (only this `README.md` is tracked).

---

## Required Files

Place the following files here according to the instructions below. Do not rename them unless you update the corresponding loader in `src/secrets/`.

### `gemini_keys.json`
Pool of Google Gemini API keys for automatic rotation.

```json
[
  {"name": "key1", "api_key": "AIza..."},
  {"name": "key2", "api_key": "AIza..."}
]
```

### `google_accounts.json`
Google OAuth account pool (optional, used for Drive sync and Google Workspace integration).

```json
[
  {
    "account": "user@gmail.com",
    "token": "ya29...",
    "refresh_token": "1//...",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "...",
    "client_secret": "..."
  }
]
```

### `client_secret_*.json`
Google OAuth 2.0 client credentials (downloaded from Google Cloud Console).

1. Go to [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create or download an existing **OAuth 2.0 Client ID** (type: Web application)
3. Place the downloaded JSON file here as-is (filename starts with `client_secret_`)

---

## SSL Certificates

SSL certificates are **not** stored here. Configure SSL paths via `config.json` (`server.ssl.cert` / `server.ssl.key`) or environment variables:

```env
SSL_CERT_FILE=~/.certs/localhost+2.pem
SSL_KEY_FILE=~/.certs/localhost+2-key.pem
```

To generate local dev certificates, use [mkcert](https://github.com/FiloSottile/mkcert):

```powershell
mkcert -install
mkcert localhost 127.0.0.1 ::1
```

---

## Security Notes

- **Never** commit real credentials to Git
- **Never** share these files publicly
- All files in this directory (except `README.md`) are automatically excluded by `.gitignore`
- Rotate API keys if you suspect they have been exposed
