import io
import json
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from main import app
from src.user_manager import user_manager
from src.rag.user_workspace_rag import user_workspace_rag_manager
client = TestClient(app)

class TestUserWorkspaceRAGManager:
    """Unit tests for UserWorkspaceRAGManager."""

    def test_collection_lifecycle(self):
        """Test creating, listing, getting, and deleting a user RAG collection."""
        test_user_id = 'test_user_9999'
        col_name = 'test_project_alpha'
        try:
            manifest = user_workspace_rag_manager.create_collection(user_id=test_user_id, name=col_name, description='Alpha test knowledge base')
            assert manifest['id'] == col_name
            assert manifest['status'] == 'created'
            collections = user_workspace_rag_manager.list_collections(test_user_id)
            assert any((c['id'] == col_name for c in collections))
            retrieved = user_workspace_rag_manager.get_collection(test_user_id, col_name)
            assert retrieved is not None
            assert retrieved['name'] == col_name
            deleted = user_workspace_rag_manager.delete_collection(test_user_id, col_name)
            assert deleted is True
            assert user_workspace_rag_manager.get_collection(test_user_id, col_name) is None
        finally:
            user_manager.delete_user_workspace(test_user_id)

    def test_ingestion_and_search_with_cleaner(self):
        """Test end-to-end cleaning, chunking, and search on multi-format files."""
        test_user_id = 'test_user_9998'
        col_name = 'docs_collection'
        try:
            user_files_dir = user_manager.get_user_directory(test_user_id, subfolder='files', create=True)
            txt_file = user_files_dir / 'guide.md'
            txt_file.write_text('# System Architecture\n\nAI-Breadboard is an interactive platform for routing and testing AI models.\n\n# Capabilities\n\nIt supports Chat, Vision, OCR, and Multi-RAG document retrieval.', encoding='utf-8')
            json_file = user_files_dir / 'settings.json'
            json_file.write_text(json.dumps({'engine': 'fastapi', 'features': ['rag', 'tts', 'skills']}), encoding='utf-8')
            user_workspace_rag_manager.create_collection(user_id=test_user_id, name=col_name, description='Knowledge base containing system docs')
            build_res = user_workspace_rag_manager.build_collection(user_id=test_user_id, rag_id=col_name)
            assert build_res['status'] == 'ok'
            assert build_res['chunks_count'] > 0
            assert 'guide.md' in build_res['processed_files']
            search_res = user_workspace_rag_manager.search_collection(user_id=test_user_id, rag_id=col_name, query='Architecture routing testing models', top_k=3)
            assert len(search_res) > 0
            assert 'AI-Breadboard' in search_res[0]['text']
            assert search_res[0]['score'] > 0.0
            user_workspace_rag_manager.delete_collection(test_user_id, col_name)
        finally:
            user_manager.delete_user_workspace(test_user_id)

