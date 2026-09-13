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
    assert len(response.text) > 0

def test_tv_endpoint(client):
    response = client.get('/tv')
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')

def test_mic_endpoint(client):
    response = client.get('/mic')
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')
    assert 'Голосовой Пульт' in response.text

def test_static_webinterface_endpoint(client):
    response = client.get('/webinterface/login.html')
    assert response.status_code == 200
    assert len(response.text) > 0
