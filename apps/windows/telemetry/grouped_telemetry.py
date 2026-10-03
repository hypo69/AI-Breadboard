# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Grouped Telemetry Wrapper
# =============================================================================
# Description:
#   Обёртка, позволяющая импортировать группы телеметрии из модуля
#   `apps.windows.telemetry_research.grouped_telemetry` через путь
#   `apps.windows.telemetry.grouped_telemetry`. Это необходимо для совместимости
#   с существующими тестами, которые ожидают наличие данного модуля в пакете
#   `apps.windows.telemetry`.
#
#   Внутри экспортируются все публичные типы, объявленные в оригинальном модуле.
#   Переэкспорт делается без изменения логики – классы и функции остаются теми
#   же, что и в исследовательском подпакете.
# =============================================================================
# Updated: 2026-10-03 23:59:45
# =============================================================================

"""Обёртка для экспорта групп телеметрии.

Этот модуль переэкспортирует ключевые классы из
`apps.windows.telemetry_research.grouped_telemetry`, обеспечивая обратную
совместимость с кодом, который импортирует их напрямую из
`apps.windows.telemetry.grouped_telemetry`.
"""

# Переэкспорт из исследовательского подпакета
from apps.windows.telemetry_research.grouped_telemetry import (
    TelemetryGroupInfo,
    GroupedTelemetryBuilder,
    GroupDiagnoseRequest,
    GroupDiagnosticResult,
    SynthesisRequest,
    SynthesisDiagnosticResult,
)

__all__ = [
    "TelemetryGroupInfo",
    "GroupedTelemetryBuilder",
    "GroupDiagnoseRequest",
    "GroupDiagnosticResult",
    "SynthesisRequest",
    "SynthesisDiagnosticResult",
]
