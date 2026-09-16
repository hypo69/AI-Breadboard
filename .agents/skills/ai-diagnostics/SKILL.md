---
name: ai-diagnostics
description: Universal diagnostics engine for analyzing system telemetry, logs, and application metrics. Use to detect anomalies and generate actionable performance reports from any structured diagnostic context.
description_i18n:
  en: Universal diagnostics engine for analyzing system telemetry, logs, and application metrics. Use to detect anomalies and generate actionable performance reports from any structured diagnostic context.
  ru: Универсальный диагностический модуль для анализа системной телеметрии, логов и метрик приложений. Используйте для обнаружения аномалий и генерации отчетов о производительности.
---

# AI Diagnostics Skill

This skill provides a unified interface for diagnosing performance issues, bottlenecks, and anomalies across the AI-Breadboard platform.

## When to use

- **System Health Checks**: Diagnosing CPU/RAM/Thermal bottlenecks on the host.
- **Log Analysis**: Identifying errors or patterns in system or cloud logs.
- **Performance Audits**: Analyzing telemetry snapshots to generate actionable recommendations.

## Usage

Use the `SystemDiagnosticEngine` to process data:

```python
from src.ai.observability.system_engine import SystemDiagnosticEngine

# Initialize with a chat model for LLM-based reasoning
diagnostician = SystemDiagnosticEngine(chat_model=my_chat_model)

# Diagnose system snapshot
report = await diagnostician.diagnose(snapshot)
print(report.summary)
```

## Advanced

- See [WORKFLOWS.md](references/workflows.md) for how to extend the diagnostic engine for new data sources (e.g., cloud logs, DB metrics).
