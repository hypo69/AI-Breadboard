# Prompts Subsystem (`.ai/prompts`)

## Purpose
Hosts the production system instructions, role descriptions, and modular rule chunks injected into AI models and autonomous agents.

---

## Organization

- **`chat/`**: System instructions for the general conversational assistant (`system_instruction.md`) and version archive (`versions/`).
- **`narrator/`**: System instructions for media summaries and voice narration (`narrator_style.md`) and version archive (`versions/`).
- **`rules/`**: Modular prompt chunks matched and assembled dynamically at runtime by `RulesRAG`.

---

## Dynamic Assembly with RulesRAG

At runtime, `core.rag.RulesRAG` semantically queries the rules collection based on user intent and injects only relevant instructions into the active context window to optimize token efficiency.
