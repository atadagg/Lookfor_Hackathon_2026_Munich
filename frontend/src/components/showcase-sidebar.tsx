"use client";

import { useState } from "react";
import { X, Presentation, Play, Image, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { sendMessage } from "@/lib/api";

interface ExampleScenario {
  id: string;
  title: string;
  useCase: string;
  description: string;
  message: string;
  hasImage?: boolean;
  imageUrl?: string;
  expectedAgent: string;
  expectedTools: string[];
  difficulty: "easy" | "medium" | "hard";
}

interface UseCaseGroup {
  id: string;
  name: string;
  icon: string;
  color: string;
  examples: ExampleScenario[];
}

const USE_CASE_EXAMPLES: UseCaseGroup[] = [
  {
    id: "uc1",
    name: "UC1: Shipping Delay (WISMO)",
    icon: "📦",
    color: "blue",
    examples: [
      {
        id: "uc1_basic",
        title: "Basic order tracking",
        useCase: "UC1",
        description: "Customer asking where their order is",
        message: "Hi, I ordered 2 weeks ago but haven't received anything yet. My email is customer@example.com. Can you check the status?",
        expectedAgent: "wismo",
        expectedTools: ["get_order_status", "get_customer_orders"],
        difficulty: "easy",
      },
      {
        id: "uc1_delayed",
        title: "Delayed shipment with promise",
        useCase: "UC1",
        description: "Order delayed, needs wait promise",
        message: "My order #12345 says it was shipped 10 days ago but still not here. What's going on?",
        expectedAgent: "wismo",
        expectedTools: ["get_order_by_id", "get_order_details"],
        difficulty: "medium",
      },
      {
        id: "uc1_no_tracking",
        title: "No tracking information",
        useCase: "UC1",
        description: "Order with no tracking, should escalate",
        message: "I can't find any tracking info for my order. Order number NP9876. Can you help?",
        expectedAgent: "wismo",
        expectedTools: ["get_order_by_id"],
        difficulty: "hard",
      },
    ],
  },
  {
    id: "uc2",
    name: "UC2: Wrong/Missing Item",
    icon: "❌",
    color: "red",
    examples: [
      {
        id: "uc2_wrong_item",
        title: "Wrong item received",
        useCase: "UC2",
        description: "Customer got wrong product",
        message: "I ordered the adult patches but received kids patches instead. Order #NP6664669. I need this fixed!",
        expectedAgent: "wrong_item",
        expectedTools: ["get_customer_orders", "get_order_details"],
        difficulty: "medium",
      },
      {
        id: "uc2_with_photo",
        title: "Wrong item with photo proof",
        useCase: "UC2",
        description: "Customer has photo evidence",
        message: "I received the wrong color. See attached photo. Order #12345",
        hasImage: true,
        imageUrl: "https://storage.aimentora.com/api/v1/download-shared-object/aHR0cDovLzEyNy4wLjAuMTo5MDAwL2dhbmdidWNrZXQvXzJkYzM5ZDQ5LTAwMDYtNDliZi05OThjLTMyNTA2Mzk4NGIwOS5qcGVnP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9Wk41RzRYNVVYSVdKWVMwREExUDklMkYyMDI2MDIwNiUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNjAyMDZUMjIyNDUyWiZYLUFtei1FeHBpcmVzPTQzMTk5",
        expectedAgent: "wrong_item",
        expectedTools: ["get_customer_orders", "shopify_create_store_credit"],
        difficulty: "hard",
      },
      {
        id: "uc2_missing_items",
        title: "Missing items in package",
        useCase: "UC2",
        description: "Partial order received",
        message: "My package arrived but it's missing 2 items. I only got the stickers but not the patches. Order NP9363178",
        expectedAgent: "wrong_item",
        expectedTools: ["get_order_details"],
        difficulty: "medium",
      },
    ],
  },
  {
    id: "uc3",
    name: "UC3: Product Issue (Defect)",
    icon: "🔧",
    color: "yellow",
    examples: [
      {
        id: "uc3_not_working",
        title: "Product not effective",
        useCase: "UC3",
        description: "Customer says product doesn't work",
        message: "The mosquito patches don't work at all. I've been bitten multiple times while wearing them. Very disappointed.",
        expectedAgent: "product_issue",
        expectedTools: ["get_product_details", "get_related_knowledge_source"],
        difficulty: "medium",
      },
      {
        id: "uc3_falling_off",
        title: "Patches falling off",
        useCase: "UC3",
        description: "Adhesive issue",
        message: "The patches keep falling off my clothes. They barely stay on for an hour. Order #NP1366949",
        expectedAgent: "product_issue",
        expectedTools: ["get_order_details", "get_product_details"],
        difficulty: "easy",
      },
    ],
  },
  {
    id: "uc4",
    name: "UC4: Refund Request",
    icon: "💰",
    color: "purple",
    examples: [
      {
        id: "uc4_basic_refund",
        title: "Standard refund request",
        useCase: "UC4",
        description: "Customer wants money back",
        message: "I'd like to get a refund for my order #NP7777. The product didn't meet my expectations.",
        expectedAgent: "refund",
        expectedTools: ["get_order_details", "shopify_refund_order"],
        difficulty: "easy",
      },
      {
        id: "uc4_store_credit",
        title: "Refund as store credit",
        useCase: "UC4",
        description: "Customer prefers store credit",
        message: "Can I get store credit instead of a refund? I want to try different products. Order #12345",
        expectedAgent: "refund",
        expectedTools: ["shopify_create_store_credit"],
        difficulty: "medium",
      },
    ],
  },
  {
    id: "uc5",
    name: "UC5: Order Modification",
    icon: "✏️",
    color: "orange",
    examples: [
      {
        id: "uc5_cancel",
        title: "Cancel order",
        useCase: "UC5",
        description: "Customer wants to cancel",
        message: "I need to cancel my order #NP5555. I ordered by mistake and it hasn't shipped yet.",
        expectedAgent: "order_mod",
        expectedTools: ["get_order_details", "shopify_cancel_order"],
        difficulty: "easy",
      },
      {
        id: "uc5_address_change",
        title: "Change shipping address",
        useCase: "UC5",
        description: "Update delivery address",
        message: "Can I update the shipping address for order #12345? I'm moving and need it sent to my new address.",
        expectedAgent: "order_mod",
        expectedTools: ["get_order_details", "shopify_update_order_shipping_address"],
        difficulty: "medium",
      },
    ],
  },
  {
    id: "uc6",
    name: "UC6: Positive Feedback",
    icon: "💬",
    color: "green",
    examples: [
      {
        id: "uc6_happy_customer",
        title: "Happy customer review",
        useCase: "UC6",
        description: "Positive feedback",
        message: "Just wanted to say the BuzzPatches are amazing! My kids love them and they actually work. Best purchase ever!",
        expectedAgent: "feedback",
        expectedTools: ["get_product_recommendations", "shopify_create_discount_code"],
        difficulty: "easy",
      },
      {
        id: "uc6_referral",
        title: "Customer wants to refer friends",
        useCase: "UC6",
        description: "Asking about referral program",
        message: "I love your products! Do you have a referral program? I want to share with my friends.",
        expectedAgent: "feedback",
        expectedTools: ["shopify_create_discount_code"],
        difficulty: "medium",
      },
    ],
  },
  {
    id: "uc7",
    name: "UC7: Subscription Management",
    icon: "🔄",
    color: "indigo",
    examples: [
      {
        id: "uc7_pause",
        title: "Pause subscription",
        useCase: "UC7",
        description: "Customer wants to pause",
        message: "I need to pause my subscription for 2 months. Going on vacation. My email is sub@example.com",
        expectedAgent: "subscription",
        expectedTools: ["skio_get_subscriptions", "skio_pause_subscription"],
        difficulty: "easy",
      },
      {
        id: "uc7_cancel",
        title: "Cancel subscription",
        useCase: "UC7",
        description: "Customer wants to cancel",
        message: "Please cancel my subscription. It's not working for me anymore.",
        expectedAgent: "subscription",
        expectedTools: ["skio_get_subscriptions", "skio_cancel_subscription"],
        difficulty: "medium",
      },
      {
        id: "uc7_skip_order",
        title: "Skip next order",
        useCase: "UC7",
        description: "Skip one delivery",
        message: "Can I skip next month's delivery? I still have plenty left.",
        expectedAgent: "subscription",
        expectedTools: ["skio_skip_next_order_subscription"],
        difficulty: "easy",
      },
    ],
  },
  {
    id: "uc8",
    name: "UC8: Discount Issues",
    icon: "🎟️",
    color: "pink",
    examples: [
      {
        id: "uc8_code_not_working",
        title: "Discount code not working",
        useCase: "UC8",
        description: "Promo code error",
        message: "The code SAVE20 isn't working at checkout. Can you help?",
        expectedAgent: "discount",
        expectedTools: ["shopify_create_discount_code"],
        difficulty: "easy",
      },
      {
        id: "uc8_expired_code",
        title: "Expired discount code",
        useCase: "UC8",
        description: "Code expired, wants new one",
        message: "My discount code expired yesterday. Can I get a new one? I was about to place an order.",
        expectedAgent: "discount",
        expectedTools: ["shopify_create_discount_code"],
        difficulty: "medium",
      },
    ],
  },
];

interface ShowcaseSidebarProps {
  onClose: () => void;
  onExampleSelected: (conversationId: string) => void;
}

const colorClasses: Record<string, string> = {
  blue: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border-blue-200 dark:border-blue-800",
  red: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300 border-red-200 dark:border-red-800",
  yellow: "bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800",
  purple: "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 border-purple-200 dark:border-purple-800",
  orange: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300 border-orange-200 dark:border-orange-800",
  green: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300 border-green-200 dark:border-green-800",
  indigo: "bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800",
  pink: "bg-pink-100 text-pink-800 dark:bg-pink-950 dark:text-pink-300 border-pink-200 dark:border-pink-800",
};

const difficultyColors: Record<string, string> = {
  easy: "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300",
  medium: "bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-300",
  hard: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
};

export function ShowcaseSidebar({ onClose, onExampleSelected }: ShowcaseSidebarProps) {
  const [selectedExample, setSelectedExample] = useState<ExampleScenario | null>(null);
  const [sending, setSending] = useState(false);
  const [expandedUseCase, setExpandedUseCase] = useState<string | null>("uc1");

  const runExample = async (example: ExampleScenario) => {
    setSending(true);
    try {
      // Generate unique conversation ID for this showcase example
      const showcaseId = `showcase_${example.id}_${Date.now()}`;
      
      // Send through the actual agent system
      await sendMessage({
        conversation_id: showcaseId,
        user_id: `showcase_${example.id}`,
        channel: "email",
        customer_email: "showcase@example.com",
        first_name: "Showcase",
        last_name: "Demo",
        shopify_customer_id: "showcase_customer",
        message: example.message,
        // TODO: Add photo_urls if example.hasImage
      });

      // Notify parent to open this conversation
      onExampleSelected(showcaseId);

      // Close sidebar
      setTimeout(() => {
        onClose();
      }, 300);
    } catch (error) {
      console.error("Failed to run example:", error);
      alert("Failed to run example. Check console for details.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-[520px] bg-background border-l shadow-2xl z-50 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50 dark:from-blue-950/20 dark:via-purple-950/20 dark:to-pink-950/20 shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
              <Presentation className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold">Hackathon Showcase</h2>
              <p className="text-xs text-muted-foreground">8 Use Cases • Pre-built Examples</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="shrink-0"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Stats */}
        <div className="flex gap-3 mt-3">
          <div className="flex-1 bg-background/80 backdrop-blur-sm rounded-lg p-2.5 border">
            <div className="text-lg font-bold text-foreground">
              {USE_CASE_EXAMPLES.length}
            </div>
            <div className="text-xs text-muted-foreground">Use Cases</div>
          </div>
          <div className="flex-1 bg-background/80 backdrop-blur-sm rounded-lg p-2.5 border">
            <div className="text-lg font-bold text-foreground">
              {USE_CASE_EXAMPLES.reduce((sum, uc) => sum + uc.examples.length, 0)}
            </div>
            <div className="text-xs text-muted-foreground">Examples</div>
          </div>
          <div className="flex-1 bg-background/80 backdrop-blur-sm rounded-lg p-2.5 border">
            <div className="text-lg font-bold text-foreground">8</div>
            <div className="text-xs text-muted-foreground">Agents</div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <ScrollArea className="h-full">
          <div className="p-6 space-y-4">
            {USE_CASE_EXAMPLES.map((useCase) => (
              <div key={useCase.id} className="rounded-lg border bg-card overflow-hidden">
                {/* Use Case Header */}
                <button
                  onClick={() =>
                    setExpandedUseCase(expandedUseCase === useCase.id ? null : useCase.id)
                  }
                  className="w-full px-4 py-3 flex items-center justify-between bg-muted/30 hover:bg-muted/50 transition-colors border-b"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{useCase.icon}</span>
                    <div className="text-left">
                      <h3 className="text-sm font-semibold">{useCase.name}</h3>
                      <p className="text-xs text-muted-foreground">
                        {useCase.examples.length} example{useCase.examples.length !== 1 ? "s" : ""}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={cn("text-xs", colorClasses[useCase.color])}>
                      {useCase.id.toUpperCase()}
                    </Badge>
                    <svg
                      className={cn(
                        "w-4 h-4 text-muted-foreground transition-transform",
                        expandedUseCase === useCase.id && "rotate-180"
                      )}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>

                {/* Examples List */}
                {expandedUseCase === useCase.id && (
                  <div className="divide-y divide-border">
                    {useCase.examples.map((example) => {
                      const isSelected = selectedExample?.id === example.id;
                      return (
                        <button
                          key={example.id}
                          onClick={() => setSelectedExample(example)}
                          className={cn(
                            "w-full text-left p-4 hover:bg-muted/50 transition-all",
                            isSelected && "bg-primary/5 border-l-2 border-l-primary"
                          )}
                        >
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <div className="flex items-center gap-2">
                              {example.hasImage && (
                                <Image className="w-3.5 h-3.5 text-purple-500" />
                              )}
                              <h4 className="text-sm font-medium">{example.title}</h4>
                            </div>
                            <Badge
                              className={cn("text-[10px]", difficultyColors[example.difficulty])}
                            >
                              {example.difficulty}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mb-2">
                            {example.description}
                          </p>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-[10px] text-muted-foreground">
                              Agent: <code className="font-mono">{example.expectedAgent}</code>
                            </span>
                            <span className="text-[10px] text-muted-foreground">•</span>
                            <span className="text-[10px] text-muted-foreground">
                              {example.expectedTools.length} tool{example.expectedTools.length !== 1 ? "s" : ""}
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Selected Example Detail */}
      {selectedExample && (
        <div className="border-t bg-muted/20 shrink-0">
          <div className="p-4">
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex-1">
                <h3 className="text-sm font-semibold mb-1">{selectedExample.title}</h3>
                <p className="text-xs text-muted-foreground">{selectedExample.description}</p>
              </div>
              <Button
                onClick={() => runExample(selectedExample)}
                disabled={sending}
                size="sm"
                className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 hover:from-blue-600 hover:via-purple-600 hover:to-pink-600 text-white shadow-lg"
              >
                <Play className="w-3.5 h-3.5 mr-1.5" />
                {sending ? "Running..." : "Run Example"}
              </Button>
            </div>

            {/* Message Preview */}
            <div className="bg-background border rounded-lg p-3 text-xs">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Customer Message
                </span>
                {selectedExample.hasImage && (
                  <Badge variant="outline" className="text-[9px]">
                    + Image
                  </Badge>
                )}
              </div>
              <p className="text-foreground leading-relaxed">{selectedExample.message}</p>
            </div>

            {/* Expected Outcome */}
            <div className="mt-3 flex items-center gap-2 text-[10px] text-muted-foreground">
              <span>Expected:</span>
              <code className="font-mono bg-muted px-1.5 py-0.5 rounded">
                {selectedExample.expectedAgent}
              </code>
              <span>→</span>
              <span className="truncate">{selectedExample.expectedTools.slice(0, 2).join(", ")}</span>
              {selectedExample.expectedTools.length > 2 && (
                <span>+{selectedExample.expectedTools.length - 2} more</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="px-6 py-3 border-t bg-muted/30 shrink-0">
        <p className="text-xs text-muted-foreground text-center">
          🎯 Click any example to run it through the live agent system
        </p>
      </div>
    </div>
  );
}
