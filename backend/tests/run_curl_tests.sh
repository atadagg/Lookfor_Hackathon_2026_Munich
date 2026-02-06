#!/bin/bash
# Automated CURL testing script for all agents
# Usage: ./run_curl_tests.sh [backend_url]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend URL
BACKEND_URL="${1:-http://localhost:8000}"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  CURL Test Suite - All Agents ${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "${YELLOW}Backend URL: $BACKEND_URL${NC}\n"

# Counter
TOTAL=0
SUCCESS=0
FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local conv_id="$2"
    local email="$3"
    local first_name="$4"
    local message="$5"
    local turn_number="${6:-1}"
    
    TOTAL=$((TOTAL + 1))
    
    echo -e "${BLUE}[$TOTAL] Testing: $test_name (Turn $turn_number)${NC}"
    echo -e "${YELLOW}Message: $message${NC}"
    
    response=$(curl -s -X POST "$BACKEND_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"conversation_id\": \"$conv_id\",
            \"user_id\": \"user-test-$TOTAL\",
            \"channel\": \"email\",
            \"customer_email\": \"$email\",
            \"first_name\": \"$first_name\",
            \"last_name\": \"TestUser\",
            \"shopify_customer_id\": \"cust-test-$TOTAL\",
            \"message\": \"$message\"
        }")
    
    if [ $? -eq 0 ]; then
        agent=$(echo "$response" | jq -r '.agent // "unknown"')
        last_message=$(echo "$response" | jq -r '.state.last_assistant_message // "N/A"' | head -c 100)
        workflow_step=$(echo "$response" | jq -r '.state.workflow_step // "N/A"')
        
        echo -e "${GREEN}✓ Agent: $agent | Step: $workflow_step${NC}"
        echo -e "${GREEN}  Reply: $last_message...${NC}"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
    
    echo ""
    sleep 0.3
}

# Check if server is up
echo -e "${YELLOW}Checking server...${NC}"
if ! curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Backend not responding at $BACKEND_URL${NC}"
    echo "Start backend with: uvicorn api.server:app --host 0.0.0.0 --port 8000"
    exit 1
fi
echo -e "${GREEN}✓ Server is up${NC}\n"

# ===========================
# UC1: WISMO Tests
# ===========================
echo -e "\n${BLUE}═══════════════════════════════${NC}"
echo -e "${BLUE}  UC1: WISMO (Shipping Delay)  ${NC}"
echo -e "${BLUE}═══════════════════════════════${NC}\n"

run_test "WISMO - In Transit" "wismo-1" "transit@test.com" "Sarah" "Where is my order? It has been a week."

run_test "WISMO - Unfulfilled" "wismo-2" "unfulfilled@test.com" "Mike" "I ordered 3 days ago but havent heard anything. When will it ship?"

run_test "WISMO - No Orders (Turn 1)" "wismo-multi-1" "noorders@test.com" "Emma" "My order hasnt arrived yet!" 1
run_test "WISMO - Provide Order ID (Turn 2)" "wismo-multi-1" "noorders@test.com" "Emma" "Its order #43189" 2

run_test "WISMO - Delivered" "wismo-4" "delivered@test.com" "James" "It says delivered but I never received it."

# ===========================
# UC2: Wrong Item Tests
# ===========================
echo -e "\n${BLUE}═══════════════════════════════${NC}"
echo -e "${BLUE}  UC2: Wrong/Missing Item      ${NC}"
echo -e "${BLUE}═══════════════════════════════${NC}\n"

run_test "Wrong Item - Wrong Product" "wrong-1" "lisa@example.com" "Lisa" "Got Zen stickers instead of Focus—kids need them for school!"

run_test "Wrong Item - Missing Items" "wrong-2" "lisa@example.com" "John" "My package arrived with only 2 of the 3 packs I paid for."

run_test "Wrong Item - Missing (Turn 1)" "wrong-multi-1" "lisa@example.com" "Amy" "Received the pet collar but the tick stickers are missing." 1
run_test "Wrong Item - Store Credit (Turn 2)" "wrong-multi-1" "lisa@example.com" "Amy" "Ill take the store credit, thanks!" 2

run_test "Wrong Item - Damaged" "wrong-4" "lisa@example.com" "Robert" "The package arrived damaged and some patches are ruined."

# ===========================
# UC3: Product Issue Tests
# ===========================
echo -e "\n${BLUE}═══════════════════════════════${NC}"
echo -e "${BLUE}  UC3: Product Issue (No Effect)${NC}"
echo -e "${BLUE}═══════════════════════════════${NC}\n"

run_test "Product Issue - Sleep" "product-1" "parent@example.com" "Rachel" "The SleepyPatch doesnt work. My kid is still not sleeping."

