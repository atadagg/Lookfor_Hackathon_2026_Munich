# 🎯 Hackathon Showcase Feature

A dedicated presentation mode for demonstrating all 8 use cases with pre-built, curated examples organized by category. Perfect for hackathon judging and live demos.

## 🎨 New Layout

### Before
```
┌──────────────────────────────┐
│ Search...    [🎮 Playground] │
└──────────────────────────────┘
```

### After
```
┌────────────────────────────────────────┐
│ [🎯 Hackathon Showcase - 8 Use Cases] │  ← Big gradient button
├────────────────────────────────────────┤
│ 🔍 Search conversations...             │  ← Standalone row
├────────────────────────────────────────┤
│ [🎮 Playground] [⚙️ Behavior]          │  ← Utility buttons
└────────────────────────────────────────┘
```

## ✨ Features

### 📊 Showcase Sidebar

**Access:** Click the big gradient "Hackathon Showcase" button

**Structure:**
```
┌─────────────────────────────────────┐
│  🎯 Hackathon Showcase              │
│  8 Use Cases • Pre-built Examples   │
├─────────────────────────────────────┤
│  [8 Use Cases] [23 Examples] [8 Agents]
├─────────────────────────────────────┤
│                                     │
│  📦 UC1: Shipping Delay (WISMO)     │ ← Expandable
│    ├─ Basic order tracking          │
│    ├─ Delayed shipment              │
│    └─ No tracking info              │
│                                     │
│  ❌ UC2: Wrong/Missing Item         │
│    ├─ Wrong item received           │
│    ├─ Wrong item with photo 📸      │ ← Has image
│    └─ Missing items                 │
│                                     │
│  ... (6 more use cases)             │
│                                     │
├─────────────────────────────────────┤
│  Selected: Wrong item with photo    │
│  [▶ Run Example]                    │
│  Customer Message: "I received..."  │
│  Expected: wrong_item → 2 tools     │
└─────────────────────────────────────┘
```

### 🎯 8 Use Cases Included

1. **UC1: Shipping Delay (WISMO)** 🔵
   - Basic order tracking
   - Delayed shipment with promise
   - No tracking information

2. **UC2: Wrong/Missing Item** 🔴
   - Wrong item received
   - Wrong item with photo proof 📸
   - Missing items in package

3. **UC3: Product Issue (Defect)** 🟡
   - Product not effective
   - Patches falling off

4. **UC4: Refund Request** 🟣
   - Standard refund request
   - Refund as store credit

5. **UC5: Order Modification** 🟠
   - Cancel order
   - Change shipping address

6. **UC6: Positive Feedback** 🟢
   - Happy customer review
   - Customer wants referral

7. **UC7: Subscription Management** 🟣
   - Pause subscription
   - Cancel subscription
   - Skip next order

8. **UC8: Discount Issues** 🩷
   - Discount code not working
   - Expired discount code

**Total: 23 pre-built examples ready for demo!**

## 🎨 Visual Hierarchy

### Main Showcase Button
- **Size**: Full width, h-11 (44px)
- **Style**: Triple gradient (blue → purple → pink)
- **Position**: Top of sidebar (most prominent)
- **Effect**: Shadow elevation on hover

### Search Bar
- **Position**: Standalone row (below showcase)
- **Size**: h-9 (36px)
- **Style**: Clean, focused design

### Utility Buttons
- **Position**: Bottom row (2 columns)
- **Size**: h-8 (32px), smaller than main CTA
- **Style**: Gradient backgrounds (purple & amber)

## 📊 Example Metadata

Each example includes:

```typescript
{
  id: "uc2_with_photo",
  title: "Wrong item with photo proof",
  useCase: "UC2",
  description: "Customer has photo evidence",
  message: "I received the wrong color. See attached photo...",
  hasImage: true,
  imageUrl: "https://storage.aimentora.com/...",
  expectedAgent: "wrong_item",
  expectedTools: ["get_customer_orders", "shopify_create_store_credit"],
  difficulty: "hard"
}
```

### Difficulty Levels
- 🟢 **Easy** - Straightforward, 1-2 tools
- 🟠 **Medium** - Multiple steps, conditional logic
- 🔴 **Hard** - Complex scenarios, edge cases, images

### Color Coding
Each use case has a unique color scheme matching the agent theme.

## 🎬 Demo Flow

### For Hackathon Judging

1. **Open Showcase** - Click big gradient button
2. **Expand UC1** - Show WISMO examples
3. **Select "Delayed shipment"** - Medium difficulty
4. **Click "Run Example"** - Sends to live system
5. **Observe** - Watch agent routing, tool calls, response
6. **Show Trace Tab** - Display timing, metrics, flow
7. **Repeat** for other use cases

### Presentation Script

> "Let me show you how our multi-agent system handles real customer scenarios..."
> 
> *Clicks Showcase button*
> 
> "We've prepared 23 examples across 8 use cases. Each demonstrates a different agent capability."
> 
> *Expands UC2*
> 
> "Here's a challenging one - wrong item with photo proof. Watch how the agent processes this..."
> 
> *Runs example, switches to Trace tab*
> 
> "See? It routed to wrong_item agent, called 2 tools, processed in 245ms, and offered store credit."

