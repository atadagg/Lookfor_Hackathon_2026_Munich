# Hackathon API Reference - All 18 Tools

## Configuration

Set the API URL in `.env`:
```bash
API_URL=https://lookfor-hackathon-backend.onrender.com
```

All endpoints use the base path: `{API_URL}/hackathon/...`

---

## 🛍️ Shopify Tools (13 tools)

### 1. Add Tags
**Endpoint:** `POST {API_URL}/hackathon/add_tags`

**Description:** Add tags to an order, customer, product, or other Shopify resource.

**Request Body:**
```json
{
  "id": "gid://shopify/Order/123456",
  "tags": ["Wrong or Missing, Store Credit Issued"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {},
  "error": null
}
```

---

### 2. Cancel Order
**Endpoint:** `POST {API_URL}/hackathon/cancel_order`

**Description:** Cancel an order with reason and refund options.

**Request Body:**
```json
{
  "orderId": "gid://shopify/Order/123456",
  "reason": "CUSTOMER",
  "notifyCustomer": true,
  "restock": true,
  "staffNote": "Customer requested cancellation",
  "refundMode": "ORIGINAL",
  "storeCredit": {
    "expiresAt": null
  }
}
```

**Parameters:**
- `reason`: `"CUSTOMER" | "DECLINED" | "FRAUD" | "INVENTORY" | "OTHER" | "STAFF"`
- `refundMode`: `"ORIGINAL" | "STORE_CREDIT"`

---

### 3. Create Discount Code
**Endpoint:** `POST {API_URL}/hackathon/create_discount_code`

**Description:** Create a discount code (percentage or fixed amount).

**Request Body:**
```json
{
  "type": "percentage",
  "value": 0.1,
  "duration": 48,
  "productIds": []
}
```

**Parameters:**
- `type`: `"percentage"` (0-1) or `"fixed"` (absolute amount)
- `value`: If percentage, 0-1 (e.g., 0.1 = 10%); if fixed, currency amount
- `duration`: Validity in hours
- `productIds`: Array of product GIDs (empty for order-wide)

**Response:**
```json
{
  "success": true,
  "data": {
    "code": "NATPAT10"
  },
  "error": null
}
```

---

### 4. Create Return
**Endpoint:** `POST {API_URL}/hackathon/create_return`

**Description:** Create a return for an order.

**Request Body:**
```json
{
  "orderId": "gid://shopify/Order/123456"
}
```

---

### 5. Create Store Credit
**Endpoint:** `POST {API_URL}/hackathon/create_store_credit`

**Description:** Issue store credit to a customer.

**Request Body:**
```json
{
  "id": "gid://shopify/Customer/123456",
  "creditAmount": {
    "amount": "49.99",
    "currencyCode": "USD"
  },
  "expiresAt": null
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "storeCreditAccountId": "gid://shopify/StoreCreditAccount/...",
    "credited": {
      "amount": "49.99",
      "currencyCode": "USD"
    },
    "newBalance": {
      "amount": "99.99",
      "currencyCode": "USD"
    }
  },
  "error": null
}
```

---

### 6. Get Collection Recommendations
**Endpoint:** `POST {API_URL}/hackathon/get_collection_recommendations`

**Description:** Get collection recommendations based on keywords.

**Request Body:**
```json
{
  "queryKeys": ["sleep", "kids", "patches"]
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "gid://shopify/Collection/1",
      "title": "Sleep Solutions",
      "handle": "sleep-solutions"
    }
  ],
  "error": null
}
```

---

### 7. Get Customer Orders
**Endpoint:** `POST {API_URL}/hackathon/get_customer_orders`

**Description:** Get a customer's orders by email with pagination.

**Request Body:**
```json
{
  "email": "customer@example.com",
  "after": "null",
  "limit": 10
}
```

**Parameters:**
- `after`: Cursor for pagination, use `"null"` for first page
- `limit`: Number of orders (max 250)