run_test "Product Issue - Focus" "product-2" "parent@example.com" "Michael" "Focus patches arent helping my son concentrate at all."

run_test "Product Issue - Report (Turn 1)" "product-multi-1" "parent@example.com" "Jennifer" "The mosquito patches dont seem to work." 1
run_test "Product Issue - Usage Info (Turn 2)" "product-multi-1" "parent@example.com" "Jennifer" "My goal is mosquito protection. I put one patch on their clothes." 2

# ===========================
# UC4: Refund Tests
# ===========================
echo -e "\n${BLUE}═══════════════════════════════${NC}"
echo -e "${BLUE}  UC4: Refund Request          ${NC}"
echo -e "${BLUE}═══════════════════════════════${NC}\n"

run_test "Refund - Expectations" "refund-1" "refund@example.com" "Tom" "Id like a refund. The patches didnt work for my child."

run_test "Refund - Changed Mind" "refund-2" "refund@example.com" "Kate" "I want to cancel my order. I changed my mind."

run_test "Refund - Request (Turn 1)" "refund-multi-1" "refund@example.com" "David" "Can I get a refund? The product didnt work." 1
run_test "Refund - Reason (Turn 2)" "refund-multi-1" "refund@example.com" "David" "It didnt meet my expectations." 2
run_test "Refund - Store Credit (Turn 3)" "refund-multi-1" "refund@example.com" "David" "Sure, Ill take the store credit with bonus!" 3

# ===========================
# UC5: Order Mod Tests
# ===========================
echo -e "\n${BLUE}═══════════════════════════════${NC}"
echo -e "${BLUE}  UC5: Order Modification      ${NC}"
echo -e "${BLUE}═══════════════════════════════${NC}\n"

run_test "Order Mod - Cancel Accidental" "ordermod-1" "ordermod@example.com" "Chris" "I need to cancel my order. I placed it by accident."

run_test "Order Mod - Update Address" "ordermod-2" "ordermod@example.com" "Nina" "Can I update my shipping address? I entered the wrong one."

run_test "Order Mod - Duplicate" "ordermod-4" "ordermod@example.com" "Michelle" "I accidentally ordered twice. Can you cancel one?"

# ===========================
# UC6: Feedback Tests
# ===========================
echo -e "\n${BLUE}═══════════════════════════════${NC}"
echo -e "${BLUE}  UC6: Positive Feedback       ${NC}"
echo -e "${BLUE}═══════════════════════════════${NC}\n"

run_test "Feedback - Enthusiastic" "feedback-1" "happy@example.com" "Jessica" "OMG! The BuzzPatch is AMAZING! No more mosquito bites!"

run_test "Feedback - Initial (Turn 1)" "feedback-multi-1" "happy@example.com" "Maria" "The FocusPatch is incredible! My sons grades improved!" 1
run_test "Feedback - Accept Review (Turn 2)" "feedback-multi-1" "happy@example.com" "Maria" "Yes! Id love to leave a review!" 2

run_test "Feedback - Recommendation" "feedback-3" "happy@example.com" "Daniel" "These patches are life-changing! Ive recommended them to 3 friends!"

# ===========================
# UC8: Discount Tests
# ===========================
echo -e "\n${BLUE}═══════════════════════════════${NC}"
echo -e "${BLUE}  UC8: Discount/Promo Code     ${NC}"
echo -e "${BLUE}═══════════════════════════════${NC}\n"

run_test "Discount - Not Working" "discount-1" "discount@example.com" "Peter" "My promo code isnt working at checkout!"

run_test "Discount - Expired" "discount-2" "discount@example.com" "Laura" "I have a discount code that says its expired. Can you help?"

run_test "Discount - Request (Turn 1)" "discount-multi-1" "discount@example.com" "Mark" "WELCOME10 code says invalid at checkout." 1
run_test "Discount - Bigger Discount (Turn 2)" "discount-multi-1" "discount@example.com" "Mark" "Can I get 20% instead? Im buying 5 packs." 2

# ===========================
# Summary
# ===========================
echo -e "\n${BLUE}═══════════════════════════════${NC}"
echo -e "${BLUE}  Test Summary                 ${NC}"
echo -e "${BLUE}═══════════════════════════════${NC}\n"

echo -e "Total Tests:    $TOTAL"
echo -e "${GREEN}Successful:     $SUCCESS${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed:         $FAILED${NC}"
else
    echo -e "${GREEN}Failed:         $FAILED${NC}"
fi
echo -e "\nSuccess Rate:   $(( SUCCESS * 100 / TOTAL ))%\n"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}\n"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed${NC}\n"
    exit 1
fi
