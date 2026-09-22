"""Version check and update logic."""

from __future__ import annotations

import configparser
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

from logger import logger

__root__ = Path(__file__).parent.parent.parent


def get_local_version() -> str:
    """Try to read version from setup.cfg [metadata] section. Fallback to 0.0.0."""
    cfg = configparser.ConfigParser()
    try:
        setup_cfg = Path(__root__) / 'setup.cfg'
        if setup_cfg.exists():
            cfg.read(setup_cfg)
            if cfg.has_section('metadata') and cfg.has_option('metadata', 'version'):
                return cfg.get('metadata', 'version').strip()
    except Exception:
        pass
    return '0.0.0'


def _get_git_origin_remote() -> Optional[str]:
    """Return origin remote URL or None."""
    try:
        out = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'], cwd=str(__root__), stderr=subprocess.DEVNULL)
        url = out.decode().strip()
        return url
    except Exception:
        return None


def _parse_github_owner_repo(remote_url: str) -> Optional[Tuple[str, str]]:
    """Parse GitHub owner and repo from remote URL.
    Supports HTTPS and SSH forms.
    """
    if not remote_url:
        return None
    m = re.search(r'github.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)', remote_url)
    if m:
        return m.group('owner'), m.group('repo')
    return None


def get_remote_latest_version() -> Optional[str]:
    """Query GitHub API for the latest version.
    
    Flow:
    - Try /releases/latest and use tag_name/name if available.
    - Fallback to /tags and pick the highest semantic version-like tag.
    Authenticated requests are used when GITHUB_TOKEN or GH_TOKEN env var is present.
    """
    def _headers() -> dict:
        headers = {'User-Agent': 'ai-breadboard-version-check'}
        token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN') or os.getenv('GITHUB_API_TOKEN')
        if token:
            headers['Authorization'] = f'token {token}'
        return headers

    try:
        remote = _get_git_origin_remote()
        if not remote:
            return None
        parsed = _parse_github_owner_repo(remote)
        if not parsed:
            return None
        owner, repo = parsed

        # Try releases/latest first
        try:
            url = f'https://api.github.com/repos/{owner}/{repo}/releases/latest'
            req = urllib.request.Request(url, headers=_headers())
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.load(resp)
                tag = data.get('tag_name') or data.get('name')
                if tag:
                    return tag
        except Exception:
            pass

        # Fallback: get tags and pick the highest semver-like tag
        try:
            url = f'https://api.github.com/repos/{owner}/{repo}/tags'
            req = urllib.request.Request(url, headers=_headers())
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.load(resp)
                tags = [t.get('name') for t in data if t.get('name')]
                if not tags:
                    return None

                debug_enabled = os.getenv('VERSION_CHECK_DEBUG') == '1'
                if debug_enabled:
                    logger.debug(f'Remote tags from API: {tags}')

                allow_prerelease = str(os.getenv('ALLOW_PRERELEASE') or '').lower() in ('1', 'true', 'yes')

                best = _choose_best_tag(tags, allow_prerelease=bool(allow_prerelease), debug=bool(debug_enabled))
                if debug_enabled:
                    logger.debug(f'Selected tag: {best} (allow_prerelease={allow_prerelease})')
                return best
        except Exception:
            pass

        # Last-resort fallback: git ls-remote --tags origin
        try:
            out = subprocess.check_output(['git', 'ls-remote', '--tags', 'origin'], cwd=str(__root__), stderr=subprocess.DEVNULL)
            lines = out.decode().splitlines()
            tags = []
            for line in lines:
                parts = line.split('\t')
                if len(parts) < 2:
                    continue
                ref = parts[1]
                if ref.startswith('refs/tags/'):
                    tag = ref[len('refs/tags/'):]
                    tag = tag.replace('^{}', '')
                    tags.append(tag)
            if not tags:
                return None

            debug_enabled = os.getenv('VERSION_CHECK_DEBUG') == '1'
            if debug_enabled:
                logger.debug(f'Remote tags from ls-remote: {tags}')

            allow_prerelease = str(os.getenv('ALLOW_PRERELEASE') or '').lower() in ('1', 'true', 'yes')

            best = _choose_best_tag(tags, allow_prerelease=bool(allow_prerelease), debug=bool(debug_enabled))
            if debug_enabled:
                logger.debug(f'Selected tag from ls-remote: {best} (allow_prerelease={allow_prerelease})')
            return best
        except Exception:
            return None
    except Exception:
        return None


