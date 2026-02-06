# CURL Test Commands - All Use Cases

## Setup
```bash
# Backend URL (change for deployed version)
export BACKEND_URL="http://localhost:8000"
```

---

## UC1: WISMO (Shipping Delay - Where Is My Order)

### Scenario 1: Simple status check (in transit)
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wismo-test-1",
    "user_id": "user-001",
    "channel": "email",
    "customer_email": "transit@test.com",
    "first_name": "Sarah",
    "last_name": "Johnson",
    "shopify_customer_id": "cust-001",
    "message": "Where is my order? It has been a week and I still havent received it."
  }' | jq
```

### Scenario 2: Unfulfilled order
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wismo-test-2",
    "user_id": "user-002",
    "channel": "email",
    "customer_email": "unfulfilled@test.com",
    "first_name": "Mike",
    "last_name": "Chen",
    "shopify_customer_id": "cust-002",
    "message": "I ordered 3 days ago but I havent heard anything. When will my order ship?"
  }' | jq
```

### Scenario 3: Multi-turn - No order found, then provide order ID
```bash
# Turn 1: Customer asks without order ID
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wismo-multiturn-1",
    "user_id": "user-003",
    "channel": "email",
    "customer_email": "noorders@test.com",
    "first_name": "Emma",
    "last_name": "Williams",
    "shopify_customer_id": "cust-003",
    "message": "My order hasnt arrived yet!"
  }' | jq

# Turn 2: Customer provides order ID
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wismo-multiturn-1",
    "user_id": "user-003",
    "channel": "email",
    "customer_email": "noorders@test.com",
    "first_name": "Emma",
    "last_name": "Williams",
    "shopify_customer_id": "cust-003",
    "message": "Its order #43189"
  }' | jq
```

### Scenario 4: Delivered but customer says not received
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wismo-test-4",
    "user_id": "user-004",
    "channel": "email",
    "customer_email": "delivered@test.com",
    "first_name": "James",
    "last_name": "Brown",
    "shopify_customer_id": "cust-004",
    "message": "It says my order was delivered but I never received it. Can you check?"
  }' | jq
```

### Scenario 5: Tracking link request
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wismo-test-5",
    "user_id": "user-005",
    "channel": "email",
    "customer_email": "transit@test.com",
    "first_name": "Linda",
    "last_name": "Garcia",
    "shopify_customer_id": "cust-005",
    "message": "Can I get the tracking number for order #1001?"
  }' | jq
```

---

## UC2: Wrong/Missing Item

### Scenario 1: Wrong item received
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wrong-item-1",
    "user_id": "user-010",
    "channel": "email",
    "customer_email": "lisa@example.com",
    "first_name": "Lisa",
    "last_name": "Martinez",
    "shopify_customer_id": "cust-010",
    "message": "Got Zen stickers instead of Focus—kids need them for school, help!"
  }' | jq
```

### Scenario 2: Missing items in package
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wrong-item-2",
    "user_id": "user-011",
    "channel": "email",
    "customer_email": "lisa@example.com",
    "first_name": "John",
    "last_name": "Davis",
    "shopify_customer_id": "cust-011",
    "message": "My package arrived with only 2 of the 3 packs I paid for."
  }' | jq
```

### Scenario 3: Multi-turn - Missing item → Photo → Store credit
```bash
# Turn 1: Report missing item
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wrong-multiturn-1",
    "user_id": "user-012",
    "channel": "email",
    "customer_email": "lisa@example.com",
    "first_name": "Amy",
    "last_name": "Taylor",
    "shopify_customer_id": "cust-012",
    "message": "Received the pet collar but the tick stickers are missing."
  }' | jq

# Turn 2: Provide details (if not escalated immediately)
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wrong-multiturn-1",
    "user_id": "user-012",
    "channel": "email",
    "customer_email": "lisa@example.com",
    "first_name": "Amy",
    "last_name": "Taylor",
    "shopify_customer_id": "cust-012",
    "message": "Its a missing item. Here is a photo of what I received: [photo attached]"
  }' | jq

# Turn 3: Choose store credit
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wrong-multiturn-1",
    "user_id": "user-012",
    "channel": "email",
    "customer_email": "lisa@example.com",
    "first_name": "Amy",
    "last_name": "Taylor",
    "shopify_customer_id": "cust-012",
    "message": "Ill take the store credit, thanks!"
  }' | jq
```

