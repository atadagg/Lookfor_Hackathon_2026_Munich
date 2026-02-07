"use client";

import { useState, useEffect } from "react";
import { X, RefreshCw, Send, Sparkles, ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui";
import { cn } from "@/lib/utils";
import { API_URL, sendMessage } from "@/lib/api";

interface Ticket {
  conversationId: string;
  customerId: string;
  createdAt: string;
  conversationType: string;
  subject: string;
  conversation: string;
  suggested_intent: string;
  first_message: string;
}

interface IntentCategory {
  name: string;
  count: number;
}

interface PlaygroundSidebarProps {
  onClose: () => void;
  onTicketSent?: (conversationId: string) => void;
}

export function PlaygroundSidebar({ onClose, onTicketSent }: PlaygroundSidebarProps) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [intents, setIntents] = useState<IntentCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [sending, setSending] = useState(false);
  const [selectedIntent, setSelectedIntent] = useState<string | null>(null);
  const [showIntentDropdown, setShowIntentDropdown] = useState(false);

  // Load available intents on mount
  useEffect(() => {
    loadIntents();
  }, []);

  const loadIntents = async () => {
    try {
      const res = await fetch(`${API_URL}/playground/intents`);
      const data = await res.json();
      setIntents(data.intents);
    } catch (error) {
      console.error("Failed to load intents:", error);
    }
  };

  const loadRandomTickets = async (intentFilter?: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/playground/random`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          count: 5,
          intent_filter: intentFilter || undefined,
        }),
      });
      const data = await res.json();
      setTickets(data.tickets);
      if (data.tickets.length > 0) {
        setSelectedTicket(data.tickets[0]);
      }
    } catch (error) {
      console.error("Failed to load tickets:", error);
    } finally {
      setLoading(false);
    }
  };

  const sendTicket = async () => {
    if (!selectedTicket) return;

    setSending(true);
    try {
      // Generate a unique conversation ID for this test
      const testConversationId = `playground_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Extract customer info
      const customerId = selectedTicket.customerId;
      const firstName = "Test";
      const lastName = "Customer";
      const email = `${customerId}@example.com`;

      // Send the ticket through the actual agent system
      await sendMessage({
        conversation_id: testConversationId,
        user_id: customerId,
        channel: "email",
        customer_email: email,
        first_name: firstName,
        last_name: lastName,
        shopify_customer_id: customerId,
        message: selectedTicket.first_message,
      });

      // Notify parent that ticket was sent
      if (onTicketSent) {
        onTicketSent(testConversationId);
      }

      // Close sidebar after successful send
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (error) {
      console.error("Failed to send ticket:", error);
      alert("Failed to send ticket. Check console for details.");
    } finally {
      setSending(false);
    }
  };

  const intentColors: Record<string, string> = {
    wismo: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
    wrong_item: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
    refund: "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300",
    order_mod: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300",
    product_issue: "bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300",
    subscription: "bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300",
    discount: "bg-pink-100 text-pink-800 dark:bg-pink-950 dark:text-pink-300",
    feedback: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300",
    unknown: "bg-gray-100 text-gray-800 dark:bg-gray-950 dark:text-gray-300",
  };

  return (
    <div className="fixed inset-y-0 right-0 w-[480px] bg-background border-l shadow-2xl z-50 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20 shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold">Agent Playground</h2>
              <p className="text-xs text-muted-foreground">Test with real customer scenarios</p>
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

        {/* Intent Filter */}
        <div className="relative mt-3">
          <button
            onClick={() => setShowIntentDropdown(!showIntentDropdown)}
            className="w-full flex items-center justify-between px-3 py-2 text-sm bg-background border rounded-md hover:bg-muted transition-colors"
          >
            <span className="text-muted-foreground">
              {selectedIntent ? `Filter: ${selectedIntent}` : "All Intents"}
            </span>
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          </button>
          
          {showIntentDropdown && (
            <div className="absolute top-full mt-1 w-full bg-background border rounded-md shadow-lg z-10 max-h-64 overflow-y-auto">
              <button
                onClick={() => {
                  setSelectedIntent(null);
                  setShowIntentDropdown(false);
                }}
                className="w-full px-3 py-2 text-sm text-left hover:bg-muted transition-colors flex items-center justify-between"
              >
                <span>All Intents</span>
                <Badge variant="secondary" className="text-xs">
                  {intents.reduce((sum, i) => sum + i.count, 0)}
                </Badge>
              </button>
              {intents.map((intent) => (
                <button
                  key={intent.name}
                  onClick={() => {
                    setSelectedIntent(intent.name);
                    setShowIntentDropdown(false);
                  }}
                  className="w-full px-3 py-2 text-sm text-left hover:bg-muted transition-colors flex items-center justify-between"
                >
                  <span className="capitalize">{intent.name.replace("_", " ")}</span>
                  <Badge variant="secondary" className="text-xs">
                    {intent.count}
                  </Badge>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 mt-3">
          <Button
            onClick={() => loadRandomTickets(selectedIntent || undefined)}
            disabled={loading}
            variant="outline"
            size="sm"
            className="flex-1"
          >
            <RefreshCw className={cn("w-3.5 h-3.5 mr-2", loading && "animate-spin")} />
            {loading ? "Loading..." : "Load Random"}
          </Button>
          <Button
            onClick={sendTicket}
            disabled={!selectedTicket || sending}
            size="sm"
            className="flex-1 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
          >
            <Send className="w-3.5 h-3.5 mr-2" />
            {sending ? "Sending..." : "Send to Agents"}
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <ScrollArea className="h-full">
          <div className="p-6 space-y-4">
          {tickets.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground mb-2">
                No scenarios loaded yet
              </p>
              <p className="text-xs text-muted-foreground">
                Click &quot;Load Random&quot; to get test scenarios
              </p>
            </div>
          ) : (
            <>
              {/* Ticket List */}
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Scenarios ({tickets.length})
                </h3>
                {tickets.map((ticket, idx) => (
                  <button
                    key={ticket.conversationId}
                    onClick={() => setSelectedTicket(ticket)}
                    className={cn(
                      "w-full text-left p-3 rounded-lg border transition-all",
                      selectedTicket?.conversationId === ticket.conversationId
                        ? "border-primary bg-primary/5 shadow-sm"
                        : "border-border hover:border-muted-foreground/30 hover:bg-muted/50"
                    )}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="text-xs font-mono text-muted-foreground">
                        #{idx + 1}
                      </span>
                      <Badge
                        className={cn(
                          "text-xs",
                          intentColors[ticket.suggested_intent] || intentColors.unknown
                        )}
                      >
                        {ticket.suggested_intent.replace("_", " ")}
                      </Badge>
                    </div>
                    <p className="text-sm font-medium line-clamp-1 mb-1">
                      {ticket.subject}
                    </p>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {ticket.first_message}
                    </p>
                  </button>
                ))}
              </div>

              {/* Selected Ticket Detail */}
              {selectedTicket && (
                <div className="border rounded-lg p-4 bg-muted/30">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                    Selected Scenario
                  </h3>
                  
                  <div className="space-y-3">
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Subject</div>
                      <div className="text-sm font-medium">{selectedTicket.subject}</div>
                    </div>
                    
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Customer Message</div>
                      <div className="text-sm bg-background border rounded-md p-3 max-h-32 overflow-y-auto">
                        {selectedTicket.first_message}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs">
                      <div>
                        <span className="text-muted-foreground">Intent:</span>{" "}
                        <Badge
                          className={cn(
                            "text-xs ml-1",
                            intentColors[selectedTicket.suggested_intent] || intentColors.unknown
                          )}
                        >
                          {selectedTicket.suggested_intent.replace("_", " ")}
                        </Badge>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Type:</span>{" "}
                        <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
                          {selectedTicket.conversationType}
                        </code>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          </div>
        </ScrollArea>
      </div>

      {/* Footer */}
      <div className="px-6 py-3 border-t bg-muted/30 shrink-0">
        <p className="text-xs text-muted-foreground text-center">
          💡 These are real anonymized customer tickets. Send them to test your multi-agent system.
        </p>
      </div>
    </div>
  );
}
