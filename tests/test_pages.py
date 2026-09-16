# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient
from src.app import create_app, register_pages, AppState

@pytest.fixture
def app_with_pages():
    app = create_app()
    state = AppState()
    app.state.app_state = state
    register_pages(app)
    return app

@pytest.fixture
def client(app_with_pages):
    return TestClient(app_with_pages)

def test_root_endpoint_unauthenticated(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')
    assert len(response.text) > 0

def test_login_endpoint(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')

def test_admin_endpoint_unauthenticated(client):
    response = client.get('/admin')
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')
    assert len(response.text) > 0
    # Must contain OAuth login button
    assert '/auth/google?next=/admin' in response.text
    assert 'btn-google' in response.text

def test_admin_endpoint_authenticated_as_admin(client):
    from src.api.router_auth import TokenData, create_jwt_token
    token = create_jwt_token(TokenData(email="admin@localhost", name="Admin", id=1))
    response = client.get('/admin', cookies={'auth_token': token})
    assert response.status_code == 200
    assert 'AI Assistant - Admin' in response.text or 'mainTabs' in response.text

def test_tv_endpoint(client):
    response = client.get('/tv')
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')

def test_mic_endpoint(client):
    response = client.get('/mic')
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')
    assert 'Голосовой Пульт' in response.text

def test_tc_endpoint(client):
    """Проверяет доступность интерфейса Test Computer по маршруту /tc."""
    response = client.get('/tc')
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')
    assert 'appsNavTabs' in response.text or 'apps-interface' in response.text

def test_apps_endpoint(client):
    """Проверяет доступность центра приложений по маршруту /apps."""
    response = client.get('/apps')
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')
    assert 'appsNavTabs' in response.text or 'apps-interface' in response.text

