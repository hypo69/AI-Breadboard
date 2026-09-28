"""Юнит-тесты для приложения Google User Desktop."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from apps.google_user_desktop.routers.router import init_router
from apps.google_user_desktop.src.state import (
    CalendarEventSummary,
    DocumentItemSummary,
    DriveFileSummary,
    GoogleAccountSummary,
    GoogleUserDesktopState,
    MailItemSummary,
)


class TestGoogleUserDesktopState(unittest.TestCase):
    """Тестирование класса управления состоянием GoogleUserDesktopState."""

    @patch('apps.google_user_desktop.src.state.list_google_accounts')
    @patch('apps.google_user_desktop.src.state.get_account_info')
    def test_get_active_account(self, mock_info, mock_list):
        """Проверка получения данных об активном аккаунте."""
        mock_list.return_value = [
            {'name': 'test_acc', 'email': 'test@example.com', 'type': 'oauth2', 'status': 'active', 'is_default': True}
        ]
        mock_info.return_value = {'name': 'test_acc', 'email': 'test@example.com', 'type': 'oauth2', 'status': 'active', 'is_default': True}

        state = GoogleUserDesktopState()
        acc = state.get_active_account()
        self.assertIsInstance(acc, GoogleAccountSummary)
        self.assertEqual(acc.name, 'test_acc')
        self.assertEqual(acc.email, 'test@example.com')
        self.assertEqual(acc.status, 'active')

    @patch('apps.google_user_desktop.src.state.list_google_accounts')
    def test_get_active_account_unconfigured(self, mock_list):
        """Проверка статуса при отсутствии аккаунтов."""
        mock_list.return_value = []
        state = GoogleUserDesktopState()
        acc = state.get_active_account()
        self.assertEqual(acc.status, 'unconfigured')

    @patch('apps.google_user_desktop.src.state.list_google_accounts')
    @patch('apps.google_user_desktop.src.state.set_default_account')
    def test_select_account(self, mock_set_default, mock_list):
        """Проверка переключения активного аккаунта."""
        mock_list.return_value = [{'name': 'work'}, {'name': 'personal'}]
        state = GoogleUserDesktopState()
        
        self.assertTrue(state.select_account('personal'))
        self.assertEqual(state.selected_account_name, 'personal')
        mock_set_default.assert_called_with('personal')

        self.assertFalse(state.select_account('non_existent'))

    @patch('apps.google_user_desktop.src.state.get_google_calendar_events')
    def test_fetch_calendar_events(self, mock_events):
        """Проверка загрузки событий Календаря."""
        mock_events.return_value = [
            {
                'id': 'ev1',
                'summary': 'Встреча команды',
                'start': {'dateTime': '2026-09-30T10:00:00Z'},
                'end': {'dateTime': '2026-09-30T11:00:00Z'},
                'location': 'Онлайн',
                'htmlLink': 'https://calendar.google.com/event1',
            }
        ]
        state = GoogleUserDesktopState()
        events = state.fetch_calendar_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].id, 'ev1')
        self.assertEqual(events[0].summary, 'Встреча команды')

    @patch('apps.google_user_desktop.src.state.list_google_documents')
    def test_fetch_documents(self, mock_docs):
        """Проверка получения списка Google Документов."""
        mock_docs.return_value = [
            {
                'id': 'doc1',
                'name': 'Отчет за Q3',
                'mimeType': 'application/vnd.google-apps.document',
                'createdTime': '2026-09-01T00:00:00Z',
                'modifiedTime': '2026-09-28T00:00:00Z',
                'webViewLink': 'https://docs.google.com/doc1',
            }
        ]
        state = GoogleUserDesktopState()
        docs = state.fetch_documents()
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].id, 'doc1')
        self.assertEqual(docs[0].name, 'Отчет за Q3')


class TestGoogleUserDesktopRouter(unittest.TestCase):
    """Тестирование FastAPI роутера Google User Desktop."""

    def setUp(self):
        """Подготовка тестового клиента FastAPI."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(init_router())
        self.client = TestClient(app)

    @patch('apps.google_user_desktop.routers.router.get_state')
    def test_get_status_endpoint(self, mock_get_state):
        """Тест эндпоинта GET /api/google-desktop/status."""
        mock_state = MagicMock()
        mock_state.refresh_all.return_value = {
            'account': {'name': 'test', 'email': 'test@test.com', 'type': 'oauth2', 'status': 'active', 'is_default': True},
            'mail_count': 5,
            'calendar_events_count': 2,
            'docs_count': 3,
            'drive_files_count': 10,
            'last_refreshed': '2026-09-28T04:00:00Z',
        }
        mock_get_state.return_value = mock_state

        resp = self.client.get('/api/google-desktop/status')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['account']['name'], 'test')
        self.assertEqual(data['mail_count'], 5)

    @patch('apps.google_user_desktop.routers.router.get_state')
    def test_get_accounts_endpoint(self, mock_get_state):
        """Тест эндпоинта GET /api/google-desktop/accounts."""
        mock_state = MagicMock()
        mock_state.get_accounts_list.return_value = [{'name': 'default'}]
        mock_state.get_active_account.return_value = GoogleAccountSummary(name='default', email='a@b.com', status='active')
        mock_get_state.return_value = mock_state

        resp = self.client.get('/api/google-desktop/accounts')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['accounts']), 1)


if __name__ == '__main__':
    unittest.main()
