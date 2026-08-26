# 📚 AI Breadboard: Libro de Texto de Arquitectura de IA, RAG y Fine-Tuning

> **Una placa de pruebas interactiva (Breadboard) para investigadores y desarrolladores de sistemas modernos de inteligencia artificial**

---

## 💡 El Manifiesto «AI Breadboard»

En la ingeniería electrónica, una **placa de pruebas (Breadboard)** es una herramienta fundamental. Permite construir circuitos a partir de componentes discretos (transistores, microcontroladores, sensores) sin necesidad de soldar, medir señales en puntos de prueba y modificar la topología del circuito al instante.

El proyecto **`aibreadboard`** traslada esta filosofía a la inteligencia artificial:
1. **Banco de Pruebas Abierto (Open Breadboard Testbench):** Ejecución nativa, transparente y directa en la máquina local (FastAPI, Python venv, ONNX DirectML) con acceso completo a cada componente.
2. **Bus Unificado de Modelos:** Conexión de cualquier modelo —desde Google Gemini en la nube hasta pequeños modelos locales (SLMs)— bajo la interfaz unificada `UnifiedChatModel`.
3. **Puntos de Prueba Abiertos:** Inspección directa de generación de embeddings, similitud de coseno, inyección de contexto y streaming de tokens.
4. **Laboratorio de RAG y Fine-Tuning:** Optimización de grafos con Microsoft Olive, exportación de pesos a ONNX y adaptación con LoRA/QLoRA.
5. **Sistema Modular de Habilidades (Skills):** Expansión dinámica de capacidades de agentes bajo demanda mediante manifiestos `SKILL.md`.

---

## 🧭 Capítulos del Libro

| Capítulo | Tema |
|---|---|
| [**Capítulo 1**](../../en/book/ch01_philosophy.md) | Filosofía No-Docker y configuración del entorno de trabajo |
| [**Capítulo 2**](../../en/book/ch02_orchestration.md) | Orquestación de modelos y tolerancia a fallos (UnifiedChatModel y ModelManager) |
| [**Capítulo 3**](../../en/book/ch03_local_inference.md) | Inferencia local In-Process y aceleración DirectML en cualquier GPU |
| [**Capítulo 4**](../../en/book/ch04_rag_architecture.md) | Arquitectura RAG, matemáticas de vectores e índices FAISS ligeros |
| [**Capítulo 5**](../../en/book/ch05_optimization_finetuning.md) | Optimización con Microsoft Olive, exportación ONNX y Fine-Tuning |
| [**Capítulo 6**](../../en/book/ch06_agents_and_mcp.md) | Agentes ReAct, protocolo MCP y tuberías de voz multimodales |
| [**Capítulo 7**](../../en/book/ch07_skills_management.md) | Creación y gestión de habilidades (Skills) para modelos y agentes |
| [**Capítulo 8**](../../en/book/ch08_laboratory_practicum.md) | Prácticas de laboratorio: 10 ejercicios interactivos en la placa de pruebas |