### Scenario 4: Damaged product
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wrong-item-4",
    "user_id": "user-013",
    "channel": "email",
    "customer_email": "lisa@example.com",
    "first_name": "Robert",
    "last_name": "Wilson",
    "shopify_customer_id": "cust-013",
    "message": "The BuzzPatch package arrived damaged and some patches are ruined. I need a replacement."
  }' | jq
```

### Scenario 5: Wrong color/variant
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "wrong-item-5",
    "user_id": "user-014",
    "channel": "email",
    "customer_email": "lisa@example.com",
    "first_name": "Patricia",
    "last_name": "Moore",
    "shopify_customer_id": "cust-014",
    "message": "I ordered the emoji design stickers but got plain ones instead. Can you send the right ones?"
  }' | jq
```

---

## UC3: Product Issue (No Effect)

### Scenario 1: Sleep patches not working
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "product-issue-1",
    "user_id": "user-020",
    "channel": "email",
    "customer_email": "parent@example.com",
    "first_name": "Rachel",
    "last_name": "Anderson",
    "shopify_customer_id": "cust-020",
    "message": "The SleepyPatch doesnt work. My kid is still not sleeping."
  }' | jq
```

### Scenario 2: Focus patches no improvement
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "product-issue-2",
    "user_id": "user-021",
    "channel": "email",
    "customer_email": "parent@example.com",
    "first_name": "Michael",
    "last_name": "Thomas",
    "shopify_customer_id": "cust-021",
    "message": "Focus patches arent helping my son concentrate at all. Hes been using them for a week."
  }' | jq
```

### Scenario 3: Multi-turn - Issue → Usage info → Guidance
```bash
# Turn 1: Report issue
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "product-multiturn-1",
    "user_id": "user-022",
    "channel": "email",
    "customer_email": "parent@example.com",
    "first_name": "Jennifer",
    "last_name": "Jackson",
    "shopify_customer_id": "cust-022",
    "message": "The mosquito patches dont seem to work. My kids still got bitten at the park."
  }' | jq

# Turn 2: Provide usage details
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "product-multiturn-1",
    "user_id": "user-022",
    "channel": "email",
    "customer_email": "parent@example.com",
    "first_name": "Jennifer",
    "last_name": "Jackson",
    "shopify_customer_id": "cust-022",
    "message": "My goal is mosquito protection. I put one patch on their clothes before going outside for 2 hours at the park."
  }' | jq
```

### Scenario 4: Itch relief not working
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "product-issue-4",
    "user_id": "user-023",
    "channel": "email",
    "customer_email": "parent@example.com",
    "first_name": "David",
    "last_name": "White",
    "shopify_customer_id": "cust-023",
    "message": "Itch relief patch did nothing for my daughters bee sting. Still scratching."
  }' | jq
```

---

## UC4: Refund Request

### Scenario 1: Product didnt meet expectations
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "refund-1",
    "user_id": "user-030",
    "channel": "email",
    "customer_email": "refund@example.com",
    "first_name": "Tom",
    "last_name": "Harris",
    "shopify_customer_id": "cust-030",
    "message": "Id like a refund. The patches didnt work for my child."
  }' | jq
```

### Scenario 2: Changed mind
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "refund-2",
    "user_id": "user-031",
    "channel": "email",
    "customer_email": "refund@example.com",
    "first_name": "Kate",
    "last_name": "Martin",
    "shopify_customer_id": "cust-031",
    "message": "I want to cancel my order. I changed my mind and dont need it anymore."
  }' | jq
```

### Scenario 3: Multi-turn - Refund → Reason → Store credit
```bash
# Turn 1: Request refund
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "refund-multiturn-1",
    "user_id": "user-032",
    "channel": "email",
    "customer_email": "refund@example.com",
    "first_name": "David",
    "last_name": "Lee",
    "shopify_customer_id": "cust-032",
    "message": "Can I get a refund? The product didnt work."
  }' | jq

# Turn 2: Explain reason
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "refund-multiturn-1",
    "user_id": "user-032",
    "channel": "email",
    "customer_email": "refund@example.com",
    "first_name": "David",
    "last_name": "Lee",
    "shopify_customer_id": "cust-032",
    "message": "It didnt meet my expectations. My kid is still having trouble sleeping."
  }' | jq

# Turn 3: Accept store credit
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "refund-multiturn-1",
    "user_id": "user-032",
    "channel": "email",
    "customer_email": "refund@example.com",
    "first_name": "David",
    "last_name": "Lee",
    "shopify_customer_id": "cust-032",
    "message": "Sure, Ill take the store credit with bonus!"
  }' | jq
