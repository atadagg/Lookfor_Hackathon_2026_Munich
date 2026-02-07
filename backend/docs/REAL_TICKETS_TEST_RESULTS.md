# Real Customer Tickets - Multi-Agent Test Results

**Test Date:** 2026-02-07 11:53:14
**API URL:** https://lookfor-hackathon-backend.onrender.com
**Backend URL:** http://localhost:8000
**Tickets Tested:** 66

## 📊 Summary

- **Total Tickets:** 66
- **Processed Successfully:** 66 ✅
- **Failed:** 0 ❌
- **Tickets with Tool Calls:** 55
- **Real API Calls Made:** 55 🌐
- **Mock Calls:** 11 🏠

## 📋 Use Case Distribution

| Agent | Tickets Handled |
|-------|-----------------|
| `duplicate` | 10 |
| `feedback` | 11 |
| `order_mod` | 4 |
| `product_issue` | 4 |
| `refund` | 11 |
| `subscription` | 2 |
| `wismo` | 22 |
| `wrong_item` | 2 |

## 📝 Detailed Test Results

### Ticket #1

**Subject:** RE: Your order is ready to ship!  
**Customer Message:**
```
Hi,  Could you please confirm that only part of my order has been sent.  I have recieved the mood calming stickers and the tick repellent stickers only.  Many thanks  Parker Wilson Parker Wilson Sent 
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `duplicate`  
**Execution Time:** 16ms  
**API Mode:** MOCK  

---

### Ticket #2

**Subject:** Return  
**Customer Message:**
```
Hello, my order number is  Order #NP6664669  My order was to include 2 packs for adults and i received all packs for kids. Also, the packs were the old version of buzzpatch. The packs barely had a sce
```

**Expected Use Case:** UC4: Refund  
**Actual Agent:** `duplicate`  
**Execution Time:** 1ms  
**API Mode:** MOCK  

---

### Ticket #3

**Subject:** Issue with Order# NP1366949  
**Customer Message:**
```
Ours fall off our clothing pretty easily. If they stayed on, they would do a better job."
```

**Expected Use Case:** UC3: Product Issue  
**Actual Agent:** `duplicate`  
**Execution Time:** 1ms  
**API Mode:** MOCK  

---

### Ticket #4

**Subject:** Re: NATPAT Order #NP1373992 confirmed  
**Customer Message:**
```
My sister,Cassie Ann, would like to consult with you. She saw your ad on FBK and is very interested. She tried to contact you through your form but wasn’t successful. Could you add her as a friend so 
```

**Expected Use Case:** Unknown  
**Actual Agent:** `duplicate`  
**Execution Time:** 1ms  
**API Mode:** MOCK  

---

### Ticket #5

**Subject:** Return  
**Customer Message:**
```
Hello!  I'm reaching out regarding my most recent order, Order# NP7412770.  I have been using NATPAT for several years without any issues, but the MagicPatch Itch Relief Patches I received seem to be 
```

**Expected Use Case:** UC3: Product Issue  
**Actual Agent:** `duplicate`  
**Execution Time:** 6ms  
**API Mode:** MOCK  

---

### Ticket #6

**Subject:** Order update  
**Customer Message:**
```
Where is my order ?  Frédéric +19409061934
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `duplicate`  
**Execution Time:** 4ms  
**API Mode:** MOCK  

---

### Ticket #7

**Subject:** Fwd: NATPAT Order #NP1375783 confirmed  
**Customer Message:**
```
I would like to return some of my order!  I opened one and was not happy with the results.   My order # was NP0192094.  Please advise how to move forward.    Thank you  Jodi Sweezy  Sent from my iPhon
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `duplicate`  
**Execution Time:** 1ms  
**API Mode:** MOCK  

---

### Ticket #8

**Subject:** Re: NATPAT Order #NP1386385 confirmed  
**Customer Message:**
```
Order# ONE+19734780131US  Hello, I was just looking to get a little information on my delivery. We are excited to try your products. We are just hoping it arrives soon for our trip. Was just curious i
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `duplicate`  
**Execution Time:** 6ms  
**API Mode:** MOCK  

---

### Ticket #9

**Subject:** Cancel all future orders NATPAT Order #NP1364562 confirmed  
**Customer Message:**
```
I haven’t used stickers but I have used plug in calming pheromones."
```

**Expected Use Case:** UC5: Order Modification  
**Actual Agent:** `duplicate`  
**Execution Time:** 6ms  
**API Mode:** MOCK  

