"use client";

import { ThreadSummary } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
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

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

const agentColorMap: Record<string, { bg: string; dot: string; badge: string }> = {
  wismo: {
    bg: "bg-blue-500",
    dot: "bg-blue-400",
    badge: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800",
  },
  wrong_item: {
    bg: "bg-red-500",
    dot: "bg-red-400",
    badge: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800",
  },
  product_issue: {
    bg: "bg-orange-500",
    dot: "bg-orange-400",
    badge: "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950 dark:text-orange-300 dark:border-orange-800",
  },
  refund: {
    bg: "bg-amber-500",
    dot: "bg-amber-400",
    badge: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800",
  },
  order_mod: {
    bg: "bg-violet-500",
    dot: "bg-violet-400",
    badge: "bg-violet-50 text-violet-700 border-violet-200 dark:bg-violet-950 dark:text-violet-300 dark:border-violet-800",
  },
  feedback: {
    bg: "bg-emerald-500",
    dot: "bg-emerald-400",
    badge: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800",
  },
  subscription: {
    bg: "bg-pink-500",
    dot: "bg-pink-400",
    badge: "bg-pink-50 text-pink-700 border-pink-200 dark:bg-pink-950 dark:text-pink-300 dark:border-pink-800",
  },
  discount: {
    bg: "bg-cyan-500",
    dot: "bg-cyan-400",
    badge: "bg-cyan-50 text-cyan-700 border-cyan-200 dark:bg-cyan-950 dark:text-cyan-300 dark:border-cyan-800",
  },
};

const fallbackColor = {
  bg: "bg-zinc-500",
  dot: "bg-zinc-400",
  badge: "bg-zinc-50 text-zinc-700 border-zinc-200",
};

export function ConversationList({ threads, selectedId, onSelect }: ConversationListProps) {
  return (
    <ScrollArea className="h-full">
      <div className="flex flex-col">
        {threads.length === 0 && (
          <div className="p-8 text-center">
            <div className="text-muted-foreground text-sm">No conversations yet</div>
            <p className="text-xs text-muted-foreground/60 mt-1">
              Send a message via the API to get started
            </p>
          </div>
        )}
        {threads.map((t) => {
          const colors = agentColorMap[t.routed_agent] || fallbackColor;
          const displayName = t.customer_name?.trim() || t.customer_email || t.conversation_id;
          const initials = t.customer_name?.trim()
            ? getInitials(t.customer_name)
            : (t.customer_email?.[0] || "?").toUpperCase();

          return (
            <button
              key={t.conversation_id}
              onClick={() => onSelect(t.conversation_id)}
              className={cn(
                "flex items-start gap-3 px-3 py-3 text-left transition-all border-b border-border/50",
                "hover:bg-accent/50",
                selectedId === t.conversation_id && "bg-accent"
              )}
            >
              {/* Avatar */}
              <div
                className={cn(
                  "shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-semibold mt-0.5",
                  colors.bg
                )}
              >
                {initials}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-sm truncate">{displayName}</span>
                  <span className="text-[11px] text-muted-foreground whitespace-nowrap shrink-0">
                    {formatDate(t.updated_at)}
                  </span>
                </div>

                <div className="flex items-center gap-1.5 flex-wrap">
                  {t.routed_agent && (
                    <Badge
                      variant="outline"
                      className={cn("text-[10px] px-1.5 py-0 h-4 font-medium border", colors.badge)}
                    >
                      {t.routed_agent}
                    </Badge>
                  )}
                  {t.is_escalated && (
                    <Badge variant="destructive" className="text-[10px] px-1.5 py-0 h-4">
                      escalated
                    </Badge>
                  )}
                </div>

                <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                  {t.first_message || t.intent || "No messages yet"}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </ScrollArea>
  );
}
