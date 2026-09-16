---
name: Engineering Standards
description: Code style, architecture principles, and quality standards for the project
inclusion: auto
---

# 🏗️ Engineering Standards & Code Style

This steering file applies project-wide engineering standards, architecture principles, and code quality requirements to all code changes.

## Source
These standards are maintained in `.ai/instructions/rules/CODE_RULES.md` and represent the unified engineering standard v1.0.

## Key Principles

### 1. Readability Over Cleverness
Code is written for human reading first. Use clear, explicit patterns rather than syntactic tricks.

### 2. Single Responsibility Principle (SRP)
Each module, class, and function handles exactly one task. If a function does multiple things, decompose it.

### 3. Explicit Over Implicit
- Dependencies must be passed explicitly (Dependency Injection)
- No global state; use controlled configuration objects
- Type hints for all functions

### 4. Early Return & Fail-Fast
Functions must exit immediately upon detecting invalid input or failed preconditions.

```python
# ✅ CORRECT: Early return
def process_data(data: dict) -> bool:
    if not data:
        return False
    # Main logic
    return True

# ❌ WRONG: Deep nesting
def process_data(data: dict) -> bool:
    if data:
        # Main logic
        return True
    return False
```

### 5. Configuration Over Hardcode
**All Parameters must come from config, not hardcoded:**
- Network ports
- Timebase URLs and IPs
- Timeouts and rate limits
- Paths to directories
- Operation modes

```python
# ✅ CORRECT
port = config.port
timeout = config.timeout

# ❌ WRONG
port = 8000
timeout = 30
```

### 6. Absolute Ban on `None`

**`None` is FORBIDDEN in this codebase.**

#### Rule 6.1: No `None` in Function Parameters
Function parameters with `None` defaults are not allowed:

```python
# ❌ FORBIDDEN
def execute_connection(self, timeout: Optional[int] = None) -> Self:

# ✅ REQUIRED
def execute_connection(self, timeout: Optional[int] = 0) -> Self:
```

#### Rule 6.2: No `None` Initialization
Variables and class properties must initialize with empty defaults, NOT `None`:

```python
# ❌ WRONG
str_output = None
dict_output = None

# ✅ CORRECT
str_output = ''
dict_output = {}
```

#### Rule 6.3: No `is None` Comparisons
Never use `is None` or `is not None`:

```python
# ❌ WRONG
if connection is None:
    ...

# ✅ CORRECT
if not connection:
    ...
```

#### Rule 6.4: Functions Must Return Values
Functions must never implicitly return `None` via bare `return`. Return explicit values:

```python
# ❌ WRONG
def validate(data):
    if not data:
        return  # Implicitly returns None

# ✅ CORRECT
def validate(data):
    if not data:
        return False
    return True
```

## Language-Specific Standards

### Python 3.12+
- Use modern features: `pathlib`, `enum.StrEnum`, `match`, `@override`, `typing.Self`, `Protocol`, `TypedDict`
- UTF-8 strict encoding without BOM
- Russian language for docstrings and comments
- File header format (Process Name, Description, Examples, etc.)

### JavaScript/TypeScript ES2024
- Use `async/await`, destructuring, optional chaining `?.`, nullish coalescing `??`
- Strict UTF-8 encoding
- Russian language for docstrings and comments (though code identifiers stay English)
- No Cyrillic in source code file headers

### PHP 8.3+
- Modern OOP with Singleton patterns
- NO Cyrillic in source code (breaks Unicode)
- Mandatory nonce verification and output escaping
- WordPress security practices

### HTML/CSS/SCSS
- NO Cyrillic in source code headers
- CSS Grid for layouts
- Responsive variable system
- data-i18n attributes for translation support

## Code Quality Rules

### Function Size Limit
- Maximum 500 lines per function (may extend to ~575 if justified)
- Must decompose if exceeding limit

### Nesting Depth
- Maximum 3 levels of nested loops/conditionals
- Deeper nesting signals need for decomposition

### No Dead Code
- Remove unused variables, imports, functions immediately
- No commented-out code "for later"
- Clean up during refactoring

### No Duplication (DRY)
- **Prior Art Audit Required**: Before implementing anything, search existing code
- If working implementation exists, reuse or extend it
- No conflicting/alternative implementations allowed
- Identical operations must use shared utilities/components

## Documentation Standard

### File Headers
Every source file must start with structured header:

```
Process Name: [Brief description of what this module does]
Description: [15-25 words explaining purpose and scope]
Examples: [Working code example]
File: [filename]
Author: [author name]
Copyright: © 2026 [organization]
```

### Docstring Format (hypo69 docblock)
Required sections in order:
1. **Short Description** - One line
2. **Long Description** - (Optional) Detailed explanation
3. **Args:** - Parameters with types and descriptions
4. **Returns:** - Return value type and description
5. **Exceptions:** - Exceptions that may be raised
6. **Examples:** - Working code examples

### Comments Philosophy
- Comments explain **WHY**, not **WHAT**
- Explain architectural decisions and non-obvious logic
- Use Russian language

## Language Standards

| Aspect | Standard |
|--------|----------|
| Docstrings | **Russian** |
| Comments | **Russian** |
| Logs | **Russian** |
| File headers | **Russian** |
| Documentation | **Russian** |
| Code identifiers | **English** |

## Application Integration Lifecycle

When creating new application in `apps/<app_name>`:

1. **Business Logic** - Implement in `apps/<app_name>/`
2. **FastAPI Router** - Export router from `router.py`
3. **Server Registration** - Add to `src/app/__init__.py`
4. **Web Tab** - Create in `src/api/webinterface/<app_name>_tab/`
5. **Admin UI** - Add to admin interface navigation
6. **TDD & Docs** - Write tests and documentation

## Related Documents

- Full details: `.ai/instructions/rules/CODE_RULES.md`
- Documentation: `.ai/instructions/rules/DOCS_RULES.md`
- Code reuse: `.ai/instructions/rules/REUSE_RULES.md`

---

**When working with code, apply these standards consistently across all languages and file types.**