---

### Ticket #10

**Subject:** Re: NATPAT Order #NP1380121 confirmed  
**Customer Message:**
```
Hello, I am wondering when my order might be shipped. Is there any update you can share?  Many thanks, - Donna ---------- Forwarded message ---------
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `duplicate`  
**Execution Time:** 5ms  
**API Mode:** MOCK  

---

### Ticket #11

**Subject:** (no subject)  
**Customer Message:**
```
Patch Power
```

**Expected Use Case:** UC6: Positive Feedback  
**Actual Agent:** `feedback`  
**Execution Time:** 2627ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`
  - `add_order_tags`

**Agent Response:**
```
Hi Customer! 🥰 Thank you so much for your wonderful feedback about Patch Power! We’re thrilled to hear you’re enjoying it. If you have a moment, we would be super grateful if you could share your experience on Trustpilot: https://trustpilot.com/evaluate/naturalpatch.com. Your support means the world
```

---

### Ticket #12

**Subject:** Cancel  
**Customer Message:**
```
I'm wanting the flea patch only.  Can this patch be attached to the collar, my kelpie chewed two lockets attached to her collar. I cannot afford to keep buying lockets
```

**Expected Use Case:** UC5: Order Modification  
**Actual Agent:** `order_mod`  
**Execution Time:** 960ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with cancellations or address updates for your order. Which would you like to do?
```

---

### Ticket #13

**Subject:** Order number NP1370371  
**Customer Message:**
```
Hello,  I’m not sure why I received another NatPat order but please cancel all future orders.  Please confirm that this has been done.  Thank you.  Rio Slaven  NATPAT Order #NP2361630 confirmed
```

**Expected Use Case:** UC5: Order Modification  
**Actual Agent:** `order_mod`  
**Execution Time:** 641ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
Your order has already been fulfilled, so I can't cancel it. I'm looping in Monica, our Head of CS, who can help with alternatives.
```

---

### Ticket #14

**Subject:** Fwd: NATPAT Order #NP1382560 confirmed  
**Customer Message:**
```
PatchPower Sent from my iPhone
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `refund`  
**Execution Time:** 775ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with that. Could you let me know why you'd like a refund? (Product didn't work as expected, shipping delay, damaged/wrong item, changed your mind, etc.)
```

---

### Ticket #15

**Subject:** Package didn't arrive: Request a refund(Order: 113-3656428-1861054)  
**Customer Message:**
```
I ordered the tick stickers on Amazon and I received the memory ones. I’d like to get this fixed please.  Joe Morgan +12351077824  Sent from my iPhone
```

**Expected Use Case:** UC4: Refund  
**Actual Agent:** `wrong_item`  
**Execution Time:** 1937ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_orders_and_details`

**Agent Response:**
```
Thanks for letting me know. I'm looping in Monica, our Head of CS, who will take it from here and process a free resend for you.
```

---

### Ticket #16

**Subject:** NATPAT Order #NP1380209  
**Customer Message:**
```
Where's my order, keeps saying bits in Coppell texas I order was suppose to be here the 16th,,," 
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 1827ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer, your order #1001 is on the way and currently in transit. Please hang tight until early next week, and if it doesn't arrive by then, I’ll be here to help! You can track it here: https://tracking.example.com/demo123.
```

---

### Ticket #17

**Subject:** Re: NATPAT Order #NP1384368 confirmed  
**Customer Message:**
```
I've always had trouble falling asleep. When I was little I would have my mom sit in my room with me until I fell asleep so I wasn't alone. If she tried to leave early I would whine that I ""wasn't as
```

**Expected Use Case:** Unknown  
**Actual Agent:** `refund`  
**Execution Time:** 666ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with that. Could you let me know why you'd like a refund? (Product didn't work as expected, shipping delay, damaged/wrong item, changed your mind, etc.)
```

---

### Ticket #18

**Subject:** Re: Your order has been delivered!  
**Customer Message:**
```
I need to cancel my subscription.  Name is Janette MacAusland address is [REDACTED_ADDRESS]
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `subscription`  
**Execution Time:** 3299ms  
**API Mode:** REAL API  
**Tools Called:**
  - `skio_get_subscriptions`

**Agent Response:**
```
Hi Janette! I see that you have an active subscription. May I ask what the reason is for wanting to cancel? I'm here to help!
```

---

### Ticket #19

**Subject:** Re: NATPAT Order #NP1386467 confirmed  
**Customer Message:**
```
I was notified this order was delivered July 8, 2025, but I did not receive it.  Thank you in advance for your help.  Christine Lanum, cell number +14743070825
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 1600ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Christine, 

