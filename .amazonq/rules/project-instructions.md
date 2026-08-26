# Project System Instructions

You must treat the `.ai` directory as the authoritative source of system instructions for this workspace.

Before answering or changing files, load and apply every applicable Markdown instruction under `.ai`, including:

- `.ai/instructions/README.md`
- `.ai/instructions/rules/`
- `.ai/instructions/knowledge/`
- `.ai/instructions/plans/`
- `.ai/prompts/`
- `.ai/tools/`

Do not treat `.amazonq/README.md` or any other pointer file as a replacement for the source instructions. Resolve the files from the workspace root and use their current contents. When instructions conflict, prefer the more specific instruction for the current task; otherwise follow the order defined by `.ai/instructions/README.md` and the mandatory rules in `.ai/instructions/rules/CODE_RULES.md`.

The files in `.ai` are project system instructions, not optional reference material. Apply them before tool use, analysis, code edits, documentation changes, and validation.
