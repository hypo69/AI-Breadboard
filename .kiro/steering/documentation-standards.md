---
name: Documentation Standards
description: TDD workflow, docstring format, and documentation requirements
inclusion: auto
---

# 📚 Documentation & TDD Standards

This steering file defines the documentation workflow (TDD-doc-gen), docstring format, and README requirements.

## Source
Based on `.ai/instructions/rules/DOCS_RULES.md` - mandatory for all functional changes.

## Three Levels of Documentation

| Level | Type | Location | When |
|-------|------|----------|------|
| **1** | Docstring | In code (function/class) | Always required |
| **2** | Comments | In code (logic explanation) | For complex logic |
| **3** | README.md | Module directory | One per module/package |

## TDD Documentation Workflow (Mandatory)

Apply TDD-doc-gen when:
- ✅ Adding new functions, classes, or methods
- ✅ Changing function signatures (add/remove/modify parameters)
- ✅ Changing function logic or return values
- ✅ Creating new directories (modules/packages)
- ✅ Refactoring code

### The 6-Step Workflow

```
STEP 1: Write Specification
├─ Where: .ai/instructions/knowledge/specs/ (new specs for complex features)
├─ What: Define function behavior, edge cases, constraints
└─ Output: Spec document for reference

        ↓

STEP 2: Add Docstring to Code
├─ Where: Function/class docstring
├─ Format: hypo69 docblock (see below)
└─ Includes: Args, Returns, Exceptions, Examples

        ↓

STEP 3: Implement Function
├─ Follow CODE_RULES.md standards
├─ Use early returns, explicit dependencies
└─ Add comments explaining "WHY", not "WHAT"

        ↓

STEP 4: Write Tests
├─ Where: tests/ directory
├─ Requirement: Minimum 70% code coverage
└─ Run: pytest tests/test_*.py --cov

        ↓

STEP 5: Write README.md (if new directory)
├─ Where: Root of new module/package
├─ Describes: Architecture, components, usage examples
└─ Updates: Cross-references and dependencies

        ↓

STEP 6: Update Main Documentation
├─ Update DOCUMENTATION_INDEX.md
├─ Update README.ru.md if needed
└─ Verify: No broken links, all references valid
```

## Docstring Format (hypo69 docblock)

### Required Sections (In Order)

```
[Short one-line description]

[Optional long explanation of design decisions, why this approach]

Args:
    param_name (type): Description, constraints, defaults.
    another_param (type): Description.

Returns:
    type: Description of return value and conditions.

Exceptions:
    ErrorType: Conditions when this error is raised.
    AnotherError: Another error condition.

Examples:
    Working code example that can be copied and executed.
```

### Python Example
```python
def execute_connection(self, timeout: Optional[int] = 0, input_str: Optional[str] = '') -> Self:
    """Запуск процесса подключения к серверу.

    Установка соединения и инициализация взаимодействия.

    Args:
        timeout (Optional[int]): Максимальное время ожидания ответа в секундах.
                                 Значение по умолчанию: 0 (без таймаута).
        input_str (Optional[str]): Входная строка инициализации.
                                   Значение по умолчанию: '' (пусто).

    Returns:
        Self: Текущий экземпляр объекта для поддержки цепочки вызовов.

    Exceptions:
        ConnectionError: Если порт недоступен или соединение не установлено.
        TimeoutError: Если превышен timeout при ожидании ответа.

    Examples:
        >>> connector = FoundryConnector(port=8000)
        >>> result = connector.execute_connection(timeout=10, input_str='init')
        >>> print(result.status)
        connected
    """
    if self.port <= 0:
        raise ConnectionError("Неверный номер порта")
    
    self.status = "connected"
    return self
```

### JavaScript/TypeScript Example
```javascript
/**
 * Asynchronous HTTP POST execution to selected path.
 *
 * Sends payload to API endpoint and handles response parsing.
 *
 * Args:
 *   endpoint (string) — API endpoint target path (e.g., '/submit').
 *   payload (object) — Request body payload details.
 *
 * Returns:
 *   object — Resolved JSON data response object.
 *
 * Exceptions:
 *   Error — Thrown on network timeout or failed status codes (non-2xx).
 *
 * Examples:
 *   const client = new ApiClient(config.api.baseUrl);
 *   const response = await client.postData('/submit', { id: 123 });
 *   console.log(response.success);
 */
async postData(endpoint, payload) {
    if (!endpoint) {
        throw new Error("Missing endpoint parameter");
    }

    const targetUrl = `${this.baseUrl}${endpoint}`;
    const response = await fetch(targetUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload ?? {})
    });

    if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
    }

    return await response.json();
}
```

## README.md Requirements

Every module/package directory **MUST** contain `README.md` with:

### 1. Module Purpose
```markdown
# Module Name

Brief description of what this module does and why it exists.
```

### 2. Architecture
```markdown
## Architecture

- **Component 1**: Description
- **Component 2**: Description
- [Add diagram if complex]
```

### 3. Key Classes/Functions
```markdown
## Key Components

### ClassName
Brief description and usage.

### function_name()
Brief description and usage.
```

### 4. Usage Examples
```markdown
## Usage

### Example 1: Basic Usage
[Working code example]

### Example 2: Advanced Usage
[Working code example]
```

### 5. Dependencies
```markdown
## Dependencies

- External library 1
- Internal module references
```

### 6. Testing
```markdown
## Testing

Run tests:
```bash
pytest tests/ --cov
```

Coverage requirement: >= 70%
```

## Comment Philosophy

### ✅ GOOD: Explain WHY
```python
# Using Set instead of Array ensures unique IDs in O(1) complexity
active_connections = set()

# Retry logic with exponential backoff prevents API rate limiting
for attempt in range(max_retries):
    delay = backoff_factor ** attempt
```

### ❌ BAD: Redundant syntax description
```python
# Create a new set of active connections
active_connections = set()

# Loop through retry attempts
for attempt in range(max_retries):
```

## Language Standard

**All documentation must be in Russian:**

| Type | Language |
|------|----------|
| Docstrings | Russian |
| Comments | Russian |
| Function descriptions | Russian |
| Parameter descriptions | Russian |
| File headers | Russian |
| README.md files | Russian |
| Code identifiers | English (per standard) |

## File Header Format

### Python Header
```python
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: [Brief description]
# =============================================================================
# Description:
#   [15-25 words explaining purpose]
#
# Examples:
#   >>> from module import Function
#   >>> result = Function()
#
# File: filename.py
# Project: Our Intelligent Assistant
# Package: PackageName
# Module: module.name
# Class: ClassName
# Function: function_name
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
```

## Testing Requirements

### Minimum Standards
- **Coverage**: >= 70% code coverage
- **Tests**: Write tests while implementing (TDD approach)
- **Execution**: Run pytest before commit

```bash
# Run all tests with coverage
pytest tests/ --cov

# Run specific test file
pytest tests/test_module.py -v

# Run with coverage report
pytest tests/ --cov --cov-report=html
```

## Related Documents

- Engineering Standards: `.ai/instructions/rules/CODE_RULES.md`
- Code Reuse: `.ai/instructions/rules/REUSE_RULES.md`
- Full spec: `.ai/instructions/README.md`

---

**Apply these documentation standards to all new code and refactoring work.**