Your order #1001 is currently on the way and is expected to arrive early next week. Please hang tight until then, and if it doesn't show up by that time, I'll be here to help you sort it out! 

Best,  
Caz
```

---

### Ticket #20

**Subject:** (no subject)  
**Customer Message:**
```
Is there an ETA on this order please?  Thank you!  Begin forwarded message:" 
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 1847ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer! Your order #1001 is on the way, and I ask that you please wait until early next week for it to arrive. If it doesn't show up by then, just let me know and I'll help you out! You can track it here: [tracking link](https://tracking.example.com/demo123).
```

---

### Ticket #21

**Subject:** Status of Order #NP1381916  
**Customer Message:**
```
MessengerAttachments/fd0b28a7-9058-4c4f-8a3e-4b2d5b5dcce7/3c6df717-7225-4122-a1cc-1f760dfb4b52.mp4" 
```

**Expected Use Case:** UC6: Positive Feedback  
**Actual Agent:** `refund`  
**Execution Time:** 787ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with that. Could you let me know why you'd like a refund? (Product didn't work as expected, shipping delay, damaged/wrong item, changed your mind, etc.)
```

---

### Ticket #22

**Subject:** Re: Quick one (sorry again!)  
**Customer Message:**
```
  You have received a message.  Order ID: +131582883944:  #   ASIN         Product Name 1   B09745CSRV   NATPAT Buzz Patch Mosquito Patch Stickers for Kids - Plant                  Based Ingredients, 
```

**Expected Use Case:** UC5: Order Modification  
**Actual Agent:** `order_mod`  
**Execution Time:** 676ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
Your order has already been fulfilled, so I can't cancel it. I'm looping in Monica, our Head of CS, who can help with alternatives.
```

---

### Ticket #23

**Subject:** Re: NATPAT Order #NP1386474 confirmed  
**Customer Message:**
```
Hello,  I received my NATPAT order and one of the bags is expired. The other two bags received have a different lot no.   Lot no.: TRBP60007 Expiry Date: 2025-05  Can you please send a replacement?  T
```

**Expected Use Case:** UC2: Wrong Item  
**Actual Agent:** `product_issue`  
**Execution Time:** 1687ms  
**API Mode:** REAL API  
**Tools Called:**
  - `shopify_get_customer_orders`
  - `shopify_get_order_details`

**Agent Response:**
```
Hi Dana,

I’m really sorry to hear about the issue with your NATPAT order #1001; that must be frustrating. To better assist you, could you share what specific goal you’re hoping to achieve with the patches? Are you looking for help with falling asleep, staying asleep, or perhaps something else?

Tha
```

---

### Ticket #24

**Subject:** New customer message on July 19, 2025 at 12:28 pm  
**Customer Message:**
```
patch power Sent from my iPad
```

**Expected Use Case:** UC6: Positive Feedback  
**Actual Agent:** `product_issue`  
**Execution Time:** 2167ms  
**API Mode:** REAL API  
**Tools Called:**
  - `shopify_get_customer_orders`
  - `shopify_get_order_details`

**Agent Response:**
```
Hi Customer,

I’m really sorry to hear that the patches from your order #1001 aren’t working as you hoped. Can you share what specific goal you’re trying to achieve with them, like falling asleep, staying asleep, or perhaps stress relief? Understanding your usage—like how many patches you’re using a
```

---

### Ticket #25

**Subject:** (no subject)  
**Customer Message:**
```
That a TRUE....PHUCK AROUND & FIND OUT situation
```

**Expected Use Case:** Unknown  
**Actual Agent:** `refund`  
**Execution Time:** 1037ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with that. Could you let me know why you'd like a refund? (Product didn't work as expected, shipping delay, damaged/wrong item, changed your mind, etc.)
```

---

### Ticket #26

**Subject:** Re: Quick one (sorry again!)  
**Customer Message:**
```
Thank you for resending the order.  I received my package last night.  I can't to try these on my granddaughter.  The mosquitoes eat her up and he is allergic to them.  She gets huge marks on her wher
```

