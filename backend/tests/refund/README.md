# Refund Request (UC4) Test Suite

Comprehensive test coverage for the Refund Request agent.

## Test Structure

```
tests/refund/
├── ROADMAP.md                              # Spec & requirements
├── conftest.py                              # Shared fixtures
├── test_refund_01_basic_workflow.py         # 7 tests - Core workflows (expectations, shipping, damaged, changed mind)
├── test_refund_02_edge_cases.py             # 4 tests - Edge cases (unicode, missing data, long messages)
├── test_refund_03_tool_failures.py          # 3 tests - Tool failure handling
├── test_refund_04_escalation_scenarios.py   # 3 tests - Escalation logic
├── test_refund_05_multiturn_complexity.py   # 4 tests - Multi-turn conversations
└── test_refund_09_integration_real_llm.py   # 2 tests - Real LLM integration
```

**Total: 23 tests**

## Running Tests

```bash
# All tests (unit + integration)
pytest tests/refund/ -v

# Unit tests only (mocked LLM, no API calls)
pytest tests/refund/ -v -k "not integration"

# Integration tests only (requires OPENAI_API_KEY)
pytest tests/refund/ -v -k "integration"

# Single suite
pytest tests/refund/test_refund_01_basic_workflow.py -v

# Single test
pytest tests/refund/test_refund_01_basic_workflow.py::test_01_01_refund_expectations_route -v
```

## Test Coverage

### 01_basic_workflow.py (7 tests)
- ✅ Route A: Product didn't meet expectations → cash refund
- ✅ Route D: Changed mind (fulfilled) → store credit or cash
- ✅ Store credit tagging
- ✅ Cash refund tagging
- ✅ Route B: Shipping delay → escalation
- ✅ Route C: Damaged item → escalation or store credit
- ✅ Multi-turn: Ask reason → Store credit

### 02_edge_cases.py (4 tests)
- ✅ Missing customer email → escalate
- ✅ Unicode customer name handling
- ✅ Very long customer message
- ✅ Empty message handling

### 03_tool_failures.py (3 tests)
- ✅ Order lookup failure → graceful escalation
- ✅ Refund tool failure → graceful handling
- ✅ Store credit tool failure → tool_traces logging

### 04_escalation_scenarios.py (3 tests)
- ✅ Shipping delay → escalate to Monica
- ✅ Damaged product → escalate for replacement
- ✅ No orders found → escalate

### 05_multiturn_complexity.py (4 tests)
- ✅ 3-turn: Request → Reason → Accept credit
- ✅ Change mind mid-conversation (credit → cash)
- ✅ Escalation persists across turns
- ✅ 4-turn expectations flow (swap decline → credit)

### 09_integration_real_llm.py (2 tests)
- ✅ Real LLM: Full refund conversation (expectations route)
- ✅ Real LLM: Changed mind refund

## Key Scenarios Tested

### Refund Routes

| Route | Trigger | Expected Behavior | Tests |
|-------|---------|-------------------|-------|
| **A: Expectations** | Product didn't work | Usage tip → Swap → Credit+bonus → Cash | 01_01, 05_04 |
| **B: Shipping Delay** | Late delivery | Wait promise → Free replacement → Escalate to Monica | 01_05, 04_01 |
| **C: Damaged/Wrong** | Physical issue | Free replacement OR credit+bonus → Escalate if replacement | 01_06, 04_02 |
| **D: Changed Mind** | Buyer's remorse | Cancel (unfulfilled) OR credit+bonus → Cash if declined | 01_02, 09_02 |

### Tool Usage
- **get_customer_latest_order**: Order lookup (all routes)
- **cancel_order**: Route D for unfulfilled orders
- **refund_order_cash**: Routes A & D after declining store credit
- **create_store_credit**: Routes A, C, D (with 10% bonus)
- **add_order_tags**: All successful resolutions

### Escalation Triggers
- ✅ No email provided
- ✅ Order lookup fails
- ✅ No orders found
- ✅ Shipping delay + refuse to wait
- ✅ Damaged/wrong item + choose replacement
- ✅ Fulfilled order cancellation attempt

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `temp_db` | Isolated test database (cleaned after each test) |
| `mock_route_to_refund` | Forces router to select refund agent |
| `unset_api_url` | Ensures mock mode (no real Shopify calls) |
| `payload_refund()` | Helper to build test payloads |
| `post_chat()` | Helper to POST to /chat endpoint |

## Mock Behavior

When `API_URL` is unset:
- **get_customer_latest_order**: Returns mock order data (FULFILLED, fulfillment date, order number)
- **refund_order_cash**: Returns success with mock transaction ID
- **create_store_credit**: Returns success with bonus amount
- **cancel_order**: Returns success
- **add_order_tags**: Returns success

## Integration Tests (09)

⚠️ **Requirements:**
- `OPENAI_API_KEY` must be set
- Real LLM calls (costs $$)
- Tests real routing and response generation

Skip integration tests during development:
```bash
pytest tests/refund/ -k "not integration"
```

## Test Results

**Last Run:** February 6, 2026

### Unit Tests (without real LLM)

| Suite | Result |
|-------|--------|
| 01_basic_workflow | ✅ 7 passed |
| 02_edge_cases | ✅ 4 passed |
| 03_tool_failures | ✅ 3 passed |
| 04_escalation_scenarios | ✅ 3 passed |
| 05_multiturn_complexity | ✅ 4 passed |
| 09_integration | ⏭️ 2 skipped |
| **TOTAL** | **✅ 21 passed, 2 deselected** |

**Time:** ~36 seconds

### Integration Tests (with real LLM)

| Suite | Result |
|-------|--------|
| 09_integration | ✅ 2 passed |
| **TOTAL** | **✅ 23 passed** |

**Time:** ~40 seconds

## Definition of Done

- [ ] All unit tests pass (21/21)
- [ ] Integration tests pass with real LLM (2/2)
- [ ] Router correctly identifies refund intents
- [ ] All refund routes (A, B, C, D) work correctly
- [ ] Store credit offered first (with 10% bonus)
- [ ] Cash refund as fallback
- [ ] Proper escalation for shipping/damaged scenarios
- [ ] Tags applied for all outcomes
- [ ] Tool failures handled gracefully
- [ ] Multi-turn conversations maintain state

## Troubleshooting

**Import errors:**
```bash
# Make sure you're in backend/ directory
cd backend
pytest tests/refund/ -v
```

**Database errors:**
```bash
# Temp DB fixture should auto-cleanup
# If issues persist, check temp_db fixture in conftest.py
```

**Tool not found errors:**
```bash
# Verify tools are imported in agents/refund/graph.py
# Check tool names match exactly in graph nodes
```

## Related Files

- `backend/agents/refund/graph.py` - Agent logic
- `backend/agents/refund/tools.py` - Refund-specific tools
- `backend/agents/refund/prompts.py` - System prompts
- `backend/tests/TEMPLATE_AGENT_TESTS.py` - Test template
- `backend/tests/refund/ROADMAP.md` - Full requirements

---

**Author:** Fidelio Team  
**Date:** February 2026  
**Hackathon:** LookFor AI Challenge
