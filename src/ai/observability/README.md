# AI Diagnostics Framework (`src/ai/diagnostics`)

A universal framework for heuristic-driven and AI-augmented anomaly detection.

## Overview
This module provides an extensible architecture for diagnosing performance issues, bottlenecks, and anomalies across any part of the **AI-Breadboard** platform (system, cloud, application, or business logic).

## Core Concepts
- **`DiagnosticEngine` (Abstract Base)**: The core framework class. It enforces a strict two-stage diagnostic process:
    1. **Heuristic Evaluation**: Fast, rule-based checks that yield high-speed performance and low cost.
    2. **AI Reasoning**: Optional, LLM-based analysis of *only* detected anomalies, ensuring token efficiency.
- **Anomaly Detection**: Uses standardized `AnomalyItem` models to represent detected problems, regardless of the source domain.

## Extending the Framework
To add diagnostics for a new domain:

1.  **Create a new engine**: Subclass `DiagnosticEngine` in `src/ai/diagnostics/`.
2.  **Implement Heuristics**: Override `evaluate_heuristics(self, data: Any)`.
3.  **Use**: Instantiate your engine and call `await engine.diagnose(data)`.

```python
from src.ai.observability.engine import DiagnosticEngine

class MyDomainEngine(DiagnosticEngine):
    def evaluate_heuristics(self, data: MyData) -> Tuple[int, List[AnomalyItem], List[str]]:
        # ... rule-based logic ...
        return score, anomalies, recommendations
```

See `skills/ai-diagnostics/` for more details on implementing specific workflows.