**Response:**
```json
{
  "success": true,
  "data": {
    "orders": [
      {
        "id": "gid://shopify/Order/5531567751245",
        "name": "#1001",
        "createdAt": "2026-02-06T22:00:00Z",
        "status": "FULFILLED",
        "trackingUrl": "https://tracking.example.com/demo123"
      }
    ],
    "hasNextPage": false,
    "endCursor": null
  },
  "error": null
}
```

---

### 8. Get Order Details
**Endpoint:** `POST {API_URL}/hackathon/get_order_details`

**Description:** Fetch detailed information for a single order.

**Request Body:**
```json
{
  "orderId": "#1234"
}
```

**Note:** Order ID must start with `#`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "gid://shopify/Order/5531567751245",
    "name": "#1234",
    "createdAt": "2026-02-06T22:00:00Z",
    "status": "FULFILLED",
    "trackingUrl": "https://tracking.example.com/1234"
  },
  "error": null
}
```

---

### 9. Get Product Details
**Endpoint:** `POST {API_URL}/hackathon/get_product_details`

**Description:** Look up product information by ID, name, or key feature.

**Request Body:**
```json
{
  "queryType": "name",
  "queryKey": "BuzzPatch"
}
```

**Parameters:**
- `queryType`: `"id" | "name" | "key feature"`
- `queryKey`: Search term (if `queryType` is `"id"`, must be Shopify Product GID)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "gid://shopify/Product/9",
      "title": "BuzzPatch",
      "handle": "buzzpatch"
    }
  ],
  "error": null
}
```

---

### 10. Get Product Recommendations
**Endpoint:** `POST {API_URL}/hackathon/get_product_recommendations`

**Description:** Get product recommendations based on keywords.

**Request Body:**
```json
{
  "queryKeys": ["sleep", "kids"]
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "gid://shopify/Product/10",
      "title": "SleepyPatch",
      "handle": "sleepypatch"
    }
  ],
  "error": null
}
```

---

### 11. Get Related Knowledge Source
**Endpoint:** `POST {API_URL}/hackathon/get_related_knowledge_source`

**Description:** Retrieve FAQs, PDFs, blog articles, and pages related to a question.

**Request Body:**
```json
{
  "question": "How do I apply the patches?",
  "specificToProductId": "gid://shopify/Product/9"
}
```

**Parameters:**
- `specificToProductId`: Product GID or `null` if not product-specific

**Response:**
```json
{
  "success": true,
  "data": {
    "faqs": [],
    "pdfs": [],
    "blogArticles": [],
    "pages": []
  },
  "error": null
}
```

---

### 12. Refund Order
**Endpoint:** `POST {API_URL}/hackathon/refund_order`

**Description:** Refund an order to original payment method or store credit.

**Request Body:**
```json
{
  "orderId": "gid://shopify/Order/123456",
  "refundMethod": "ORIGINAL_PAYMENT_METHODS"
}
```

**Parameters:**
- `refundMethod`: `"ORIGINAL_PAYMENT_METHODS" | "STORE_CREDIT"`

---

### 13. Update Order Shipping Address
**Endpoint:** `POST {API_URL}/hackathon/update_order_shipping_address`

**Description:** Update an order's shipping address.

**Request Body:**
```json
{
  "orderId": "gid://shopify/Order/123456",
  "shippingAddress": {
    "firstName": "John",
    "lastName": "Doe",
    "company": "",
    "address1": "123 Main St",
    "address2": "Apt 4B",
    "city": "New York",
    "provinceCode": "NY",
    "country": "US",
    "zip": "10001",
    "phone": "+1234567890"
  }
}
```

---

## 📦 Skio Subscription Tools (5 tools)

### 14. Cancel Subscription
**Endpoint:** `POST {API_URL}/hackathon/cancel-subscription`

**Description:** Cancel a subscription.

**Request Body:**
```json
{
  "subscriptionId": "sub_123456",
  "cancellationReasons": ["Too expensive", "Not using it enough"]
}
```

---

### 15. Get Subscriptions
**Endpoint:** `POST {API_URL}/hackathon/get-subscriptions`

**Description:** Get all subscriptions of a customer by email.