**Expected Use Case:** UC6: Positive Feedback  
**Actual Agent:** `feedback`  
**Execution Time:** 1945ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`
  - `add_order_tags`

**Agent Response:**
```
Hi Christy! 🥰 I'm so glad to hear that your package arrived safely! I hope your granddaughter loves the patches and finds relief from those pesky mosquitoes! 🌼 If you have a moment, we would be super grateful if you could share your experience on Trustpilot: https://trustpilot.com/evaluate/naturalpa
```

---

### Ticket #27

**Subject:** Return request  
**Customer Message:**
```
Patch Power
```

**Expected Use Case:** UC4: Refund  
**Actual Agent:** `feedback`  
**Execution Time:** 1761ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`
  - `add_order_tags`

**Agent Response:**
```
Hi Customer! 🥰 Thank you so much for your wonderful feedback! We’re thrilled to hear you’re loving Patch Power! If you have a moment, we’d be super grateful if you could share your experience on Trustpilot: https://trustpilot.com/evaluate/naturalpatch.com. Your support means the world to us! ❤️🙏 xx
```

---

### Ticket #28

**Subject:** Status of order NP1354045  
**Customer Message:**
```
Please stop swearing it’s so unprofessional and unnecessary.
```

**Expected Use Case:** Unknown  
**Actual Agent:** `refund`  
**Execution Time:** 747ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with that. Could you let me know why you'd like a refund? (Product didn't work as expected, shipping delay, damaged/wrong item, changed your mind, etc.)
```

---

### Ticket #29

**Subject:** Order not shipped  
**Customer Message:**
```
Where is my order?  Order #NP3352659
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 1834ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer, your order #1001 is on the way! Please hang tight until early next week, and if it doesn’t arrive by then, I’ll be here to help you out. You can track it here: [tracking link](https://tracking.example.com/demo123).
```

---

### Ticket #30

**Subject:** RE: NATPAT Order #NP1386497 confirmed  
**Customer Message:**
```
I was trying to get some sun on my legs at work when one of my kids joined and informed me that “Mommy likes to lay out in the yard nekked while daddy mows the grass!” 🙈
```

**Expected Use Case:** Unknown  
**Actual Agent:** `feedback`  
**Execution Time:** 1582ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`
  - `add_order_tags`

**Agent Response:**
```
Hi Customer! 😂 That sounds like such a funny moment with your kids! Thank you for sharing that with me! If you have a moment, I’d love it if you could share your experience with us on Trustpilot. Your feedback means the world to us! ❤️🙏
```

---

### Ticket #31

**Subject:** Missing Order  
**Customer Message:**
```
Hello,  I had placed an order on July 11th. I have not yet received any updates on the shipping status of my order.  Can you please help me with this?  Order #NP8527336  Thanks,  Neel Iyer
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 2221ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Neel, 

Your order #NP8527336 is on the way! Please hang tight until early next week, and if it hasn't arrived by then, I'll be here to help you sort it out. You can track it here: https://tracking.example.com/demo123. 

Thanks!
```

---

### Ticket #32

**Subject:** NP1382086  
**Customer Message:**
```
I found them at target where I live
```

**Expected Use Case:** Unknown  
**Actual Agent:** `feedback`  
**Execution Time:** 1748ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`
  - `add_order_tags`

**Agent Response:**
```
Hi Customer! 😊 I'm so glad to hear you found us at Target! 🥰 If you have a moment, we would be super grateful if you could share your experience on Trustpilot. Your feedback means the world to us! ❤️ Thank you! xx
```

---

### Ticket #33

**Subject:** (no subject)  
**Customer Message:**
```
I have not yet received them.  Jenna Smith  user_b3015ce891@example.com
```

**Expected Use Case:** Unknown  
**Actual Agent:** `wismo`  
**Execution Time:** 1752ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer, your order #1001 is on the way! Please hang tight until early next week, and if it doesn't arrive by then, I’ll be here to help you out. You can track it here: [tracking link](https://tracking.example.com/demo123).
```

---

### Ticket #34

**Subject:** Order  
**Customer Message:**
```
Patch power !  Lauralee Beaurieux
```

**Expected Use Case:** UC6: Positive Feedback  
**Actual Agent:** `feedback`  
**Execution Time:** 1965ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`
  - `add_order_tags`

**Agent Response:**
```
Hi Customer! 🥰 Thank you so much for your amazing feedback! We're thrilled to hear you're loving the patch power! If you have a moment, we'd be super grateful if you could share your experience on Trustpilot. It really helps us out! ❤️🙏 [Trustpilot Link]
```

---

### Ticket #35

**Subject:** Order not even showing as sent - I ordered on 9th July ORDER NO: NP1380411  
**Customer Message:**
```
You received a new message from your online store's contact    form.     Country Code:     US     Name:     Andrea Wesolowski     Email:     user_68baec07fe@example.com     Phone Number:     +16027919
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 1845ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Andrea, 

