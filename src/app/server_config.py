"""Server configuration and startup utilities."""

from __future__ import annotations

import sys
from pathlib import Path

from src.config import server_cfg
from src.logger import logger

__root__ = Path(__file__).parent.parent


def get_server_config():
    """Get server configuration."""
    port: int = int(getattr(server_cfg, "port", 8000))
    if not port:
        logger.error('Port not configured')
        sys.exit(1)

    _ssl_cfg = getattr(server_cfg, 'ssl', None)
    _cert_str = (getattr(_ssl_cfg, 'cert', '') or '').strip() if _ssl_cfg else ''
    _key_str = (getattr(_ssl_cfg, 'key', '') or '').strip() if _ssl_cfg else ''
    _cert_str = _cert_str or os.getenv('SSL_CERT_FILE', '').strip()
    _key_str = _key_str or os.getenv('SSL_KEY_FILE', '').strip()
    _default_certs = Path.home() / '.certs'
    cert_file = Path(_cert_str).expanduser() if _cert_str else _default_certs / 'localhost+2.pem'
    key_file = Path(_key_str).expanduser() if _key_str else _default_certs / 'localhost+2-key.pem'

    use_ssl = getattr(server_cfg, "use_ssl", True)
    host = getattr(server_cfg, "host", "0.0.0.0")
    reload = bool(getattr(server_cfg, "reload", True))

    ssl_kwargs = {}
    if use_ssl and cert_file.exists() and key_file.exists():
        ssl_kwargs = {'ssl_certfile': str(cert_file), 'ssl_keyfile': str(key_file)}
        logger.info(f'Server starting https://{host}:{port} (SSL enabled)')
    else:
        logger.warning('Starting without HTTPS (SSL disabled or certificates not found)')
        logger.info(f'Запуск сервера http://{host}:{port}')

    logger.info(f"Uvicorn autoreload: {'ON' if reload else 'OFF'}")
    
    return {
        'host': host,
        'port': port,
        'reload': reload,
        'ssl_kwargs': ssl_kwargs,
        'branch': str(os.getenv('GIT_BRANCH', 'main'))
    }


def run_server(app):
    """Run the FastAPI server with configured settings."""
    import uvicorn
    
    config = get_server_config()
    uvicorn.run('main:app', host=config['host'], port=config['port'], 
                reload=config['reload'], **config['ssl_kwargs'])
