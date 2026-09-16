# Workflow: Adding new diagnostic rules

1. Create a new subclass of `DiagnosticEngine` in `src/ai/diagnostics/`.
2. Implement `evaluate_heuristics` for your specific data structure.
3. Pass your data to `diagnose()`.