**Request Body:**
```json
{
  "email": "customer@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "status": "CANCELLED",
      "subscriptionId": "sub_122",
      "nextBillingDate": null
    },
    {
      "status": "PAUSED",
      "subscriptionId": "sub_123",
      "nextBillingDate": "2026-05-01"
    },
    {
      "status": "ACTIVE",
      "subscriptionId": "sub_124",
      "nextBillingDate": "2026-03-01"
    }
  ],
  "error": null
}
```

**Note:** Returns an array of all customer subscriptions with different statuses.

---

### 16. Pause Subscription
**Endpoint:** `POST {API_URL}/hackathon/pause-subscription`

**Description:** Pause a subscription until a specific date.

**Request Body:**
```json
{
  "subscriptionId": "sub_123456",
  "pausedUntil": "2026-03-01"
}
```

**Parameters:**
- `pausedUntil`: Date in `YYYY-MM-DD` format

---

### 17. Skip Next Order
**Endpoint:** `POST {API_URL}/hackathon/skip-next-order-subscription`

**Description:** Skip the next order of an ongoing subscription.

**Request Body:**
```json
{
  "subscriptionId": "sub_123456"
}
```

---

### 18. Unpause Subscription
**Endpoint:** `POST {API_URL}/hackathon/unpause-subscription`

**Description:** Unpause a paused subscription.

**Request Body:**
```json
{
  "subscriptionId": "sub_123456"
}
```

---

## 🧪 Testing with Real API

### 1. Set API URL in `.env`
```bash
# In backend/.env
API_URL=https://lookfor-hackathon-backend.onrender.com
```

### 2. Restart Backend
```bash
cd backend
uvicorn api.server:app --reload
```

### 3. Test Individual Tool (Python)
```python
import asyncio
from tools.shopify import shopify_add_tags

async def test():
    result = await shopify_add_tags(
        id="gid://shopify/Order/123456",
        tags=["Test Tag"]
    )
    print(result)

asyncio.run(test())
```

### 4. Test via Chat API
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-api-001",
    "user_id": "user-001",
    "customer_email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "shopify_customer_id": "cust-001",
    "message": "I need a 10% discount code"
  }'
```

### 5. Check Tool Execution
Look for `tool_traces` in the response:
```json
{
  "state": {
    "internal_data": {
      "tool_traces": [
        {
          "name": "create_discount_10_percent",
          "inputs": {},
          "output": {
            "success": true,
            "data": {"code": "NATPAT10"}
          }
        }
      ]
    }
  }
}
```

---

## 📊 Tool Usage by Agent

| Agent | Tools Used |
|-------|-----------|
| **WISMO** | get_customer_orders, get_order_details |
| **Wrong Item** | get_customer_orders, get_order_details, add_tags, create_store_credit, refund_order |
| **Product Issue** | get_customer_orders, get_order_details, get_product_details, get_related_knowledge_source, create_return |
| **Refund** | get_customer_orders, refund_order, add_tags |
| **Order Mod** | get_customer_orders, cancel_order, update_order_shipping_address |
| **Feedback** | add_tags, get_product_recommendations |
| **Subscription** | get_subscriptions, skip_next_order, pause_subscription, cancel_subscription, unpause_subscription |
| **Discount** | create_discount_code |

---

## 🔍 Error Handling

All tools return this standard format:
```json
{
  "success": boolean,
  "data": object | array,
  "error": string | null
}
```

**Common Errors:**
- `"API_URL is not configured"` - Set `API_URL` in `.env`
- `"HTTP error: ..."` - Network/connection issue
- `"Non-200 from {url}: {status}"` - API returned error status
- `"Invalid JSON: ..."` - API response not valid JSON

---

## 📝 Notes

- All endpoints now use correct spelling: `/hackathon/...` (not `hackhaton`)
- Mock mode: If `API_URL` is not set, tools return mock data
- Real mode: If `API_URL` is set, tools call the actual hackathon API
- All tools are async and use `httpx` for HTTP requests
- 15-second timeout on all API calls

---

## 🚀 Ready to Test!

Your backend is now configured to use the real hackathon API endpoints. Set the `API_URL` in your `.env` file and restart the server to test with real data.
