# src/secrets — Secret Keys Directory

This directory stores **private credential files** that must **never** be committed to version control.

The entire `src/secrets/` directory is listed in `.gitignore` (only this `README.md` is tracked).

---

## Directory Structure

```text
src/secrets/
├── gemini_keys.json         # Pool of Google Gemini API keys
├── google_ouath_files/      # Google OAuth client secrets & credentials
│   └── <user>_secret.json   # OAuth 2.0 client credentials for user (e.g. davidka_secret.json)
└── google_oauth_tokens/     # Saved Google OAuth user tokens
    └── <user>_token.json    # Cached user authentication tokens (e.g. davidka_token.json)
```

---

## File Naming Conventions

- **Credentials / Secrets:** Saved in `src/secrets/google_ouath_files/<user>_secret.json` where `<user>` is the username received from input.
- **OAuth Tokens:** Saved in `src/secrets/google_oauth_tokens/<user>_token.json` where `<user>` is the username received from input.
- **Gemini Keys:** Maintained in `src/secrets/gemini_keys.json`.

---

## Required Files

### `gemini_keys.json`
Pool of Google Gemini API keys for automatic rotation.

```json
[
  {"name": "key1", "api_key": "AIza..."},
  {"name": "key2", "api_key": "AIza..."}
]
```

### `google_ouath_files/<user>_secret.json`
Google OAuth 2.0 client credentials (downloaded from Google Cloud Console or provided via setup).

```json
{
  "installed": {
    "client_id": "...",
    "project_id": "...",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "...",
    "redirect_uris": ["http://localhost"]
  }
}
```

### `google_oauth_tokens/<user>_token.json`
OAuth 2.0 tokens (access token, refresh token, expiry) generated during authorization.

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