def _choose_best_tag(tags: list[str], allow_prerelease: bool = False, debug: bool = False) -> str:
    """Choose the best tag from a list of semantic version-like tags."""
    def _parse_version(v: str) -> list[int]:
        if not v:
            return [0, 0, 0]
        parts = re.findall(r"(\d+)", v)
        return [int(p) for p in parts]
    
    def _is_prerelease(tag: str) -> bool:
        return any(x in tag.lower() for x in ('alpha', 'beta', 'rc', 'dev', 'pre'))
    
    # Filter out prerelease tags if not allowed
    if not allow_prerelease:
        tags = [t for t in tags if not _is_prerelease(t)]
    
    if not tags:
        return '0.0.0'
    
    # Sort by version
    tagged_versions = [(t, _parse_version(t)) for t in tags]
    tagged_versions.sort(key=lambda x: x[1], reverse=True)
    
    if debug:
        logger.debug(f'Sorted tags: {[t[0] for t in tagged_versions]}')
    
    return tagged_versions[0][0]


def _is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def check_updates() -> dict:
    """Check if a newer version is available.
    
    Returns:
        dict: Check result with keys:
            - status: 'ok', 'error', or 'up_to_date'
            - current_version: local version
            - remote_version: latest remote version (if available)
            - is_update_available: bool
            - message: optional message
    """
    try:
        from src.utils.versioning import compare_versions as _compare_versions
        
        local_v = get_local_version()
        remote_v = get_remote_latest_version()
        
        if not remote_v:
            return {
                'status': 'error',
                'current_version': local_v,
                'is_update_available': False,
                'message': 'Could not determine remote version'
            }
        
        cmp = _compare_versions(local_v, remote_v)
        
        if cmp >= 0:
            return {
                'status': 'up_to_date',
                'current_version': local_v,
                'remote_version': remote_v,
                'is_update_available': False,
                'message': f'Application is up-to-date: {local_v}'
            }
        
        return {
            'status': 'ok',
            'current_version': local_v,
            'remote_version': remote_v,
            'is_update_available': True,
            'message': f'A newer version is available: {remote_v}'
        }
    except Exception as e:
        return {
            'status': 'error',
            'current_version': get_local_version(),
            'is_update_available': False,
            'message': f'Failed to check updates: {e}'
        }


def prompt_and_perform_update(branch: str = 'main') -> bool:
    """If a newer remote version exists, prompt the user and, on consent, run git pull --ff-only.
    
    Returns:
        bool: True if update was performed, False otherwise.
    """
    try:
        auto_update_env = os.getenv('AUTO_UPDATE') or os.getenv('ai-breadboard_AUTO_UPDATE')
        auto_update = str(auto_update_env or '').lower() in ('1', 'true', 'yes')
        
        if not _is_interactive() and not auto_update:
            logger.debug('Non-interactive shell and AUTO_UPDATE not enabled: skipping version check')
            return False

        check_result = check_updates()
        if check_result.get('status') == 'error':
            logger.warning(f"Version check failed: {check_result.get('message')}")
            return False
        
        if not check_result.get('is_update_available'):
            logger.info(f"Application is up-to-date: {check_result.get('current_version')}")
            return False

        current = check_result.get('current_version', 'unknown')
        remote = check_result.get('remote_version', 'unknown')
        logger.info(f'A newer version is available: {remote} (current: {current})')

        do_update = auto_update
        if not do_update:
            try:
                resp = input(
                    f'Доступно update {remote} (текущая версия {current}). '
                    'Обновить код и перезагрузиться? [y/N]: '
                ).strip().lower()
                do_update = resp in ('y', 'yes')
            except Exception:
                do_update = False

        if not do_update:
            logger.info('User declined update or update not approved')
            return False

        # Execute update
        logger.info(f'Starting update from {current} to {remote}...')
        
        try:
            subprocess.check_call(['git', 'fetch', 'origin', branch], cwd=str(__root__))
            subprocess.check_call(['git', 'merge', '--ff-only', f'origin/{branch}'], cwd=str(__root__))
            logger.info('Update pulled successfully.')
            logger.success(f'Update completed: {current} → {remote}')
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f'Failed to update repository: {e}')
            return False
            
    except Exception as e:
        logger.error(f'Error during version check/update: {e}')
        return False
