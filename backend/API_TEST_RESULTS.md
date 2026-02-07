# Hackathon API Test Results

**Test Date:** 2026-02-07 11:26:12
**API URL:** Not set (MOCK mode)
**Backend URL:** http://localhost:8000

## 📊 Summary

- **Total Tests:** 7
- **Passed:** 0 ✅
- **Failed:** 7 ❌
- **Real API Calls:** 0 🌐
- **Mock Calls:** 7 🏠

## 📝 Detailed Results

### UC1: WISMO

**Test ID:** `uc1_wismo_01`  
**Description:** Customer asks about order status  
**Status:** ❌ FAIL  
**Error:** All connection attempts failed  

---

### UC2: Wrong Item

**Test ID:** `uc2_wrong_item_01`  
**Description:** Customer received wrong item  
**Status:** ❌ FAIL  
**Error:** All connection attempts failed  

---

### UC3: Product Issue

**Test ID:** `uc3_product_issue_01`  
**Description:** Product not working as expected  
**Status:** ❌ FAIL  
**Error:** All connection attempts failed  

---

### UC4: Refund Request

**Test ID:** `uc4_refund_01`  
**Description:** Customer requests refund  
**Status:** ❌ FAIL  
**Error:** All connection attempts failed  

---

### UC5: Order Modification

**Test ID:** `uc5_order_mod_01`  
**Description:** Customer wants to cancel order  
**Status:** ❌ FAIL  
**Error:** All connection attempts failed  

---

### UC7: Subscription

**Test ID:** `uc7_subscription_01`  
**Description:** Customer asks about subscription  
**Status:** ❌ FAIL  
**Error:** All connection attempts failed  

---

### UC8: Discount Request

**Test ID:** `uc8_discount_01`  
**Description:** Customer asks for discount code  
**Status:** ❌ FAIL  
**Error:** All connection attempts failed  

---

## 🔧 Tool Execution Summary

| Use Case | Agent | Tools Called | API Status |
|----------|-------|--------------|------------|
| UC1: WISMO | - | - | ❌ Error |
| UC2: Wrong Item | - | - | ❌ Error |
| UC3: Product Issue | - | - | ❌ Error |
| UC4: Refund Request | - | - | ❌ Error |
| UC5: Order Modification | - | - | ❌ Error |
| UC7: Subscription | - | - | ❌ Error |
| UC8: Discount Request | - | - | ❌ Error |

## 💡 Recommendations

⚠️  **API_URL not configured** - All tests ran in MOCK mode

To test with real API:
1. Set `API_URL=https://lookfor-hackathon-backend.onrender.com` in `.env`
2. Restart backend: `uvicorn api.server:app --reload`
3. Run tests again

⚠️  **7 test(s) failed** - Review error details above

---

**Test Configuration:**
- Backend: `http://localhost:8000`
- API: `Not set`
- Database: Temporary (tests do not affect main state.db)