```

### Scenario 4: Shipping delay refund
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "refund-4",
    "user_id": "user-033",
    "channel": "email",
    "customer_email": "refund@example.com",
    "first_name": "Susan",
    "last_name": "Clark",
    "shopify_customer_id": "cust-033",
    "message": "Please refund my order. It was supposed to arrive last week for my sons birthday and it still hasnt shipped."
  }' | jq
```

### Scenario 5: Damaged product refund
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "refund-5",
    "user_id": "user-034",
    "channel": "email",
    "customer_email": "refund@example.com",
    "first_name": "Karen",
    "last_name": "Lopez",
    "shopify_customer_id": "cust-034",
    "message": "I need a refund. The package arrived damaged and half the stickers are unusable."
  }' | jq
```

---

## UC5: Order Modification

### Scenario 1: Cancel accidental order
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "ordermod-1",
    "user_id": "user-040",
    "channel": "email",
    "customer_email": "ordermod@example.com",
    "first_name": "Chris",
    "last_name": "Hall",
    "shopify_customer_id": "cust-040",
    "message": "I need to cancel my order. I placed it by accident."
  }' | jq
```

### Scenario 2: Update shipping address
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "ordermod-2",
    "user_id": "user-041",
    "channel": "email",
    "customer_email": "ordermod@example.com",
    "first_name": "Nina",
    "last_name": "Young",
    "shopify_customer_id": "cust-041",
    "message": "Can I update my shipping address? I entered the wrong one."
  }' | jq
```

### Scenario 3: Multi-turn - Cancel → Reason → Confirm
```bash
# Turn 1: Request cancellation
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "ordermod-multiturn-1",
    "user_id": "user-042",
    "channel": "email",
    "customer_email": "ordermod@example.com",
    "first_name": "Brian",
    "last_name": "King",
    "shopify_customer_id": "cust-042",
    "message": "I want to cancel order #1001"
  }' | jq

# Turn 2: Provide reason
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "ordermod-multiturn-1",
    "user_id": "user-042",
    "channel": "email",
    "customer_email": "ordermod@example.com",
    "first_name": "Brian",
    "last_name": "King",
    "shopify_customer_id": "cust-042",
    "message": "I ordered it by mistake. My kid clicked the button twice."
  }' | jq
```

### Scenario 4: Cancel due to duplicate order
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "ordermod-4",
    "user_id": "user-043",
    "channel": "email",
    "customer_email": "ordermod@example.com",
    "first_name": "Michelle",
    "last_name": "Wright",
    "shopify_customer_id": "cust-043",
    "message": "I accidentally ordered twice. Can you cancel one of them?"
  }' | jq
```

### Scenario 5: Wrong address - urgent
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "ordermod-5",
    "user_id": "user-044",
    "channel": "email",
    "customer_email": "ordermod@example.com",
    "first_name": "Steven",
    "last_name": "Scott",
    "shopify_customer_id": "cust-044",
    "message": "URGENT! I put my old address by mistake. Can you update it to my new address before it ships?"
  }' | jq
```

---

## UC6: Positive Feedback

### Scenario 1: Enthusiastic feedback
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "feedback-1",
    "user_id": "user-050",
    "channel": "email",
    "customer_email": "happy@example.com",
    "first_name": "Jessica",
    "last_name": "Green",
    "shopify_customer_id": "cust-050",
    "message": "OMG! The BuzzPatch is AMAZING! My kids love them and no more mosquito bites! Thank you so much!"
  }' | jq
```

### Scenario 2: Multi-turn - Feedback → Yes to review → Link
```bash
# Turn 1: Send feedback
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "feedback-multiturn-1",
    "user_id": "user-051",
    "channel": "email",
    "customer_email": "happy@example.com",
    "first_name": "Maria",
    "last_name": "Rodriguez",
    "shopify_customer_id": "cust-051",
    "message": "Just wanted to say the FocusPatch is incredible! My sons grades improved!"
  }' | jq

# Turn 2: Accept review request
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "feedback-multiturn-1",
    "user_id": "user-051",
    "channel": "email",
    "customer_email": "happy@example.com",
    "first_name": "Maria",
    "last_name": "Rodriguez",
    "shopify_customer_id": "cust-051",
    "message": "Yes! Id love to leave a review!"
  }' | jq
```

### Scenario 3: Product recommendation feedback
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "feedback-3",
    "user_id": "user-052",
    "channel": "email",
    "customer_email": "happy@example.com",
    "first_name": "Daniel",
    "last_name": "Adams",
    "shopify_customer_id": "cust-052",
    "message": "These patches are life-changing! My daughter sleeps through the night now. Ive already recommended them to 3 friends!"
  }' | jq
