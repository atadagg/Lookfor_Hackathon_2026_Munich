# Wrong / Missing Item Test Suite (UC2)

Test-driven roadmap for the **Wrong / Missing Item in Parcel** use case. Tests define the MUST-HAVE behavior; implementation should be updated until all tests pass.

## Final Test Results

```
pytest tests/wrong_item/ -v
======================================= 13 passed, 1 warning =======================================
```

| Suite | File | Count | Status |
|-------|------|-------|--------|
| 01 Basic Workflow | `test_wrong_item_01_basic_workflow.py` | 5 | ✅ passed |
| 02 Edge Cases | `test_wrong_item_02_edge_cases.py` | 3 | ✅ passed |
| 03 Tool Failures | `test_wrong_item_03_tool_failures.py` | 1 | ✅ passed |
| 04 Escalation | `test_wrong_item_04_escalation_scenarios.py` | 1 | ✅ passed |
| 05 Multi-Turn | `test_wrong_item_05_multiturn_complexity.py` | 2 | ✅ passed |
| 09 Real LLM | `test_wrong_item_09_integration_real_llm.py` | 1 | ✅ passed (requires OPENAI_API_KEY) |

**Total: 13 passed** (12 mocked LLM, 1 real LLM when `OPENAI_API_KEY` is set).

## ROADMAP

See **[ROADMAP.md](./ROADMAP.md)** for the full workflow specification (Steps 1–7, tools, escalation, tags).

## Test Files

| File | Purpose |
|------|---------|
| `test_wrong_item_01_basic_workflow.py` | Routing, order lookup, apology/photo ask (Steps 1–3) |
| `test_wrong_item_02_edge_cases.py` | Missing data, empty message, unicode |
| `test_wrong_item_03_tool_failures.py` | Tool failure handling (stub) |
| `test_wrong_item_04_escalation_scenarios.py` | Escalation message (reship → Monica/support) |
| `test_wrong_item_05_multiturn_complexity.py` | Multi-turn, duplicate detection |
| `test_wrong_item_09_integration_real_llm.py` | Real LLM (requires OPENAI_API_KEY) |

## Running Tests

From `backend/`:

```bash
pytest tests/wrong_item/ -v
```

With real LLM (optional):

```bash
pytest tests/wrong_item/test_wrong_item_09_integration_real_llm.py -v
```

## Definition of Done

- All tests in `tests/wrong_item/` pass.
- ROADMAP.md checkboxes satisfied by the wrong_item agent implementation.
- Reship path escalates; store credit/refund use correct tools and tags.