Your order #1001 is currently on the way, and I ask that you please wait until early next week for it to arrive. If it doesn’t show up by then, just let me know, and I’ll be happy to help! 

Best,  
Caz
```

---

### Ticket #36

**Subject:** Payment  
**Customer Message:**
```
Hello,  I placed this order on July 2, 2025 and have not received it!  What's the problem?  It should have been here  8 days ago.  Sincerity, Deanna
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 2309ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Deanna, I totally understand your concern! Your order #1001 is currently on the way, and I ask that you please wait until early next week for it to arrive. If it doesn't show up by then, I’ll be here to help you sort it out! You can track it here: https://tracking.example.com/demo123.
```

---

### Ticket #37

**Subject:** Re: NATPAT Order #NP1373568 confirmed  
**Customer Message:**
```
Hi Agent,  My package hasn't still arrived so there is nothing to review yet.  Regards, Neha
```

**Expected Use Case:** Unknown  
**Actual Agent:** `wismo`  
**Execution Time:** 1887ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Neha, I see your order #1001 is on the way! Please hang tight until early next week, and if it doesn’t arrive by then, I’ll be here to help you sort it out. You can track it here: [tracking link](https://tracking.example.com/demo123).
```

---

### Ticket #38

**Subject:** Order #NP1384099  
**Customer Message:**
```
Hi there,  I just purchased the bite relief patches by mistake, meaning to get the mosquito repellent, would I be able to return them please? My order number is #NP9938917     Emily Chamberlain
```

**Expected Use Case:** UC4: Refund  
**Actual Agent:** `order_mod`  
**Execution Time:** 705ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with cancellations or address updates for your order. Which would you like to do?
```

---

### Ticket #39

**Subject:** 2 Orders 1 Package #NP1374421  
**Customer Message:**
```
I just can't wait to see a mosquito drunk. If its not after snacking on me.  😆"
```

**Expected Use Case:** Unknown  
**Actual Agent:** `feedback`  
**Execution Time:** 1694ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`
  - `add_order_tags`

**Agent Response:**
```
Hi Customer! 😄 I'm so glad to hear from you! I totally understand your decision, and I appreciate your feedback! Wishing you a mosquito-free day filled with laughter! 🦟❤️✨
```

---

### Ticket #40

**Subject:** Re: Your order is ready to ship!  
**Customer Message:**
```
I have placed the subject order on June 9 and still haven’t received it to date. Can you please update me on the status of the order?   Thanks, Razan   Sent from my iPhone
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 1534ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Razan,  
Your order #1001 is currently on the way! Please hang tight until early next week, and if it doesn’t arrive by then, I’ll be here to help you out. You can track it here: [Tracking Link](https://tracking.example.com/demo123).
```

---

### Ticket #41

**Subject:** Re: NATPAT Order #NP1386525 confirmed  
**Customer Message:**
```
Hi we are really disappointed to have not received our order… this is an urgent issue as we have Clint’s In need for these items please can you inform us of why we haven’t received the order and at th
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 1955ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer, I totally understand your frustration! Your order #1001 is currently on the way, and I kindly ask you to wait until early next week for it to arrive. If it doesn’t show up by then, I’ll be here to help you sort it out! You can track it here: [tracking link](https://tracking.example.com
```

---

### Ticket #42

**Subject:** (no subject)  
**Customer Message:**
```
I placed my order #NP4510618 on July 12,2025. My credit card has been charged but my order has not shipped yet. Please check on why my order has not shipped yet and advise.  Thank you.  Pam Griffith  
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 1767ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Pam, thanks for reaching out! Your order #1001 is currently on the way, and you can track it here: https://tracking.example.com/demo123. Please hang tight until early next week, and if it hasn’t arrived by then, I’ll be here to help!
```

---

### Ticket #43

**Subject:** rsJyOiHszjy2Tt7TxbIMka2Ro  
**Customer Message:**
```
MessengerAttachments/ccc84273-a2af-483c-baf6-e02c8fd591c5/966ed92c-1aac-4781-a071-14a474f1d48b.jpg
```

**Expected Use Case:** Unknown  
**Actual Agent:** `refund`  
**Execution Time:** 886ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with that. Could you let me know why you'd like a refund? (Product didn't work as expected, shipping delay, damaged/wrong item, changed your mind, etc.)
```

---

### Ticket #44

**Subject:** Haven't received order  
**Customer Message:**
```
THANKS FOR NO INSTRUCTIONS ON THE PET ZEN!
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `product_issue`  
**Execution Time:** 1874ms  
**API Mode:** REAL API  
**Tools Called:**
  - `shopify_get_customer_orders`
  - `shopify_get_order_details`

