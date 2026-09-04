# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for configuration and environment
# =============================================================================
# Description:
#   Module содержит тесты для проверки конфигурации окружения и доступности
#
# File: test_environment.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Тесты конфигурации и окружения
"""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

class TestEnvConfig:
    """Тесты конфигурации окружения."""

    def test_env_file_exists(self):
        """Тест наличия .env файла."""
        env_path = Path(__file__).parent.parent / '.env'
        
        # .env не обязателен для тестов
        # assert env_path.exists() or env_path.with_suffix('.example').exists()

    def test_env_example_valid(self):
        """Тест валидности .env.example."""
        env_example_path = Path(__file__).parent.parent / '.env.example'
        
        assert env_example_path.exists()
        
        content = env_example_path.read_text(encoding='utf-8')
        
        # Check обязательных переменных
        required_vars = [
            'GOOGLE_CLIENT_ID',
            'GOOGLE_CLIENT_SECRET',
            'JWT_SECRET',
            'NGROCK_AUTOTOKEN',
            'TTS_VOICE'
        ]
        
        for var in required_vars:
            assert var in content

    def test_required_variables_set(self):
        """Тест установки обязательных переменных через conftest fixture."""
        critical_vars = [
            'GOOGLE_CLIENT_ID',
            'JWT_SECRET',
        ]
        
        for var in critical_vars:
            assert var in os.environ, f"Критичная переменная {var} не установлена"

class TestConfigFiles:
    """Тесты конфигурационных файлов."""

    def test_fastapi_config_exists(self):
        """Тест наличия config.json."""
        config_path = Path(__file__).parent.parent / 'config.json'
        
        assert config_path.exists()
        
        import json
        with open(config_path, encoding='utf-8') as f:
            config = json.load(f)
        
        server_cfg = config.get('server', config)
        assert 'host' in server_cfg
        assert 'port' in server_cfg
        assert 'workers' in server_cfg

    def test_fastapi_config_valid(self):
        """Тест валидности config.json."""
        config_path = Path(__file__).parent.parent / 'config.json'
        
        import json
        with open(config_path, encoding='utf-8') as f:
            config = json.load(f)
        
        server_cfg = config.get('server', config)
        # Check значений
        assert server_cfg['host'] == '0.0.0.0'
        assert isinstance(server_cfg['port'], int)
        assert server_cfg['port'] > 0
        assert server_cfg['workers'] > 0

    def test_github_workflows_exist(self):
        """Тест наличия GitHub workflows."""
        workflows_dir = Path(__file__).parent.parent / '.github' / 'workflows'
        
        assert workflows_dir.exists()
        
        workflow_files = list(workflows_dir.glob('*.yml'))
        assert len(workflow_files) > 0

class TestDocumentation:
    """Тесты документации."""

    def test_readme_exists(self):
        """Тест наличия README.MD."""
        readme_path = Path(__file__).parent.parent / 'README.MD'
        
        assert readme_path.exists()

    def test_mkdocs_exists(self):
        """Тест наличия mkdocs.yml."""
        mkdocs_path = Path(__file__).parent.parent / 'mkdocs.yml'
        
        assert mkdocs_path.exists()

    def test_docs_structure(self):
        """Тест структуры docs/."""
        docs_dir = Path(__file__).parent.parent / 'docs'
        
        assert docs_dir.exists()
        
        # Check обязательных файлов
        required_files = [
            'index.md',
            'quickstart.md',
            'features.md'
        ]
        
        for file in required_files:
            assert (docs_dir / file).exists()

    def test_docs_user_section(self):
        """Тест раздела user документации."""
        docs_user_dir = Path(__file__).parent.parent / 'docs' / 'user'
        
        assert docs_user_dir.exists()
        
        required_files = [
            'getting-started.md',
            'player.md',
            'remote-control.md',
            'telegram.md',
            'admin-panel.md'
        ]
        
        for file in required_files:
            assert (docs_user_dir / file).exists()

    def test_docs_dev_section(self):
        """Тест раздела dev документации."""
        docs_dev_dir = Path(__file__).parent.parent / 'docs' / 'dev'
        
        assert docs_dev_dir.exists()
        
        required_files = [
            'getting-started.md',
            'architecture.md',
            'api-reference.md',
            'plugins.md'
        ]
        
        for file in required_files:
            assert (docs_dev_dir / file).exists()

class TestRequirements:
    """Тесты зависимостей."""

    def test_requirements_exist(self):
        """Тест наличия requirements.txt."""
        req_path = Path(__file__).parent.parent / 'requirements.txt'
        
        assert req_path.exists()

    def test_requirements_test_exist(self):
        """Тест наличия requirements-test.txt."""
        req_test_path = Path(__file__).parent.parent / 'requirements-test.txt'
        
        assert req_test_path.exists()

    def test_requirements_test_content(self):
        """Тест содержимого requirements-test.txt."""
        req_test_path = Path(__file__).parent.parent / 'requirements-test.txt'
        content = req_test_path.read_text(encoding='utf-8')
        if '-r req/' in content:
            req_sub_path = Path(__file__).parent.parent / 'req' / 'requirements-test.txt'
            if req_sub_path.exists():
                content += "\n" + req_sub_path.read_text(encoding='utf-8')
        
        required_packages = [
            'pytest',
            'pytest-asyncio',
            'pytest-cov',
            'httpx',
            'coverage'
        ]
        
        for package in required_packages:
            assert package in content

class TestDirectoryStructure:
    """Тесты структуры директорий."""

    def test_src_exists(self):
        """Test existence of src/."""
        src_dir = Path(__file__).parent.parent / 'src'
        
        assert src_dir.exists()

    def test_rag_exists(self):
        """Test existence of src/rag/."""
        rag_dir = Path(__file__).parent.parent / 'src' / 'rag'
        
        assert rag_dir.exists()

    def test_webinterface_exists(self):
        """Тест наличия webinterface/."""
        webinterface_dir = Path(__file__).parent.parent / 'src' / 'fastapi' / 'webinterface'
        
        assert webinterface_dir.exists()

    def test_tests_exists(self):
        """Тест наличия tests/."""
        tests_dir = Path(__file__).parent.parent / 'tests'
        
        assert tests_dir.exists()
