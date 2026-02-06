# WISMO Test Suite

Comprehensive test coverage for the Shipping Delay – Neutral Status Check (WISMO) workflow.

## Test Files

| File | Description | Tests |
|------|-------------|-------|
| `test_wismo_01_basic_workflow.py` | Happy paths - all standard workflow branches | 7 tests |
| `test_wismo_02_edge_cases.py` | Edge cases - missing data, malformed inputs | 13 tests |
| `test_wismo_03_tool_failures.py` | Tool failures - network errors, API failures | 6 tests |
| `test_wismo_04_escalation_scenarios.py` | All escalation paths | 7 tests |
| `test_wismo_05_multiturn_complexity.py` | Multi-turn scenarios - memory, state persistence | 8 tests |
| `test_wismo_09_integration_real_llm.py` | Real LLM integration tests (requires API key) | 3 tests |

**Total: 44 tests**

## Final Test Results

```
pytest tests/wismo/ -v --tb=short
=================== 44 passed, 1 warning ===================
```

| Suite | File | Count | Status |
|-------|------|-------|--------|
| 01 Basic Workflow | `test_wismo_01_basic_workflow.py` | 7 | ✅ passed |
| 02 Edge Cases | `test_wismo_02_edge_cases.py` | 13 | ✅ passed |
| 03 Tool Failures | `test_wismo_03_tool_failures.py` | 6 | ✅ passed |
| 04 Escalation | `test_wismo_04_escalation_scenarios.py` | 7 | ✅ passed |
| 05 Multi-Turn | `test_wismo_05_multiturn_complexity.py` | 8 | ✅ passed |
| 09 Real LLM | `test_wismo_09_integration_real_llm.py` | 3 | ✅ passed (requires OPENAI_API_KEY) |

**Total: 44 passed** (41 mocked LLM, 3 real LLM when `OPENAI_API_KEY` is set).

## Running Tests

### All WISMO tests (mocked LLM):
```bash
pytest tests/wismo/ -v
```

### Specific test file:
```bash
pytest tests/wismo/test_wismo_01_basic_workflow.py -v
```

### Real LLM integration tests (requires OPENAI_API_KEY):
```bash
pytest tests/wismo/test_wismo_09_integration_real_llm.py -v
```

### Run with coverage:
```bash
pytest tests/wismo/ --cov=agents.wismo --cov-report=html
```

## Test Coverage

### ✅ Basic Workflow (01)
- IN_TRANSIT → wait promise set
- UNFULFILLED → explained
- DELIVERED → confirmed
- No orders → asks for ID
- Customer provides ID → resolves
- Tracking URL included
- Wait promise day calculation

### ✅ Edge Cases (02)
- Missing customer email
- Missing first_name/last_name
- Empty/very long messages
- Order ID formats (#123, NP12345, order 123, bare number)
- Unicode characters
- Email format variations

### ✅ Tool Failures (03)
- Tool returns success=false
- Tool returns malformed data
- Tool timeout
- Tool empty data
- Error message preservation

### ✅ Escalation (04)
- Missing email escalates
- Order ID not provided twice → escalates
- Missed promise date → escalates
- Escalated thread blocks replies
- Escalation summary structure

### ✅ Multi-Turn (05)
- Memory preserved
- Duplicate detection
- State persistence
- Context preservation
- Rapid successive messages
- Long conversation history

### ✅ Real LLM Integration (09)
- Real router classification
- Real LLM response generation
- Full end-to-end flow

## Test Template for Other Use Cases

To create tests for other agents (wrong_item, refund, etc.), copy this structure:

```
tests/
├── wrong_item/
│   ├── test_wrong_item_01_basic_workflow.py
│   ├── test_wrong_item_02_edge_cases.py
│   ├── test_wrong_item_03_tool_failures.py
│   ├── test_wrong_item_04_escalation_scenarios.py
│   ├── test_wrong_item_05_multiturn_complexity.py
│   └── test_wrong_item_09_integration_real_llm.py
├── refund/
│   ├── test_refund_01_basic_workflow.py
│   └── ...
└── ...
```

### Common Fixtures Pattern

All test files share these fixtures:
- `temp_db` - Isolated SQLite DB per test
- `mock_route_to_[agent]` - Bypass router, hardcode agent
- `mock_[agent]_llm` - Mock LLM response generation
- `unset_api_url` - Force mock tool responses

### Test Naming Convention

- `test_[number]_[description]` - Numbered for easy reference
- Grouped by category (01=basic, 02=edge cases, etc.)
- Descriptive names that explain what's being tested

## Hackathon Demo Checklist

Before presentation, run all tests to ensure:

- ✅ All basic workflows work
- ✅ Edge cases handled gracefully
- ✅ Tool failures escalate properly
- ✅ Escalation paths work correctly
- ✅ Multi-turn conversations maintain context
- ✅ Real LLM integration works (if API key available)

Run: `pytest tests/wismo/ -v --tb=short`