**Agent Response:**
```
Hi Customer,

I’m sorry to hear you’re feeling frustrated with your order #1001 and the lack of instructions for the Pet Zen patches. I’d love to understand your goal better—what are you hoping to achieve with the patches? Are you looking for help with falling asleep, staying asleep, or perhaps some
```

---

### Ticket #45

**Subject:** Order?  
**Customer Message:**
```
Wondering if you could help…I ordered 6/24 and still haven’t received my shipment. Can you tell me when to expect a delivery?
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 2016ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer, your order #1001 is currently in transit and should arrive by early next week. You can track it here: [tracking link](https://tracking.example.com/demo123). If it doesn’t show up by then, just let me know and I’ll help you out!
```

---

### Ticket #46

**Subject:** New customer message on July 19, 2025 at 5:14 pm  
**Customer Message:**
```
Hi, I placeDrew Davis an orDrew Daviser on July 3rDrew Davis anDrew Davis it was scheDrew DavisuleDrew Davis to be Drew DaviselivereDrew Davis by July 11 but I haven’t gotten anything yet. My confirma
```

**Expected Use Case:** UC4: Refund  
**Actual Agent:** `wismo`  
**Execution Time:** 1781ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Emily, thanks for reaching out! Your order #1001 is currently on the way, and I ask that you please wait until early next week for it to arrive. If it doesn’t show up by then, I’ll be here to help you out!
```

---

### Ticket #47

**Subject:** Re: Need NATPAT Today? Now Available at Your Local Target  
**Customer Message:**
```
I received an email my order was ready to ship last Tuesday.  An email said it should arrive by the 19th. I keep checking the tracking number and it says USPS is still waiting for the package.   I kno
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 1649ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer, your order #1001 is on the way and is currently in transit. Please hang tight until early next week, and if it doesn’t arrive by then, I’ll be here to help you sort it out. You can track it here: [tracking link](https://tracking.example.com/demo123).
```

---

### Ticket #48

**Subject:** Order #NP1378363  
**Customer Message:**
```
Please can you confirm the locket has been dispatched?" 
```

**Expected Use Case:** Unknown  
**Actual Agent:** `wismo`  
**Execution Time:** 1880ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer,  
Your order #1001 is on its way! Please hang tight until early next week, and if it doesn't arrive by then, I'll be here to help you out. You can track it [here](https://tracking.example.com/demo123).
```

---

### Ticket #49

**Subject:** Re: NATPAT Order #NP1386426 confirmed  
**Customer Message:**
```
Plus, Shop 40% Off Winter Favourites.  Email not displaying correctly?  View it as a web page                             &#xA0;&#xA0;&#xA0;   NEW IN     WOMEN     CURVE     MEN     BRANDS     SALE   
```

**Expected Use Case:** UC4: Refund  
**Actual Agent:** `refund`  
**Execution Time:** 737ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with that. Could you let me know why you'd like a refund? (Product didn't work as expected, shipping delay, damaged/wrong item, changed your mind, etc.)
```

---

### Ticket #50

**Subject:** Re: NATPAT Order #NP1367371 confirmed  
**Customer Message:**
```
I use these!!!
```

**Expected Use Case:** UC6: Positive Feedback  
**Actual Agent:** `feedback`  
**Execution Time:** 1681ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`
  - `add_order_tags`

**Agent Response:**
```
Hi Customer! 🥰 We're so thrilled to hear that you're using our patches! If you have a moment, we’d love it if you could share your experience on Trustpilot. Your feedback means the world to us! ❤️🙏
```

---

### Ticket #51

**Subject:** Re: Your order has been delivered!  
**Customer Message:**
```
The angry reacts must be from other people who haven’t received their orders or responses from you on said orders..?
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 1699ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer, I totally understand your frustration! Your order #1001 is on the way, so please hang tight until early next week. If it doesn't arrive by then, I’ll be here to help you sort it out! You can track it here: [https://tracking.example.com/demo123](https://tracking.example.com/demo123).
```

---

### Ticket #52

**Subject:** Re: NATPAT Order #NP1386572 confirmed  
**Customer Message:**
```
Hi. I didn't receive my order. Shirley
```