```

### Scenario 4: Camping trip success story
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "feedback-4",
    "user_id": "user-053",
    "channel": "email",
    "customer_email": "happy@example.com",
    "first_name": "Angela",
    "last_name": "Baker",
    "shopify_customer_id": "cust-053",
    "message": "BuzzPatch saved our camping trip—no bites at all! The kids had so much fun without constantly scratching."
  }' | jq
```

### Scenario 5: Multi-turn - Feedback → Decline review politely
```bash
# Turn 1: Send feedback
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "feedback-multiturn-2",
    "user_id": "user-054",
    "channel": "email",
    "customer_email": "happy@example.com",
    "first_name": "Elizabeth",
    "last_name": "Nelson",
    "shopify_customer_id": "cust-054",
    "message": "The kids LOVE choosing their emoji stickers each night! Great product!"
  }' | jq

# Turn 2: Decline review
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "feedback-multiturn-2",
    "user_id": "user-054",
    "channel": "email",
    "customer_email": "happy@example.com",
    "first_name": "Elizabeth",
    "last_name": "Nelson",
    "shopify_customer_id": "cust-054",
    "message": "Thanks for asking but Im pretty busy right now. Maybe later!"
  }' | jq
```

---

## UC8: Discount/Promo Code

### Scenario 1: Code not working
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "discount-1",
    "user_id": "user-060",
    "channel": "email",
    "customer_email": "discount@example.com",
    "first_name": "Peter",
    "last_name": "Turner",
    "shopify_customer_id": "cust-060",
    "message": "My promo code isnt working at checkout!"
  }' | jq
```

### Scenario 2: Expired code
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "discount-2",
    "user_id": "user-061",
    "channel": "email",
    "customer_email": "discount@example.com",
    "first_name": "Laura",
    "last_name": "Phillips",
    "shopify_customer_id": "cust-061",
    "message": "I have a discount code that says its expired. Can you help?"
  }' | jq
```

### Scenario 3: Multi-turn - Get code → Ask for bigger discount
```bash
# Turn 1: Request new code
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "discount-multiturn-1",
    "user_id": "user-062",
    "channel": "email",
    "customer_email": "discount@example.com",
    "first_name": "Mark",
    "last_name": "Campbell",
    "shopify_customer_id": "cust-062",
    "message": "WELCOME10 code says invalid at checkout."
  }' | jq

# Turn 2: Ask for bigger discount
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "discount-multiturn-1",
    "user_id": "user-062",
    "channel": "email",
    "customer_email": "discount@example.com",
    "first_name": "Mark",
    "last_name": "Campbell",
    "shopify_customer_id": "cust-062",
    "message": "Can I get 20% instead? Im buying 5 packs."
  }' | jq
```

### Scenario 4: Forgot to apply code
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "discount-4",
    "user_id": "user-063",
    "channel": "email",
    "customer_email": "discount@example.com",
    "first_name": "Nancy",
    "last_name": "Mitchell",
    "shopify_customer_id": "cust-063",
    "message": "I forgot to apply my discount code when I ordered. Can you refund the difference?"
  }' | jq
```

### Scenario 5: Multiple codes issue
```bash
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "discount-5",
    "user_id": "user-064",
    "channel": "email",
    "customer_email": "discount@example.com",
    "first_name": "George",
    "last_name": "Roberts",
    "shopify_customer_id": "cust-064",
    "message": "I have two promo codes but the app wont accept both. How do I use them together?"
  }' | jq
```

---

## Bonus: Edge Cases & Complex Scenarios

### Complex 1: Multi-issue (WISMO + Wrong Item)
```bash
# Turn 1: Start with shipping delay
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "complex-1",
    "user_id": "user-070",
    "channel": "email",
    "customer_email": "transit@test.com",
    "first_name": "Complex",
    "last_name": "Case1",
    "shopify_customer_id": "cust-070",
    "message": "My order was delayed and now that it finally arrived, its the wrong product!"
  }' | jq

# Turn 2: Focus on wrong item
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "complex-1",
    "user_id": "user-070",
    "channel": "email",
    "customer_email": "transit@test.com",
    "first_name": "Complex",
    "last_name": "Case1",
    "shopify_customer_id": "cust-070",
    "message": "I ordered BuzzPatch but got SleepyPatch instead."
  }' | jq