class TestUserWorkspaceRAGAPI:
    """Integration tests for /api/user/rags REST API."""

    def test_api_crud_and_search_flow(self):
        """Test full REST API workflow: upload file, create collection, build, search, delete."""
        rag_name = 'api_rag_test'
        file_content = b'# Python Guidelines\n\nAlways follow explicit dependency injection and fail-fast principles in Python code.'
        upload_resp = client.post('/api/user/files/upload', files={'file': ('python_guide.md', io.BytesIO(file_content), 'text/markdown')}, data={'subfolder': 'files'})
        assert upload_resp.status_code == 200
        create_resp = client.post('/api/user/rags', json={'name': rag_name, 'description': 'Guidelines collection'})
        assert create_resp.status_code == 200
        assert create_resp.json()['collection']['id'] == rag_name
        list_resp = client.get('/api/user/rags')
        assert list_resp.status_code == 200
        assert any((c['id'] == rag_name for c in list_resp.json()['collections']))
        build_resp = client.post(f'/api/user/rags/{rag_name}/build', json={'files': ['python_guide.md']})
        assert build_resp.status_code == 200
        assert build_resp.json()['status'] == 'ok'
        assert build_resp.json()['chunks_count'] > 0
        search_resp = client.post(f'/api/user/rags/{rag_name}/search', json={'query': 'dependency injection fail-fast', 'top_k': 2})
        assert search_resp.status_code == 200
        results = search_resp.json()['results']
        assert len(results) > 0
        assert 'dependency injection' in results[0]['text']
        del_resp = client.delete(f'/api/user/rags/{rag_name}')
        assert del_resp.status_code == 200
        assert del_resp.json()['status'] == 'ok'
        client.delete('/api/user/files?filename=python_guide.md&subfolder=files')

    def test_qa_entries_and_reindexing(self):
        """Test adding Q&A entries, listing, searching, and deleting specific entries."""
        test_user_id = 'test_user_9997'
        col_name = 'qa_test_col'
        try:
            user_workspace_rag_manager.create_collection(user_id=test_user_id, name=col_name)
            qa_entry = user_workspace_rag_manager.add_qa_entry(user_id=test_user_id, rag_id=col_name, question='Где можно скачать фильм?', answer='Фильмы и сериалы можно найти в каталоге локальной медиатеки.')
            assert qa_entry['chunk_id'].startswith('qa_')
            assert 'локальной медиатеки' in qa_entry['content']
            entries_data = user_workspace_rag_manager.list_entries(user_id=test_user_id, rag_id=col_name)
            assert entries_data['total'] == 1
            assert entries_data['entries'][0]['chunk_id'] == qa_entry['chunk_id']
            search_res = user_workspace_rag_manager.search_collection(user_id=test_user_id, rag_id=col_name, query='скачать фильм', top_k=2)
            assert len(search_res) > 0
            assert 'медиатеки' in search_res[0]['text']
            del_success = user_workspace_rag_manager.delete_entry(user_id=test_user_id, rag_id=col_name, chunk_id=qa_entry['chunk_id'])
            assert del_success is True
            entries_after = user_workspace_rag_manager.list_entries(user_id=test_user_id, rag_id=col_name)
            assert entries_after['total'] == 0
            search_after = user_workspace_rag_manager.search_collection(user_id=test_user_id, rag_id=col_name, query='скачать фильм', top_k=2)
            assert len(search_after) == 0
            user_workspace_rag_manager.delete_collection(test_user_id, col_name)
        finally:
            user_manager.delete_user_workspace(test_user_id)

    def test_api_qa_entries_crud_flow(self):
        """Test API endpoints for adding, listing, and deleting Q&A entries."""
        rag_name = 'api_qa_collection'
        client.post('/api/user/rags', json={'name': rag_name, 'description': 'QA API testing'})
        post_resp = client.post(f'/api/user/rags/{rag_name}/entries', json={'question': 'Как настроить SSL сертификат?', 'answer': 'Используйте скрипт install_cert.ps1 или команду assist cert generate.'})
        assert post_resp.status_code == 200
        chunk_id = post_resp.json()['entry']['chunk_id']
        list_resp = client.get(f'/api/user/rags/{rag_name}/entries')
        assert list_resp.status_code == 200
        assert list_resp.json()['total'] == 1
        search_resp = client.post(f'/api/user/rags/{rag_name}/search', json={'query': 'сертификат SSL', 'top_k': 1})
        assert search_resp.status_code == 200
        assert len(search_resp.json()['results']) > 0
        del_entry_resp = client.delete(f'/api/user/rags/{rag_name}/entries/{chunk_id}')
        assert del_entry_resp.status_code == 200
        assert del_entry_resp.json()['deleted_chunk_id'] == chunk_id
        list_empty = client.get(f'/api/user/rags/{rag_name}/entries')
        assert list_empty.json()['total'] == 0
        client.delete(f'/api/user/rags/{rag_name}')