"use client";

import { useState, useEffect } from "react";
import { X, Play, ChevronDown, ChevronRight, Package, XCircle, Wrench, DollarSign, Edit3, MessageSquare, RotateCw, Ticket } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { sendMessage } from "@/lib/api";

interface RealTicket {
  conversationId: string;
  customerId: string;
  createdAt: string;
  conversationType: string;
  subject: string;
  conversation: string;
}

interface CategorizedTicket extends RealTicket {
  category: string;
  categoryLabel: string;
  difficulty: "easy" | "medium" | "hard";
  expectedAgent: string;
}

interface ShowcaseSidebarProps {
  onClose: () => void;
  onExampleSelected: (conversationId: string) => void;
}

const USE_CASE_CATEGORIES = [
  { id: "wismo", label: "UC1: Order Tracking", icon: Package, color: "blue" },
  { id: "wrong_item", label: "UC2: Wrong/Missing Item", icon: XCircle, color: "red" },
  { id: "product_issue", label: "UC3: Product Defect", icon: Wrench, color: "amber" },
  { id: "refund", label: "UC4: Refund Request", icon: DollarSign, color: "purple" },
  { id: "order_mod", label: "UC5: Order Modification", icon: Edit3, color: "orange" },
  { id: "feedback", label: "UC6: Feedback", icon: MessageSquare, color: "green" },
  { id: "subscription", label: "UC7: Subscription", icon: RotateCw, color: "indigo" },
  { id: "discount", label: "UC8: Discount Issues", icon: Ticket, color: "pink" },
];

const colorClasses: Record<string, string> = {
  blue: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  red: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
  amber: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  purple: "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
  orange: "bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-300",
  green: "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300",
  indigo: "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300",
  pink: "bg-pink-100 text-pink-700 dark:bg-pink-950 dark:text-pink-300",
};

const difficultyColors: Record<string, string> = {
  easy: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  medium: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  hard: "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
};

function categorizeTicket(ticket: RealTicket): CategorizedTicket {
  const subject = ticket.subject.toLowerCase();
  const conversation = ticket.conversation.toLowerCase();
  const combined = subject + " " + conversation;

  // WISMO patterns
  if (
    combined.includes("where is") ||
    combined.includes("tracking") ||
    combined.includes("shipped") ||
    combined.includes("not received") ||
    combined.includes("order status") ||
    combined.includes("delivery")
  ) {
    return {
      ...ticket,
      category: "wismo",
      categoryLabel: "Order Tracking",
      difficulty: combined.includes("not received") ? "hard" : "medium",
      expectedAgent: "wismo",
    };
  }

  // Wrong item patterns
  if (
    combined.includes("wrong") ||
    combined.includes("missing") ||
    combined.includes("incorrect") ||
    combined.includes("didn't receive") ||
    combined.includes("received all packs for kids")
  ) {
    return {
      ...ticket,
      category: "wrong_item",
      categoryLabel: "Wrong/Missing Item",
      difficulty: "hard",
      expectedAgent: "wrong_item",
    };
  }

  // Product issue patterns
  if (
    combined.includes("fall off") ||
    combined.includes("not working") ||
    combined.includes("don't work") ||
    combined.includes("defective") ||
    combined.includes("quality issue") ||
    combined.includes("old version")
  ) {
    return {
      ...ticket,
      category: "product_issue",
      categoryLabel: "Product Defect",
      difficulty: "medium",
      expectedAgent: "product_issue",
    };
  }

  // Refund patterns
  if (
    combined.includes("refund") ||
    combined.includes("money back") ||
    combined.includes("return")
  ) {
    return {
      ...ticket,
      category: "refund",
      categoryLabel: "Refund Request",
      difficulty: "easy",
      expectedAgent: "refund",
    };
  }

  // Subscription patterns
  if (
    combined.includes("subscription") ||
    combined.includes("cancel subscription") ||
    combined.includes("pause subscription")
  ) {
    return {
      ...ticket,
      category: "subscription",
      categoryLabel: "Subscription",
      difficulty: "easy",
      expectedAgent: "subscription",
    };
  }

  // Discount patterns
  if (
    combined.includes("discount") ||
    combined.includes("coupon") ||
    combined.includes("promo code")
  ) {
    return {
      ...ticket,
      category: "discount",
      categoryLabel: "Discount",
      difficulty: "easy",
      expectedAgent: "discount",
    };
  }

  // Order modification patterns
  if (
    combined.includes("cancel order") ||
    combined.includes("change address") ||
    combined.includes("modify order")
  ) {
    return {
      ...ticket,
      category: "order_mod",
      categoryLabel: "Order Modification",
      difficulty: "medium",
      expectedAgent: "order_mod",
    };
  }

  // Feedback patterns (default)
  return {
    ...ticket,
    category: "feedback",
    categoryLabel: "Feedback",
    difficulty: "easy",
    expectedAgent: "feedback",
  };
}