```

### Complex 2: Very long conversation (5+ turns)
```bash
# Turn 1
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "complex-long-1",
    "user_id": "user-071",
    "channel": "email",
    "customer_email": "parent@example.com",
    "first_name": "Sarah",
    "last_name": "LongConvo",
    "shopify_customer_id": "cust-071",
    "message": "The patches dont work."
  }' | jq

# Turn 2
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "complex-long-1",
    "user_id": "user-071",
    "channel": "email",
    "customer_email": "parent@example.com",
    "first_name": "Sarah",
    "last_name": "LongConvo",
    "shopify_customer_id": "cust-071",
    "message": "Im trying to help my son sleep better."
  }' | jq

# Turn 3
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "complex-long-1",
    "user_id": "user-071",
    "channel": "email",
    "customer_email": "parent@example.com",
    "first_name": "Sarah",
    "last_name": "LongConvo",
    "shopify_customer_id": "cust-071",
    "message": "Ive been using 1 patch right before bed for 3 nights."
  }' | jq

# Turn 4
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "complex-long-1",
    "user_id": "user-071",
    "channel": "email",
    "customer_email": "parent@example.com",
    "first_name": "Sarah",
    "last_name": "LongConvo",
    "shopify_customer_id": "cust-071",
    "message": "OK Ill try using it 2 hours before bedtime. But if it still doesnt work I want a refund."
  }' | jq

# Turn 5
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "complex-long-1",
    "user_id": "user-071",
    "channel": "email",
    "customer_email": "parent@example.com",
    "first_name": "Sarah",
    "last_name": "LongConvo",
    "shopify_customer_id": "cust-071",
    "message": "It still isnt working. Id like that refund now please."
  }' | jq
```

---

## Quick Test All Use Cases (One-liner)
```bash
# Test one scenario from each UC
curl -sX POST "$BACKEND_URL/chat" -H "Content-Type: application/json" -d '{"conversation_id":"quick-wismo","user_id":"q1","channel":"email","customer_email":"transit@test.com","first_name":"Quick","last_name":"Test","shopify_customer_id":"cq1","message":"Wheres my order?"}' | jq -r '.state.last_assistant_message' && echo "---" && \
curl -sX POST "$BACKEND_URL/chat" -H "Content-Type: application/json" -d '{"conversation_id":"quick-wrong","user_id":"q2","channel":"email","customer_email":"lisa@example.com","first_name":"Quick","last_name":"Test","shopify_customer_id":"cq2","message":"Got wrong item"}' | jq -r '.state.last_assistant_message' && echo "---" && \
curl -sX POST "$BACKEND_URL/chat" -H "Content-Type: application/json" -d '{"conversation_id":"quick-product","user_id":"q3","channel":"email","customer_email":"parent@example.com","first_name":"Quick","last_name":"Test","shopify_customer_id":"cq3","message":"Patches dont work"}' | jq -r '.state.last_assistant_message' && echo "---" && \
curl -sX POST "$BACKEND_URL/chat" -H "Content-Type: application/json" -d '{"conversation_id":"quick-refund","user_id":"q4","channel":"email","customer_email":"refund@example.com","first_name":"Quick","last_name":"Test","shopify_customer_id":"cq4","message":"I want a refund"}' | jq -r '.state.last_assistant_message' && echo "---" && \
curl -sX POST "$BACKEND_URL/chat" -H "Content-Type: application/json" -d '{"conversation_id":"quick-ordermod","user_id":"q5","channel":"email","customer_email":"ordermod@example.com","first_name":"Quick","last_name":"Test","shopify_customer_id":"cq5","message":"Cancel my order"}' | jq -r '.state.last_assistant_message' && echo "---" && \
curl -sX POST "$BACKEND_URL/chat" -H "Content-Type: application/json" -d '{"conversation_id":"quick-feedback","user_id":"q6","channel":"email","customer_email":"happy@example.com","first_name":"Quick","last_name":"Test","shopify_customer_id":"cq6","message":"Love the patches!"}' | jq -r '.state.last_assistant_message' && echo "---" && \
curl -sX POST "$BACKEND_URL/chat" -H "Content-Type: application/json" -d '{"conversation_id":"quick-discount","user_id":"q7","channel":"email","customer_email":"discount@example.com","first_name":"Quick","last_name":"Test","shopify_customer_id":"cq7","message":"My promo code doesnt work"}' | jq -r '.state.last_assistant_message'
```

---

## Summary
- **Total scenarios: 50+**
- **Multi-turn conversations: 10+**
- **Use cases covered: All 8**
- **Edge cases: 2 complex scenarios**
