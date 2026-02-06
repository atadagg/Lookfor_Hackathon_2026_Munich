"use client";

import { useEffect, useState } from "react";
import { fetchThread, fetchThreadState, ThreadDetail, ThreadState } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { MessageTab } from "./message-tab";
import { TraceTab } from "./trace-tab";
import { LogsTab } from "./logs-tab";
import { cn } from "@/lib/utils";

interface ConversationDetailProps {
  conversationId: string;
}

const tabs = [
  { id: "message", label: "Message", icon: "M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" },
  { id: "trace", label: "Agent Trace", icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" },
  { id: "logs", label: "Raw Logs", icon: "M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" },
] as const;

type TabId = (typeof tabs)[number]["id"];

export function ConversationDetail({ conversationId }: ConversationDetailProps) {
  const [thread, setThread] = useState<ThreadDetail | null>(null);
  const [state, setState] = useState<ThreadState | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabId>("message");

  useEffect(() => {
    let cancelled = false;

    Promise.all([fetchThread(conversationId), fetchThreadState(conversationId)])
      .then(([t, s]) => {
        if (!cancelled) {
          setThread(t);
          setState(s);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-2">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-muted-foreground">Loading...</span>
        </div>
      </div>
    );
  }

  if (!thread) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Thread not found
      </div>
    );
  }

  const customerName =
    state?.customer_info?.first_name && state?.customer_info?.last_name
      ? `${state.customer_info.first_name} ${state.customer_info.last_name}`
      : state?.customer_info?.email || conversationId;

  const messageCount = thread.messages.length;

  return (
    <div className="flex h-full flex-col">
      {/* Thread header */}
      <div className="border-b px-5 py-3.5 bg-background">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div>
              <h2 className="text-sm font-semibold">{customerName}</h2>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[11px] text-muted-foreground font-mono">
                  {conversationId}
                </span>
                <span className="text-[11px] text-muted-foreground">
                  &middot; {messageCount} message{messageCount !== 1 ? "s" : ""}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            {state?.routed_agent && (
              <Badge className="text-[10px] h-5">{state.routed_agent}</Badge>
            )}
            {thread.is_escalated && (
              <Badge variant="destructive" className="text-[10px] h-5">Escalated</Badge>
            )}
            <Badge variant="outline" className="text-[10px] h-5">{thread.status}</Badge>
          </div>
        </div>
      </div>

      {/* Custom animated tabs */}
      <div className="border-b px-5">
        <nav className="flex gap-6" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "relative flex items-center gap-1.5 py-3 text-xs font-medium transition-colors",
                activeTab === tab.id
                  ? "text-foreground"
                  : "text-muted-foreground hover:text-foreground/70"
              )}
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d={tab.icon} />
              </svg>
              {tab.label}
              {/* Animated underline */}
              {activeTab === tab.id && (
                <span className="absolute inset-x-0 -bottom-px h-[2px] bg-foreground rounded-full animate-in fade-in slide-in-from-left-1 duration-200" />
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      <div className="flex-1 min-h-0">
        {activeTab === "message" && (
          <MessageTab thread={thread} customerName={customerName} />
        )}
        {activeTab === "trace" && (
          <TraceTab state={state} />
        )}
        {activeTab === "logs" && (
          <LogsTab state={state} />
        )}
      </div>
    </div>
  );
}
