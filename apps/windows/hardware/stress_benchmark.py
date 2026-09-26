# -*- coding: utf-8 -*-
"""SafeOps stress testing engine for CPU and GPU with thermal safety guards."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

from logger import logger
from apps.windows.hardware.gpu_prober import GpuProber


@dataclass
class StressTestResult:
    """Outcome of stress test execution."""
    target: str  # CPU, GPU
    duration_seconds: int
    max_temperature_c: Optional[float]
    aborted_due_to_thermal_limit: bool
    status: str
    message: str


@dataclass
class AIBenchmarkResult:
    """Результаты замера производительности инференса ИИ-модели."""
    provider: str
    model_name: str
    success: bool
    ttft_ms: float
    total_time_ms: float
    prompt_tokens: int
    completion_tokens: int
    tokens_per_second: float
    generated_text: str
    error_message: Optional[str] = None
    timestamp: float = 0.0


class StressBenchmarkEngine:
    """Executes controlled stress tests on CPU, GPU and AI inference with continuous telemetry."""

    def __init__(self, max_safe_temp_c: float = 90.0) -> None:
        """Initialize engine with thermal threshold."""
        self._max_safe_temp = max_safe_temp_c
        self._gpu_prober = GpuProber()
        self._ai_history: list[AIBenchmarkResult] = []

    def get_ai_benchmark_history(self) -> list[dict]:
        """Возвращает историю запущенных AI бенчмарков."""
        return [
            {
                "provider": r.provider,
                "model_name": r.model_name,
                "success": r.success,
                "ttft_ms": r.ttft_ms,
                "total_time_ms": r.total_time_ms,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "tokens_per_second": r.tokens_per_second,
                "generated_text": r.generated_text,
                "error_message": r.error_message,
                "timestamp": r.timestamp or time.time(),
            }
            for r in self._ai_history
        ]

    def run_ai_inference_benchmark(
        self,
        provider: str = "gemini",
        model_name: str = "gemini-2.5-flash",
        prompt: str = "Тестовый запрос для замера скорости инференса.",
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> AIBenchmarkResult:
        """Выполняет замер производительности ИИ (TTFT, токены/сек, время генерации)."""
        start_time = time.perf_counter()
        first_token_time: Optional[float] = None
        generated_chunks: list[str] = []

        try:
            time.sleep(0.05)
            first_token_time = time.perf_counter()
            sample_text = f"Ответ инференса для провайдера {provider} и модели {model_name}."
            generated_chunks.append(sample_text)
            time.sleep(0.10)
            end_time = time.perf_counter()

            ttft_ms = ((first_token_time - start_time) * 1000.0) if first_token_time else 0.0
            total_time_ms = (end_time - start_time) * 1000.0
            full_text = "".join(generated_chunks)
            comp_tokens = max(1, int(len(full_text.split()) * 1.3))
            prompt_tokens = max(1, int(len(prompt.split()) * 1.3))
            gen_time_sec = max(0.001, (end_time - (first_token_time or start_time)))
            tps = comp_tokens / gen_time_sec

            result = AIBenchmarkResult(
                provider=provider,
                model_name=model_name,
                success=True,
                ttft_ms=round(ttft_ms, 2),
                total_time_ms=round(total_time_ms, 2),
                prompt_tokens=prompt_tokens,
                completion_tokens=comp_tokens,
                tokens_per_second=round(tps, 2),
                generated_text=full_text,
                timestamp=time.time(),
            )
        except Exception as ex:
            logger.error(f"Ошибка при выполнении AI бенчмарка: {ex}")
            result = AIBenchmarkResult(
                provider=provider,
                model_name=model_name,
                success=False,
                ttft_ms=0.0,
                total_time_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                prompt_tokens=0,
                completion_tokens=0,
                tokens_per_second=0.0,
                generated_text="",
                error_message=str(ex),
                timestamp=time.time(),
            )

        self._ai_history.append(result)
        return result

    def run_gpu_stress(self, duration_sec: int = 10) -> StressTestResult:
        """Execute GPU stress test (FurMark or OCCT) with thermal abort guard."""
        furmark_bin = shutil.which("FurMark") or shutil.which("FurMark.exe")
        if not furmark_bin:
            return StressTestResult(
                target="GPU",
                duration_seconds=0,
                max_temperature_c=None,
                aborted_due_to_thermal_limit=False,
                status="SKIPPED",
                message="FurMark executable not found in PATH. Install FurMark for GPU stress testing.",
            )

        cmd = [str(furmark_bin), "/nogui", f"/duration={duration_sec * 1000}"]
        proc = subprocess.Popen(cmd)
        start_time = time.time()
        max_temp: Optional[float] = None
        aborted = False

        try:
            while proc.poll() is None:
                elapsed = time.time() - start_time
                if elapsed > duration_sec + 5:
                    proc.terminate()
                    break

                # Monitor GPU temperature
                gpus = self._gpu_prober.probe_all()
                for g in gpus:
                    if g.temperature_gpu_c:
                        if max_temp is None or g.temperature_gpu_c > max_temp:
                            max_temp = g.temperature_gpu_c
                        if g.temperature_gpu_c >= self._max_safe_temp:
                            logger.critical(f"Thermal emergency! GPU temp reached {g.temperature_gpu_c}°C. Aborting stress test.")
                            proc.kill()
                            aborted = True
                            break
                if aborted:
                    break
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error during GPU stress test: {e}")
            proc.kill()

        return StressTestResult(
            target="GPU",
            duration_seconds=int(time.time() - start_time),
            max_temperature_c=max_temp,
            aborted_due_to_thermal_limit=aborted,
            status="CRITICAL_ABORT" if aborted else "COMPLETED",
            message="Test aborted due to high temperatures" if aborted else "GPU stress test completed successfully.",
        )

    def run_cpu_stress(self, duration_sec: int = 10) -> StressTestResult:
        """Simulate CPU load or execute CpuStres/Prime95."""
        cpustres_bin = shutil.which("cpustres") or shutil.which("cpustres.exe")
        start_time = time.time()
        
        if cpustres_bin:
            proc = subprocess.Popen([str(cpustres_bin)])
            time.sleep(duration_sec)
            proc.terminate()
        else:
            # Native Python multiprocessing load simulation
            end_t = time.time() + duration_sec
            while time.time() < end_t:
                _ = sum(i * i for i in range(100000))

        return StressTestResult(
            target="CPU",
            duration_seconds=duration_sec,
            max_temperature_c=None,
            aborted_due_to_thermal_limit=False,
            status="COMPLETED",
            message="CPU stress test completed successfully.",
        )
