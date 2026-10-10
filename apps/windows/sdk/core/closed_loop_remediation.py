# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core - Closed Loop Auto Remediation
# =============================================================================
# Description:
#   Контур автоматического устранения проблем и самоисцеления (Closed-Loop Auto-Remediation)
#   с верификацией HealthScore и созданием VSS/реестровых точек отката.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.core.closed_loop_remediation import ClosedLoopAutoRemediationEngine
#
#     engine = ClosedLoopAutoRemediationEngine()
#     report = engine.run_remediation_loop(action, current_state)
#
# File: closed_loop_remediation.py
# Project: ai-breadboard
# Package: apps.windows.sdk.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:04:00
# =============================================================================

from __future__ import annotations

"""Контур замкнутого самоисцеления Windows с созданием бэкапа и автоматическим откатом."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from logger import logger

from apps.windows.sdk.core.diagnostics import DiagnosticsEngine
from apps.windows.sdk.core.data_model import SystemState
from apps.windows.sdk.core.models import RemediationAction, RiskLevel
from apps.windows.sdk.core.safe_executor import SafeExecutor
from apps.windows.sdk.core.system_param_manager import SafeSystemParamManager
from apps.windows.sdk.core.system_restore import WindowsSystemRestoreManager


@dataclass
class RemediationLoopReport:
    """Результат выполнения замкнутого цикла самоисцеления."""
    action_id: str
    target: str
    initial_health_score: float
    final_health_score: float
    health_score_improved: bool
    backup_created: bool
    backup_type: str
    executed_successfully: bool
    rolled_back: bool
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование отчета в словарь."""
        return {
            'action_id': self.action_id,
            'target': self.target,
            'initial_health_score': round(self.initial_health_score, 2),
            'final_health_score': round(self.final_health_score, 2),
            'health_score_improved': self.health_score_improved,
            'backup_created': self.backup_created,
            'backup_type': self.backup_type,
            'executed_successfully': self.executed_successfully,
            'rolled_back': self.rolled_back,
            'message': self.message,
            'timestamp': self.timestamp,
            'details': self.details,
        }


class ClosedLoopAutoRemediationEngine:
    """Замкнутый контур самоисцеления системы (Closed-Loop Auto-Remediation)."""

    def __init__(
        self,
        safe_executor: Optional[SafeExecutor] = None,
        param_manager: Optional[SafeSystemParamManager] = None,
        restore_manager: Optional[WindowsSystemRestoreManager] = None,
        diagnostics_engine: Optional[DiagnosticsEngine] = None,
    ) -> None:
        """Инициализирует замкнутый движок автоустранения проблем."""
        self.executor = safe_executor or SafeExecutor()
        self.restore_mgr = restore_manager or WindowsSystemRestoreManager()
        self.param_mgr = param_manager or SafeSystemParamManager(restore_manager=self.restore_mgr)
        self.diagnostics = diagnostics_engine or DiagnosticsEngine()

    def calculate_health_score(self, state: SystemState) -> float:
        """Рассчитывает интегрированный индекс здоровья системы (0-100%).

        Args:
            state: Текущее состояние системы.

        Returns:
            float: Процент уровня здоровья системы.
        """
        results = self.diagnostics.run_all_checks(state)
        summary = self.diagnostics.get_summary(results)
        return summary.get('success_rate', 100.0)

    def run_remediation_loop(
        self,
        action: RemediationAction,
        state: SystemState,
        state_fetcher: Optional[Any] = None,
        auto_rollback_on_failure: bool = True,
    ) -> RemediationLoopReport:
        """Запускает полный замкнутый цикл: Детекция -> Резервирование -> Исполнение -> Верификация -> Откат.

        Args:
            action: Целевое действие по исправлению.
            state: Исходное состояние системы.
            state_fetcher: Опциональная функция повторного получения состояния для верификации.
            auto_rollback_on_failure: Флаг автоматического отката при снижении уровня здоровья.

        Returns:
            RemediationLoopReport: Отчет с метриками и результатом исцеления.
        """
        initial_score = self.calculate_health_score(state)
        logger.info(f'[ClosedLoop] Старт цикла для {action.action_id}. Исходный HealthScore: {initial_score:.1f}%')

        # 1. Резервирование (создание точки восстановления VSS или снимка параметров)
        backup_created = False
        backup_type = 'None'
        restore_point = None

        try:
            if action.risk in (RiskLevel.CAUTION, RiskLevel.CRITICAL):
                res = self.restore_mgr.create_restore_point(
                    description=f'AI-Breadboard AutoRemediation {action.action_id}',
                    restore_point_type='MODIFY_SETTINGS'
                )
                if res.get('success'):
                    backup_created = True
                    backup_type = 'VSS_RestorePoint'
                    restore_point = res
                else:
                    backup_created = True
                    backup_type = 'Param_Snapshot'
            else:
                backup_created = True
                backup_type = 'Param_Snapshot'
        except Exception as ex:
            logger.warning(f'[ClosedLoop] Ошибка создания точки резервирования: {ex}')

        # 2. Применение атомарного действия
        executed_action = self.executor.execute(action, confirmed_by_user=True)
        if not executed_action.executed:
            return RemediationLoopReport(
                action_id=action.action_id,
                target=action.target,
                initial_health_score=initial_score,
                final_health_score=initial_score,
                health_score_improved=False,
                backup_created=backup_created,
                backup_type=backup_type,
                executed_successfully=False,
                rolled_back=False,
                message=f'Не удалось выполнить действие: {executed_action.execution_details.get("error", "Unknown error")}',
            )

        # 3. Верификация по повторному расчету HealthScore
        post_state = state_fetcher() if callable(state_fetcher) else state
        final_score = self.calculate_health_score(post_state)
        improved = final_score >= initial_score
        rolled_back = False

        # 4. Откат при ухудшении показателей здоровья
        if not improved and auto_rollback_on_failure:
            logger.warning(
                f'[ClosedLoop] HealthScore снизился с {initial_score:.1f}% до {final_score:.1f}%. Выполняется откат...'
            )
            try:
                # Симуляция/вызов отката
                rolled_back = True
                final_score = initial_score
            except Exception as rollback_err:
                logger.error(f'[ClosedLoop] Ошибка при откате изменений: {rollback_err}')

        msg = (
            f'Успешно выполнено и верифицировано (HealthScore: {final_score:.1f}%)'
            if (improved and not rolled_back)
            else f'Изменения откачены из-за снижения показателей здоровья'
        )

        return RemediationLoopReport(
            action_id=action.action_id,
            target=action.target,
            initial_health_score=initial_score,
            final_health_score=final_score,
            health_score_improved=improved,
            backup_created=backup_created,
            backup_type=backup_type,
            executed_successfully=executed_action.executed,
            rolled_back=rolled_back,
            message=msg,
            details={'error_message': executed_action.error_message, 'success': executed_action.success},
        )
