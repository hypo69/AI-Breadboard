import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
from apps.windows.telemetry.models import SystemSnapshot, CpuMetrics, MemoryMetrics
from src.ai.observability.system_engine import SystemDiagnosticEngine

async def test_ai_diagnostics():
    print('Запуск теста для ai-diagnostics...')
    snapshot = SystemSnapshot(cpu=CpuMetrics(total_percent=95.0), memory=MemoryMetrics(percent=95.0, used_gb=30.0, total_gb=32.0))
    diagnostician = SystemDiagnosticEngine()
    score, anomalies, recommendations = diagnostician.evaluate_heuristics(snapshot)
    print(f'Результаты оценки: Score={score}')
    print(f'Обнаружено аномалий: {len(anomalies)}')
    assert score < 100, 'Оценка должна быть ниже 100 при высокой нагрузке'
    assert len(anomalies) > 0, 'Должны быть обнаружены аномалии'
    print('Тест ai-diagnostics успешно пройден.')
    return True
if __name__ == '__main__':
    try:
        asyncio.run(test_ai_diagnostics())
    except Exception as e:
        print(f'Тест провален: {e}')
        sys.exit(1)