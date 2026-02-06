# Subscription Management (UC7) Test Suite

Comprehensive test coverage for the Subscription Management agent.

## Test Structure

```
tests/subscription/
├── ROADMAP.md                                   # Spec & requirements
├── conftest.py                                   # Shared fixtures
├── test_subscription_01_basic_workflow.py        # 5 tests - Core subscription flows
├── test_subscription_02_edge_cases.py            # 2 tests - Edge cases
└── test_subscription_09_integration_real_llm.py  # 1 test  - Real LLM integration
```

**Total: 8 tests**

## Running Tests

```bash
# All tests
pytest tests/subscription/ -v

# Unit tests only
pytest tests/subscription/ -v -k "not integration"

# Integration tests only
pytest tests/subscription/ -v -k "integration"
```

## Test Coverage

### 01_basic_workflow.py (5 tests)
- ✅ Cancel request routes correctly
- ✅ Skip next order request
- ✅ Billing issue → escalate immediately
- ✅ Pause subscription request
- ✅ "Too many on hand" → skip/discount flow

### 02_edge_cases.py (2 tests)
- ✅ Missing email → escalate
- ✅ Credit card update → escalate

### 09_integration_real_llm.py (1 test)
- ✅ Real LLM: Cancel request

## Key Scenarios Tested

### Subscription Flows

| Route | Trigger | Expected Behavior | Tests |
|-------|---------|-------------------|-------|
| **A: Too Many** | Too many on hand | Skip offer → 20% discount → Cancel | 01_02, 01_05 |
| **B: Quality** | Didn't like product | Product swap → Cancel | - |
| **C: Billing** | Double charge | Escalate to Monica immediately | 01_03 |
| **D: Credit Card** | Update CC | Escalate to Monica (can't update via API) | 02_02 |
| **E: Pause** | Pause request | Pause subscription with date | 01_04 |

### Tool Usage
- **skio_get_subscription_status**: Check subscription (all routes)
- **skio_skip_next_order_subscription**: Route A - skip offer
- **shopify_create_discount_code**: Route A - 20% retention discount
- **shopify_get_product_recommendations**: Route B - product swap
- **skio_cancel_subscription**: Routes A, B - cancellation
- **skio_pause_subscription**: Route E - pause
- **shopify_add_tags**: Tag subscription actions

### Escalation Triggers
- ✅ No email provided
- ✅ Billing issues (double charge, unexpected charge)
- ✅ Credit card update requests
- ✅ Subscription lookup fails

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `temp_db` | Isolated test database |
| `mock_route_to_subscription` | Forces router to subscription agent |
| `unset_api_url` | Ensures mock mode |
| `payload_subscription()` | Helper to build test payloads |
| `post_chat()` | Helper to POST to /chat |

## Test Results

**Last Run:** February 6, 2026

### Unit Tests (without real LLM)

| Suite | Result | Status |
|-------|--------|--------|
| 01_basic_workflow | ✅ 5/5 passed | Cancel, skip, billing, pause flows |
| 02_edge_cases | ✅ 2/2 passed | No email, CC update |
| 09_integration | ⏭️ 1 deselected | Awaiting OPENAI_API_KEY |
| **TOTAL** | **✅ 7 passed, 1 deselected** | 2 warnings |

**Time:** 18.06 seconds

**Status:** ✅ **All tests passing!**

Run tests with:
```bash
cd backend
pytest tests/subscription/ -v -k "not integration"
```

**Expected:** All 7 tests should pass once agent is verified

## Definition of Done

- [ ] All unit tests pass (7/7)
- [ ] Integration test passes (1/1)
- [ ] Router identifies subscription intents correctly
- [ ] Skip flow works correctly
- [ ] 20% discount retention offer works
- [ ] Product swap recommendations work
- [ ] Billing/CC issues escalate properly
- [ ] Pause functionality works
- [ ] Cancellation only after retention attempts
- [ ] Tags applied for all actions

## Related Files

- `backend/agents/subscription/graph.py` - Agent logic (ConversationalAgent)
- `backend/agents/subscription/prompts.py` - System prompts
- `backend/tools/skio.py` - Skio subscription tools
- `backend/tests/subscription/ROADMAP.md` - Full requirements

---

**Author:** Fidelio Team  
**Date:** February 2026  
**Hackathon:** LookFor AI Challenge
