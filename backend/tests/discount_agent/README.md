# Discount Code Request (UC8) Test Suite

Comprehensive test coverage for the Discount Code Request agent.

## Test Structure

```
tests/discount_agent/
├── ROADMAP.md                                   # Spec & requirements
├── conftest.py                                   # Shared fixtures
├── test_discount_01_basic_workflow.py            # 5 tests - Code creation & delivery
├── test_discount_02_edge_cases.py                # 3 tests - Polite, short, specific percentage requests
├── test_discount_03_tool_failures.py             # 2 tests - Tool failure handling
├── test_discount_04_escalation_scenarios.py      # 2 tests - Escalation logic
├── test_discount_05_multiturn_complexity.py      # 3 tests - Multi-turn conversations
└── test_discount_09_integration_real_llm.py      # 1 test  - Real LLM integration
```

**Total: 16 tests**

## Running Tests

```bash
# All tests
pytest tests/discount_agent/ -v

# Unit tests only
pytest tests/discount_agent/ -v -k "not integration"

# Integration tests only
pytest tests/discount_agent/ -v -k "integration"
```

## Test Coverage

### 01_basic_workflow.py (5 tests)
- ✅ Simple discount request
- ✅ Discount creation tool called
- ✅ Reply contains code (NATPAT10-)
- ✅ No duplicate codes per conversation
- ✅ Usage instructions included

### 02_edge_cases.py (3 tests)
- ✅ Polite discount request
- ✅ Very short request ("Discount?")
- ✅ Specific percentage request (20% → get 10%)

### 03_tool_failures.py (2 tests)
- ✅ Discount creation failure → graceful handling
- ✅ Multiple tool failures → still responds

### 04_escalation_scenarios.py (2 tests)
- ✅ Normal request → no escalation
- ✅ Tool failure → escalate to Monica

### 05_multiturn_complexity.py (3 tests)
- ✅ 2-turn clarification flow
- ✅ Code creation remembered across turns
- ✅ 3-turn state persistence

### 09_integration_real_llm.py (1 test)
- ✅ Real LLM: Discount code request

## Key Scenarios Tested

### Discount Code Creation

| Step | Action | Expected Behavior | Tests |
|------|--------|-------------------|-------|
| **1. Check** | Check if code already created | Read `internal_data.code_created` | 01_04, 05_02 |
| **2. Create** | Create 10% discount code | Call `shopify_create_discount_code` | 01_02, 01_03 |
| **3. Respond** | Send code with instructions | Include code + how to use | 01_05, 09_01 |

### Code Format
```
NATPAT10-{random}
```
- **Percentage:** 10% off
- **Usage:** Single use per customer
- **Prefix:** NATPAT10-

### Required Elements in Response
- ✅ Discount code (NATPAT10-XXXXX)
- ✅ How to use at checkout
- ✅ Single-use limitation mentioned

### Tool Usage
- **create_discount_10_percent**: Creates Shopify discount code

### Important Constraints
- **No duplicates**: Don't create multiple codes for same conversation
- **Always 10%**: Even if customer asks for different percentage
- **Single-use**: Code works once per customer

### Escalation Triggers
- ✅ Tool failure (Shopify API down)
- ❌ Normal request (no escalation)

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `temp_db` | Isolated test database |
| `mock_route_to_discount` | Forces router to discount agent |
| `unset_api_url` | Ensures mock mode |
| `payload_discount()` | Helper to build test payloads |
| `post_chat()` | Helper to POST to /chat |

## Mock Behavior

When `API_URL` is unset:
- **create_discount_10_percent**: Returns mock code `NATPAT10-MOCK12345`

## Test Results

**Last Run:** February 6, 2026

### Unit Tests (without real LLM)

| Suite | Result | Status |
|-------|--------|--------|
| 01_basic_workflow | ✅ 5/5 passed | Code creation, no duplicates |
| 02_edge_cases | ✅ 3/3 passed | Polite, short, specific % |
| 03_tool_failures | ✅ 2/2 passed | Graceful failures |
| 04_escalation_scenarios | ✅ 2/2 passed | No escalation + tool failures |
| 05_multiturn_complexity | ✅ 3/3 passed | State persistence |
| 09_integration | ⏭️ 1 deselected | Awaiting OPENAI_API_KEY |
| **TOTAL** | **✅ 15 passed, 1 deselected** | 2 warnings |

**Time:** 28.56 seconds

**Status:** ✅ **All Tests Passing!**

### What Was Fixed
- ✅ Added `last_assistant_message` to state
- ✅ Added `code_created` flag to internal_data
- ✅ Fixed `current_workflow` field name ("discount_code")
- ✅ LangGraph implementation with proper tool calls
- ✅ Code duplication prevention logic

### Agent Features
- ✅ Creates 10% discount codes (NATPAT10-XXXXX format)
- ✅ Prevents duplicate codes per conversation
- ✅ 48-hour validity, single-use
- ✅ Graceful error handling
- ✅ Clear usage instructions

**Run tests to verify:**
```bash
cd backend
pytest tests/discount_agent/ -v -k "not integration"
```

## Definition of Done

- [ ] All unit tests pass (15/15)
- [ ] Integration test passes (1/1)
- [ ] Router identifies discount requests correctly
- [ ] Discount code created (NATPAT10- format)
- [ ] 10% off, single use
- [ ] No duplicate codes per conversation
- [ ] Clear usage instructions provided
- [ ] Tool failures escalate appropriately

## Example Response

```
Hi Alex! 😊

I'd be happy to help with that! Here's a special 10% discount code just for you:

**NATPAT10-ABC123**

Simply enter this code at checkout to get 10% off your order.

Please note: This code is for single use only.

Happy shopping! 🎉

Caz
```

---

**Author:** Fidelio Team  
**Date:** February 2026