## 🔄 Workflow

### Conversation ID Format
```
showcase_{example_id}_{timestamp}
```

Example: `showcase_uc2_with_photo_1707234567890`

### Customer Profile
```json
{
  "conversation_id": "showcase_uc2_with_photo_1707234567890",
  "user_id": "showcase_uc2_with_photo",
  "channel": "email",
  "customer_email": "showcase@example.com",
  "first_name": "Showcase",
  "last_name": "Demo",
  "shopify_customer_id": "showcase_customer",
  "message": "I received the wrong color..."
}
```

## 📈 Benefits

### For Presentation
- ✅ **Organized by use case** - Easy to navigate
- ✅ **Pre-tested examples** - Know what to expect
- ✅ **One-click demo** - No setup needed
- ✅ **Visual feedback** - Difficulty badges, tool counts

### For Testing
- ✅ **Comprehensive coverage** - All 8 agents
- ✅ **Edge cases included** - Hard difficulty scenarios
- ✅ **Real messages** - Authentic customer language
- ✅ **Expected outcomes** - Know what should happen

### For Judging
- ✅ **Professional UI** - Polished, gradient design
- ✅ **Clear organization** - Grouped by category
- ✅ **Quick access** - 2 clicks to run any example
- ✅ **Full observability** - Complete trace visibility

## 🆚 Showcase vs Playground

| Feature | Showcase | Playground |
|---------|----------|------------|
| **Purpose** | Hackathon presentation | Development testing |
| **Data** | 23 curated examples | 66 random tickets |
| **Organization** | Grouped by use case | Random selection |
| **Filtering** | By use case | By intent |
| **Best for** | Demos & judging | Quick testing |
| **Examples** | Pre-built, tested | Real customer data |
| **UI** | Prominent CTA | Utility button |

## 📂 File Structure

```
frontend/
  src/
    app/
      page.tsx                     # Updated layout with 3 buttons
    components/
      showcase-sidebar.tsx         # New showcase UI (340 lines)
      playground-sidebar.tsx       # Random ticket testing
      mas-behavior-sidebar.tsx     # Agent configuration

SHOWCASE_FEATURE.md               # This document
```

## 🎯 Comparison

### Layout Changes

**Header now has 3 sections:**

1. **Title Row** (unchanged)
   ```
   Lookfor Digital Support        [66 threads]
   ```

2. **Showcase Button** (NEW - Primary CTA)
   ```
   [🎯 Hackathon Showcase - 8 Use Cases →]
   ```

3. **Search Bar** (Standalone)
   ```
   [🔍 Search conversations...]
   ```

4. **Utility Buttons** (2 columns)
   ```
   [🎮 Playground] [⚙️ Behavior]
   ```

### Visual Hierarchy

1. 🥇 **Showcase** - Large, triple gradient, h-11
2. 🥈 **Search** - Medium, clean, h-9
3. 🥉 **Utils** - Small, dual buttons, h-8

## 🚀 Usage

### Quick Demo (30 seconds)

```bash
# 1. Start the app
docker-compose up

# 2. Open browser
open http://localhost:3000

# 3. Click "Hackathon Showcase"
# 4. Expand "UC2: Wrong Item"  
# 5. Click "Wrong item with photo"
# 6. Click "Run Example"
# 7. Switch to "Trace" tab
# 8. Show metrics, timing, tool calls

# Done! Perfect for judging.
```

### Full Walkthrough (5 minutes)

1. **UC1 (WISMO)** - Show order tracking
2. **UC2 (Wrong Item)** - Show photo processing
3. **UC3 (Product Issue)** - Show knowledge base
4. **UC4 (Refund)** - Show payment options
5. **UC5 (Order Mod)** - Show address update
6. **UC6 (Feedback)** - Show discount generation
7. **UC7 (Subscription)** - Show pause/cancel
8. **UC8 (Discount)** - Show code creation

## 📊 Statistics

- **Total Examples**: 23 scenarios
- **Use Cases**: 8 categories
- **Agents**: 8 specialists
- **Tools**: 18 available
- **Code**: ~340 lines (frontend only)
- **Build Time**: ~2 seconds
- **Runtime**: Instant (no backend changes needed)

## ✅ Advantages

### Developer Experience
- 🎯 Clear organization
- 📝 Descriptive titles
- 🎨 Visual indicators (icons, badges, colors)
- 🔍 Easy navigation

### Presentation Quality
- ✨ Professional UI
- 🎬 One-click demos
- 📊 Expected outcomes shown
- ⚡ Fast execution

### Testing Coverage
- ✅ Easy scenarios (basic flows)
- ✅ Medium scenarios (conditional logic)
- ✅ Hard scenarios (edge cases, images)

## 🎉 Perfect for Hackathon!

This feature makes your presentation:
- **Professional** - Beautiful, organized UI
- **Comprehensive** - All 8 use cases covered
- **Interactive** - Live demos with one click
- **Observable** - Full trace visibility
- **Impressive** - Triple-gradient design, smooth animations

**Total Development**: ~2 hours  
**Lines of Code**: ~340 frontend + docs  
**Impact**: Massive improvement for demos! 🚀

---

**Ready to impress the judges!** 🏆