**Expected Use Case:** UC2: Wrong Item  
**Actual Agent:** `wismo`  
**Execution Time:** 2065ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer,  
Your order #1001 is on the way! Please hang tight until early next week, and if it hasn't arrived by then, I'll be here to help you sort it out. You can track it here: [tracking link](https://tracking.example.com/demo123).
```

---

### Ticket #53

**Subject:** Re: NATPAT Order #NP1386574 confirmed  
**Customer Message:**
```
Please can you advise me when I’m likely to receive this order? No further details for tracking available on the Shop app. We are away from the 24th July and I placed the order on the 9th July.   Lisa
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 1531ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Lisa,  
Your order #1001 is currently in transit and should arrive by early next week. You can track it here: [tracking link](https://tracking.example.com/demo123). If it doesn't arrive by then, just let me know and I'll help you out!
```

---

### Ticket #54

**Subject:** Order# NP1377958  
**Customer Message:**
```
Dear NATPAT,  Joseph Kreizinger wants to connect with you for the order below:   Customer Order Number:  +15023156350  Purchase Order No:  +13261856066  Reason for Contact:  Where is my order  Item na
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 1854ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer, your order #1001 is on the way! Please hang tight until early next week, and if it doesn't arrive by then, I'll be here to help you out. You can track it [here](https://tracking.example.com/demo123).
```

---

### Ticket #55

**Subject:** Re: NATPAT Order #NP1386553 confirmed  
**Customer Message:**
```
MessengerAttachments/cc4df462-b3e4-41b7-aec8-6110abee155b/1f933bfb-f749-441d-9e4b-98be0e7ee3e6.mp4" 
```

**Expected Use Case:** Unknown  
**Actual Agent:** `refund`  
**Execution Time:** 763ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with that. Could you let me know why you'd like a refund? (Product didn't work as expected, shipping delay, damaged/wrong item, changed your mind, etc.)
```

---

### Ticket #56

**Subject:** Fwd: NATPAT Order #NP1381451 confirmed  
**Customer Message:**
```
So awesome, but when seen on babies, I worry that they may peel them off and put them in their mouth so that they become a choking hazard.  I would think it’s safest to put the stickers on their backs
```

**Expected Use Case:** UC6: Positive Feedback  
**Actual Agent:** `feedback`  
**Execution Time:** 1745ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`
  - `add_order_tags`

**Agent Response:**
```
Hi Customer! 🥰 Thank you so much for your wonderful feedback! Your concern is totally valid, and we appreciate you sharing your thoughts on safety. If you have a moment, we’d be so grateful if you could share your experience on Trustpilot: https://trustpilot.com/evaluate/naturalpatch.com. It really 
```

---

### Ticket #57

**Subject:** Re: NATPAT Order #NP1386223 confirmed  
**Customer Message:**
```
I’ve just tried to order from New Zealand  But the system will not accept my Apple Pay card  Says it needs a province We have no provinces!  Please advise   Sonia Cushing  Sent from my iPhone" 
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `subscription`  
**Execution Time:** 2017ms  
**API Mode:** MOCK  
**Agent Response:**
```
Hi Sonia, I understand you're having trouble with your Apple Pay card due to the province requirement. I'm escalating this issue to our Head of Customer Support, Monica, who will assist you further. Thank you for your patience!
```

---

### Ticket #58

**Subject:** refund?  
**Customer Message:**
```
My order never arrived !! Sent from my iPhone" 
```

**Expected Use Case:** UC4: Refund  
**Actual Agent:** `wismo`  
**Execution Time:** 2108ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer, I see your order #1001 is on the way! Please hang tight until early next week, and if it doesn't arrive by then, I’ll be here to help sort it out. You can track it here: https://tracking.example.com/demo123.
```

---

### Ticket #59

**Subject:** Original order  
**Customer Message:**
```
  The below products have expired and are in the Quarantine store.   Client: NATPAT   Product Code  Expiry Date  Batch Ref  Quantity  Bin  ABP001  2025-06-30  TRABP40002  54  ND27  STP001  2025-05-23 
```

**Expected Use Case:** UC2: Wrong Item  
**Actual Agent:** `refund`  
**Execution Time:** 753ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with that. Could you let me know why you'd like a refund? (Product didn't work as expected, shipping delay, damaged/wrong item, changed your mind, etc.)
```

---

### Ticket #60

