# Showcase Testing Notes

## Known Issue: 404 Errors from API

The Showcase feature uses anonymized customer IDs from real tickets, but these customers don't exist in the Shopify system. This causes 404 errors when agents try to look up orders.

### Why This Happens

1. Showcase tickets use fake customer IDs: `cust_b1f341ae`, `cust_9c3d8a2b`, etc.
2. These are sent as: `cust_b1f341ae@example.com`
3. Backend API tries to fetch orders for these non-existent customers
4. Shopify returns 404 - customer not found
5. Agent escalates due to tool error

### Solution Applied

Updated all showcase ticket messages to **prominently include order numbers** (NP format). This allows the agent to:

1. Detect order number in the message
2. Use `get_order_by_id` tool instead of `get_customer_orders`
3. Look up orders directly by ID (which may work better than customer email)

### Examples Updated

- "Where is my order?" → "Where is my order NP8073419?"
- "Request refund" → "Request refund for order NP8523147"
- "Cancel my order" → "Cancel order NP9012345"
- All messages now include order number in subject AND body

### Expected Behavior

With order numbers prominent:
- ✅ Agent should detect order ID from message
- ✅ Use `get_order_by_id(order_id="NP8073419")`
- ⚠️ May still fail if order doesn't exist in system
- ⚠️ Agents may still try customer email first

### Alternative Solutions

If 404 errors persist:

1. **Use real customer emails** from your Shopify store
2. **Mock the API responses** for showcase customers
3. **Add test customers** to Shopify with known order history
4. **Handle 404 gracefully** in agent logic (treat as "no orders found")

### Test Customers (from CURL tests)

These might work better if they exist in your system:
```
- transit@test.com
- unfulfilled@test.com
- delivered@test.com
- noorders@test.com
```

Consider replacing showcase customer emails with these test emails.
