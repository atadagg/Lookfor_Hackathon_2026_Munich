"use client";

import { ThreadSummary } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

interface ConversationListProps {
  threads: ThreadSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

function formatDate(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) {
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

const agentColors: Record<string, string> = {
  wismo: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  wrong_item: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  product_issue: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  refund: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  order_mod: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  feedback: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  subscription: "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200",
  discount: "bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200",
};

export function ConversationList({ threads, selectedId, onSelect }: ConversationListProps) {
  return (
    <ScrollArea className="h-full">
      <div className="flex flex-col">
        {threads.length === 0 && (
          <div className="p-6 text-center text-sm text-muted-foreground">
            No conversations yet
          </div>
        )}
        {threads.map((t, i) => (
          <div key={t.conversation_id}>
            <button
              onClick={() => onSelect(t.conversation_id)}
              className={cn(
                "flex w-full flex-col gap-1 p-3 text-left text-sm transition-colors hover:bg-accent",
                selectedId === t.conversation_id && "bg-muted"
              )}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold truncate max-w-[160px]">
                  {t.customer_name || t.customer_email || t.conversation_id}
                </span>
                <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
                  {formatDate(t.updated_at)}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                {t.routed_agent && (
                  <Badge
                    variant="secondary"
                    className={cn("text-[10px] px-1.5 py-0", agentColors[t.routed_agent] || "")}
                  >
                    {t.routed_agent}
                  </Badge>
                )}
                {t.is_escalated && (
                  <Badge variant="destructive" className="text-[10px] px-1.5 py-0">
                    escalated
                  </Badge>
                )}
                <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                  {t.status}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
                {t.first_message || t.intent || "No messages yet"}
              </p>
            </button>
            {i < threads.length - 1 && <Separator />}
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