**Subject:** Order status  
**Customer Message:**
```
Hi I made an order on the 14th of this month. Order number is NP8073419, and I’m yet to receive a confirmation email or message regarding this order. Kindly let me know when to get the confirmation an
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wismo`  
**Execution Time:** 2171ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_order_status`

**Agent Response:**
```
Hey Customer, your order #1001 is on the way! Please hang tight until early next week, and if it doesn't arrive by then, I'll be here to help you sort it out. You can track it here: https://tracking.example.com/demo123.
```

---

### Ticket #61

**Subject:** Plz cancel my subscription  
**Customer Message:**
```
Hello,  While I've received the order of buzz patches I have not received the Sleepy patches yet.  The tracking shows delivered and checked with the neighbors but nothing came up.
```

**Expected Use Case:** UC1: WISMO  
**Actual Agent:** `wrong_item`  
**Execution Time:** 1624ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_orders_and_details`

**Agent Response:**
```
Thanks for letting me know. I'm looping in Monica, our Head of CS, who will take it from here and process a free resend for you.
```

---

### Ticket #62

**Subject:** New customer message on July 19, 2025 at 8:48 pm  
**Customer Message:**
```
Agent's message: "Get your kid's ""bug armor"" for bite-free adventures! Find us at Target (US), Woolies/CWH (AU), or tap the link in bio! 🌟"
```

**Expected Use Case:** Unknown  
**Actual Agent:** `feedback`  
**Execution Time:** 1730ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`
  - `add_order_tags`

**Agent Response:**
```
Hi Customer! 🥰 Thank you so much for your positive feedback! We’re thrilled to hear you’re excited about our "bug armor"! If you could take a moment to share your thoughts on Trustpilot, we would be incredibly grateful! 🙏❤️ Here’s the link: https://trustpilot.com/evaluate/naturalpatch.com. Thank you
```

---

### Ticket #63

**Subject:** Re: NATPAT Order #NP1386638 confirmed  
**Customer Message:**
```
Does not work"
```

**Expected Use Case:** Unknown  
**Actual Agent:** `product_issue`  
**Execution Time:** 2057ms  
**API Mode:** REAL API  
**Tools Called:**
  - `shopify_get_customer_orders`
  - `shopify_get_order_details`

**Agent Response:**
```
Hi Customer,

I’m sorry to hear that the patches from your order #1001 aren’t working as you hoped. Can you share what specific goal you’re trying to achieve with them? For example, are you looking for help with falling asleep, staying asleep, or something else? Understanding your usage will also he
```

---

### Ticket #64

**Subject:** Order number Np1376061  
**Customer Message:**
```
I don't need any stickers for children, only needed for adults.  Please advise.  😊" 
```

**Expected Use Case:** UC4: Refund  
**Actual Agent:** `refund`  
**Execution Time:** 729ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with that. Could you let me know why you'd like a refund? (Product didn't work as expected, shipping delay, damaged/wrong item, changed your mind, etc.)
```

---

### Ticket #65

**Subject:** Shipping  
**Customer Message:**
```
Markle Jen my son is a magnet for bugs. So he get 3 stickers on his little body , they work great
```

**Expected Use Case:** UC6: Positive Feedback  
**Actual Agent:** `feedback`  
**Execution Time:** 1644ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`
  - `add_order_tags`

**Agent Response:**
```
Hi Customer! 🥰 I'm so thrilled to hear that our stickers are working great for your son! 🌟 If you have a moment, we would be so grateful if you could share your experience on Trustpilot. Your feedback means the world to us! ❤️🙏
```

---

### Ticket #66

**Subject:** Order  
**Customer Message:**
```
Patch Power  Sent from Yahoo Mail for iPhone
```

**Expected Use Case:** UC6: Positive Feedback  
**Actual Agent:** `refund`  
**Execution Time:** 832ms  
**API Mode:** REAL API  
**Tools Called:**
  - `get_customer_latest_order`

**Agent Response:**
```
I can help with that. Could you let me know why you'd like a refund? (Product didn't work as expected, shipping delay, damaged/wrong item, changed your mind, etc.)
```

---

## 📊 Statistics

- **Average Response Time:** 1358ms
- **Success Rate:** 100%
- **Tool Usage Rate:** 83%

## 💡 Insights

✅ **55 tickets triggered real API calls** - Integration working!

### Use Case Coverage

- **duplicate**: 10 ticket(s)
- **feedback**: 11 ticket(s)
- **order_mod**: 4 ticket(s)
- **product_issue**: 4 ticket(s)
- **refund**: 11 ticket(s)
- **subscription**: 2 ticket(s)
- **wismo**: 22 ticket(s)
- **wrong_item**: 2 ticket(s)
