# TDD & Documentation Engineering Standards

**Project:** `AI-Breadboard`  
**Standard Version:** 3.0  
**Scope:** All Python codebase modules, routers, providers, plugins, and test suites  
**Author:** hypo69  

---

## 🎯 Core Philosophy & Principles

Test-Driven Development (TDD) in AI-Breadboard is not just a testing practice, but an **architectural specification and documentation engine**. Code, tests, and documentation are inextricably linked:

1. **Self-Documenting Tests:** Every test is written as an executable specification. A developer or agent reading the test file must immediately understand the business rule, the input constraints, and the failure conditions without inspecting the implementation.
2. **Deterministic Invariant:** Code is never considered complete until unit/integration tests pass with 100% green status and all accompanying documentation is fully synchronized.
3. **No Cryptic Assertions:** Raw, uncommented assertions (`assert x == y`) are strictly prohibited. Every assertion must explain *what* broke and *why*.

---

## 🔄 The 6-Step TDD & Documentation Protocol

```mermaid
flowchart TD
    S1[Шаг 1: Impact Analysis & Smoke Test] --> S2[Шаг 2: Test Suite Design with AAA]
    S2 --> S3[Шаг 3: Granular Test Implementation & Comments]
    S3 --> S4[Шаг 4: Test Execution & Verification]
    S4 -->|Tests Fail| FIX[Fix Implementation / Bug]
    FIX --> S4
    S4 -->|Tests Green (100%)| S5[Шаг 5: Directory & Architecture Documentation]
    S5 --> S6[Шаг 6: Master Knowledge Registry Update]
```

### Protocol Steps Breakdown

| Step | Phase | Key Actions | Mandatory Requirements |
| :--- | :--- | :--- | :--- |
| **1** | **Impact Analysis** | Analyze caller/callee hierarchy and transitive imports before writing tests. | Smoke-check module import: `python -c "from module import Target"`. |
| **2** | **Test Suite Design** | Create `tests/test_<module_name>.py` with standard header. | Follow `Arrange -> Act -> Assert` block structure. |
| **3** | **Detailed Coding** | Implement coverage across all 6 test categories. | **Comment every variable**, declare explicit types, provide custom assert messages. |
| **4** | **Test Verification** | Run `pytest tests/test_<module>.py -v`. | 100% pass required. Never proceed to docs if any test is failing. |
| **5** | **Module Docs** | Create/Update `README.md` in module and webinterface directories. | Документация на русском языке, покрывающая назначение, таблицу API и архитектуру. |
| **6** | **Master Registry** | Update `.ai/instructions/knowledge/project_overview.md` & `DOCUMENTATION.md`. | Register all new endpoints, routers, and database schemas. |

---

## 📋 Granular Test Coverage Categories

Every public function, router endpoint, and database adapter must be covered across six distinct categories:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Mandatory Test Coverage Matrix                        │
├──────────────────────┬──────────────────────────────────────────────────────┤
│ 1. Happy Path        │ Standard valid inputs with expected canonical output │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 2. Edge Cases        │ Empty collections, null bytes, zero values, max size │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 3. Type Variants     │ Dict vs TokenData, int vs str, custom models         │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 4. Boundary Values   │ Expiry limits, pagination offsets, rate limits       │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 5. Error Scenarios   │ Malformed JWTs, invalid signatures, non-existent IDs │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 6. Regression/Trans  │ Verification of caller modules and dependent routers │
└──────────────────────┴──────────────────────────────────────────────────────┘
```

---

## 📝 Test Implementation Anatomy & Rules

Every test method must adhere to the following template:

```python
def test_sso_token_generation_and_verification_happy_path():
    """Test standard SSO token generation and verification cycle.

    Validates: Signed JWT contains expected sub, email, and name claims.
    Dependencies: Used by WordPress sync bridge and Messenger WebSocket auth.
    """
    # --- 1. Arrange: Prepare test input data with explicit comments ---
    # User identifier from WordPress environment
    test_user_id: str = "wp_user_42"
    # User email address
    test_email: str = "test@wordpress.org"
    # User display name
    test_name: str = "WP Tester"
    # Token lifetime in hours
    test_expiry: int = 2

    # --- 2. Act: Execute function under test ---
    # Generated signed JWT token string
    token: str = create_sso_token(
        user_id=test_user_id,
        email=test_email,
        display_name=test_name,
        expiry_hours=test_expiry
    )
    # Decoded dictionary payload
    decoded: dict | None = verify_sso_token(token)

    # --- 3. Assert: Verify results with informative diagnostic messages ---
    assert token is not None, "Token generation returned None"
    assert isinstance(token, str), f"Expected token string, got {type(token)}"
    assert decoded is not None, "Failed to decode valid SSO token"
    assert decoded.get("sub") == test_user_id, f"Subject claim mismatch: {decoded.get('sub')} != {test_user_id}"
    assert decoded.get("email") == test_email, f"Email claim mismatch: {decoded.get('email')} != {test_email}"
    assert decoded.get("name") == test_name, f"Name claim mismatch: {decoded.get('name')} != {test_name}"
```

### Strict Code Constraints in Tests:
- ❌ **Forbidden:** `assert result` without a failure message.
- ❌ **Forbidden:** Anonymous undeclared magic numbers or strings passed directly into Act calls without named Arrange variables.
- ❌ **Forbidden:** Omitting type annotations on test fixture variables.
- ✅ **Required:** Triple-quote docstrings with `Validates:` and `Dependencies:` context.

---

## 📚 Post-Test Documentation Invariant

Documentation generation and synchronization are triggered **immediately upon green test completion**:

1. **Docstrings (`hypo69 docblock`):**
   - Must specify `Args`, `Returns`, `Raises` (or `Exceptions`), and `Examples`.
   - Strictly prohibit Sphinx/reST tags (`:param:`, `:returns:`).
2. **Directory Documentation (`README.md`):**
   - Каждая директория, создаваемая в `src/`, `plugins/`, `apps/` или `wp/`, должна содержать `README.md` на русском языке.
3. **Knowledge Base Synchronization:**
   - Add new routers to `.ai/instructions/knowledge/project_overview.md`.
   - Update architecture diagrams when new services or communication layers (e.g. WebSockets, WebRTC) are introduced.

---

## 🛠️ Verification Commands

```powershell
# Run specific test suite with verbose output
pytest tests/test_<module_name>.py -v

# Run with full coverage report
pytest tests/test_<module_name>.py --cov=src/<module_name> --cov-report=term-missing

# Full project regression run
.\launchers\run_tests.ps1
```
