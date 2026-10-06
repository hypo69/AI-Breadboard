# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Focus_Policy Tests - Test Focus Policy
# =============================================================================
# Description:
#   Тесты Focus Policy Engine: профили, Task Scheduler, перехват уведомлений,
#   журнал сессий и REST API /api/v1/focus.
#
# Usage Examples:
#   pytest apps/windows/modules/focus_policy/tests/test_focus_policy.py -v
#
# File: test_focus_policy.py
# Project: ai-breadboard
# Package: apps.windows.modules.focus_policy.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 22:05:00
# =============================================================================

from __future__ import annotations
"""Тесты WindowsFocusController и FocusTaskRegistrar."""

from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.modules.focus_policy.controller import WindowsFocusController
from apps.windows.modules.focus_policy.models import FocusProfile, ListenerNotification
from apps.windows.modules.focus_policy.scheduler import FocusTaskRegistrar


class FakeRunner:
    """Фиксирует вызовы schtasks вместо реального запуска."""

    def __init__(self) -> None:
        self.calls: List[List[str]] = []

    def __call__(self, cmd: List[str]) -> int:
        self.calls.append(cmd)
        return 0


class FakeListener:
    """Подставной UserNotificationListener."""

    def __init__(self, status: str = 'Allowed') -> None:
        self.status = status
        self.toasts: List[ListenerNotification] = []
        self.removed: List[int] = []

    def request_access(self) -> str:
        return self.status

    def get_toasts(self) -> List[ListenerNotification]:
        return list(self.toasts)

    def remove(self, notification_id: int) -> None:
        self.removed.append(notification_id)


def _profile(**over: Any) -> FocusProfile:
    data: Dict[str, Any] = {
        'profile_id': 'prof-work-default',
        'name': 'Рабочий фокус',
        'schedule': {'days': ['mon', 'fri'], 'start_time': '09:00', 'end_time': '18:00', 'auto_start': True},
        'notifications': {'mode': 'suppress_and_store', 'allow_priority_apps': ['Priority.App']},
    }
    data.update(over)
    return FocusProfile(**data)


@pytest.fixture
def env(tmp_path: Path):
    runner, listener, applied = FakeRunner(), FakeListener(), []
    ctrl = WindowsFocusController(
        db_path=tmp_path / 'telemetry.db',
        registrar=FocusTaskRegistrar(runner=runner, python='python.exe'),
        listener=listener,
        applier=lambda profile: applied.append(profile.profile_id if profile else None),
    )
    return ctrl, runner, listener, applied


def test_save_profile_registers_scheduler_tasks(env) -> None:
    ctrl, runner, *_ = env
    ctrl.save_profile(_profile())
    assert ctrl.get_profile('prof-work-default').name == 'Рабочий фокус'
    flat = [' '.join(c) for c in runner.calls]
    start = next(c for c in flat if 'TC_Focus_Start_prof-work-default' in c)
    stop = next(c for c in flat if 'TC_Focus_Stop_prof-work-default' in c)
    assert '\\TestComputer\\FocusTimers\\' in start and '/ST 09:00' in start and '/D MON,FRI' in start
    assert '/ST 18:00' in stop
    assert 'apps.windows.core.focus_executor --action start --profile-id prof-work-default' in start


def test_disabled_autostart_deletes_tasks(env) -> None:
    ctrl, runner, *_ = env
    prof = _profile()
    prof.schedule.auto_start = False
    ctrl.save_profile(prof)
    assert not any('/Create' in c for c in runner.calls)
    assert any('/Delete' in c for c in runner.calls)


def test_session_lifecycle_and_summary(env) -> None:
    ctrl, _, listener, applied = env
    ctrl.save_profile(_profile())
    sid = ctrl.start_session('prof-work-default', 'UI_MANUAL')
    assert ctrl.status().is_focus_active and ctrl.status().session_id == sid

    listener.toasts = [
        ListenerNotification(id=1, app_user_model_id='Teams', app_display_name='Microsoft Teams', title='a', text='b'),
        ListenerNotification(id=2, app_user_model_id='Teams', app_display_name='Microsoft Teams', title='c', text='d'),
        ListenerNotification(id=3, app_user_model_id='Priority.App', app_display_name='Terminal', title='e', text='f'),
    ]
    assert ctrl.poll_notifications() == 2
    assert ctrl.poll_notifications() == 0  # повторно не архивируем
    assert listener.removed == [1, 2]
    assert ctrl.status().suppressed_notifications_count == 2

    summary = ctrl.stop_session()
    assert summary.total_suppressed == 2
    assert summary.by_app == {'Microsoft Teams': 2}
    assert not ctrl.status().is_focus_active
    assert applied == ['prof-work-default', None]
    assert len(ctrl.list_suppressed(sid)) == 2


def test_denied_listener_runs_limited_mode(tmp_path: Path) -> None:
    listener = FakeListener(status='Denied')
    ctrl = WindowsFocusController(
        db_path=tmp_path / 't.db', registrar=FocusTaskRegistrar(runner=FakeRunner()), listener=listener, applier=lambda p: None
    )
    ctrl.save_profile(_profile())
    ctrl.start_session('prof-work-default', 'UI_MANUAL')
    listener.toasts = [ListenerNotification(id=1, app_user_model_id='x', app_display_name='X')]
    assert ctrl.poll_notifications() == 0
    assert ctrl.request_listener_access() == 'Denied'


def test_unknown_profile_and_double_start(env) -> None:
    ctrl, *_ = env
    with pytest.raises(KeyError):
        ctrl.start_session('nope', 'UI_MANUAL')
    ctrl.save_profile(_profile())
    ctrl.start_session('prof-work-default', 'UI_MANUAL')
    with pytest.raises(RuntimeError):
        ctrl.start_session('prof-work-default', 'UI_MANUAL')


def test_executor_start_stop(env, monkeypatch) -> None:
    from apps.windows.core import focus_executor

    ctrl, *_ = env
    ctrl.save_profile(_profile())
    focus_executor.run('start', 'prof-work-default', controller=ctrl)
    assert ctrl.status().is_focus_active
    focus_executor.run('stop', 'prof-work-default', controller=ctrl)
    assert not ctrl.status().is_focus_active


def test_rest_api(env) -> None:
    from apps.windows.modules.focus_policy.router import init_router

    ctrl, *_ = env
    app = FastAPI()
    app.include_router(init_router(ctrl))
    client = TestClient(app)

    body = _profile().model_dump()
    assert client.post('/api/v1/focus/profiles', json=body).status_code == 200
    ctrl.start_session('prof-work-default', 'UI_MANUAL')
    st = client.get('/api/v1/focus/status').json()
    assert st['is_focus_active'] and st['active_profile_id'] == 'prof-work-default'
    assert st['listener_access_status'] in ('Allowed', 'Unspecified')
    assert client.get('/api/v1/focus/suppressed-notifications').json() == []
    assert client.post('/api/v1/focus/request-listener-access').json()['status'] == 'Allowed'