function extractFirstMessage(conversation: string): string {
  const customerMatch = conversation.match(/Customer's message: "([^"]*)"/);
  if (customerMatch) {
    return customerMatch[1].substring(0, 200).trim() + (customerMatch[1].length > 200 ? "..." : "");
  }
  return conversation.substring(0, 200).trim() + (conversation.length > 200 ? "..." : "");
}

export function ShowcaseSidebar({ onClose, onExampleSelected }: ShowcaseSidebarProps) {
  const [tickets, setTickets] = useState<CategorizedTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState<CategorizedTicket | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<string | null>("wismo");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadTickets();
  }, []);

  const loadTickets = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/showcase-tickets.json");
      const rawTickets: RealTicket[] = await response.json();
      
      // Categorize and take max 3 per category for cleaner UI
      const categorized = rawTickets.map(categorizeTicket);
      const byCategory = new Map<string, CategorizedTicket[]>();
      
      categorized.forEach((ticket) => {
        if (!byCategory.has(ticket.category)) {
          byCategory.set(ticket.category, []);
        }
        const existing = byCategory.get(ticket.category)!;
        if (existing.length < 4) {
          existing.push(ticket);
        }
      });

      const final: CategorizedTicket[] = [];
      USE_CASE_CATEGORIES.forEach((cat) => {
        const tickets = byCategory.get(cat.id) || [];
        final.push(...tickets);
      });

      setTickets(final);
    } catch (error) {
      console.error("Failed to load showcase tickets:", error);
    } finally {
      setLoading(false);
    }
  };

  const runExample = async (ticket: CategorizedTicket) => {
    setSending(true);
    try {
      const showcaseId = `showcase_${ticket.customerId}_${Date.now()}`;
      const firstMessage = extractFirstMessage(ticket.conversation);

      await sendMessage({
        conversation_id: showcaseId,
        user_id: ticket.customerId,
        channel: ticket.conversationType || "email",
        customer_email: `${ticket.customerId}@example.com`,
        first_name: "Showcase",
        last_name: "Customer",
        shopify_customer_id: ticket.customerId,
        message: firstMessage,
      });

      onExampleSelected(showcaseId);
      setTimeout(() => onClose(), 300);
    } catch (error) {
      console.error("Failed to run example:", error);
      alert("Failed to run example. Check console for details.");
    } finally {
      setSending(false);
    }
  };

  const ticketsByCategory = tickets.reduce((acc, ticket) => {
    if (!acc[ticket.category]) {
      acc[ticket.category] = [];
    }
    acc[ticket.category].push(ticket);
    return acc;
  }, {} as Record<string, CategorizedTicket[]>);

  return (
    <div className="fixed inset-y-0 right-0 w-[500px] bg-background border-l shadow-2xl z-50 flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-sm font-semibold">Hackathon Showcase</h2>
          <p className="text-xs text-muted-foreground">
            {tickets.length} real tickets across {USE_CASE_CATEGORIES.length} use cases
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose} className="shrink-0">
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Stats */}
      <div className="px-4 py-2 border-b bg-muted/30 shrink-0">
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-background border rounded p-2">
            <div className="text-lg font-bold">{USE_CASE_CATEGORIES.length}</div>
            <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Use Cases</div>
          </div>
          <div className="bg-background border rounded p-2">
            <div className="text-lg font-bold">{tickets.length}</div>
            <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Examples</div>
          </div>
          <div className="bg-background border rounded p-2">
            <div className="text-lg font-bold">8</div>
            <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Agents</div>
          </div>
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {loading ? (
            <div className="text-center py-8 text-sm text-muted-foreground">Loading tickets...</div>
          ) : (
            USE_CASE_CATEGORIES.map((category) => {
              const categoryTickets = ticketsByCategory[category.id] || [];
              if (categoryTickets.length === 0) return null;
              
              const Icon = category.icon;
              const isExpanded = expandedCategory === category.id;

              return (
                <div key={category.id} className="border rounded-lg overflow-hidden bg-card">
                  {/* Category Header */}
                  <button
                    onClick={() => setExpandedCategory(isExpanded ? null : category.id)}
                    className="w-full px-3 py-2.5 flex items-center justify-between bg-muted/30 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm font-medium">{category.label}</span>
                      <Badge variant="outline" className="text-xs">
                        {categoryTickets.length}
                      </Badge>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    )}
                  </button>

                  {/* Tickets List */}
                  {isExpanded && (
                    <div className="divide-y">
                      {categoryTickets.map((ticket, idx) => {
                        const isSelected = selectedTicket?.conversationId === ticket.conversationId;
                        const message = extractFirstMessage(ticket.conversation);

                        return (
                          <button
                            key={ticket.conversationId}
                            onClick={() => setSelectedTicket(ticket)}
                            className={cn(
                              "w-full text-left px-3 py-2.5 hover:bg-muted/30 transition-colors",
                              isSelected && "bg-primary/5 border-l-2 border-l-primary"
                            )}
                          >
                            <div className="flex items-start justify-between gap-2 mb-1.5">
                              <span className="text-xs font-medium line-clamp-1">
                                {ticket.subject}
                              </span>
                              <Badge className={cn("text-[9px] shrink-0", difficultyColors[ticket.difficulty])}>
                                {ticket.difficulty}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                              {message}
                            </p>
                            <div className="flex items-center gap-1.5 mt-1.5">
                              <span className="text-[9px] text-muted-foreground">
                                Agent: <code className="font-mono">{ticket.expectedAgent}</code>
                              </span>
                              <span className="text-[9px] text-muted-foreground">•</span>
                              <span className="text-[9px] text-muted-foreground">
                                {ticket.createdAt}
                              </span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </ScrollArea>

      {/* Selected Ticket Detail */}
      {selectedTicket && (
        <div className="border-t bg-muted/20 p-4 shrink-0">
          <div className="flex items-start justify-between gap-2 mb-3">
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold mb-0.5 truncate">{selectedTicket.subject}</h3>
              <p className="text-xs text-muted-foreground">
                {selectedTicket.categoryLabel} • {selectedTicket.difficulty}
              </p>
            </div>
            <Button
              onClick={() => runExample(selectedTicket)}
              disabled={sending}
              size="sm"
              className="shrink-0"
            >
              <Play className="w-3.5 h-3.5 mr-1.5" />
              {sending ? "Running..." : "Run"}
            </Button>
          </div>

          {/* Message Preview */}
          <div className="bg-background border rounded-lg p-3 text-xs">
            <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Customer Message
            </div>
            <p className="text-foreground leading-relaxed line-clamp-4">
              {extractFirstMessage(selectedTicket.conversation)}
            </p>
          </div>

          {/* Expected Outcome */}
          <div className="mt-3 flex items-center gap-2 text-[10px] text-muted-foreground">
            <span>Expected Agent:</span>
            <code className="font-mono bg-muted px-1.5 py-0.5 rounded">
              {selectedTicket.expectedAgent}
            </code>
          </div>
        </div>
      )}
    </div>
  );
}
