"use client";

import { useEffect, useState } from "react";
import { fetchThread, fetchThreadState, ThreadDetail, ThreadState } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { MessageTab } from "./message-tab";
import { TraceTab } from "./trace-tab";
import { LogsTab } from "./logs-tab";

interface ConversationDetailProps {
  conversationId: string;
}

export function ConversationDetail({ conversationId }: ConversationDetailProps) {
  const [thread, setThread] = useState<ThreadDetail | null>(null);
  const [state, setState] = useState<ThreadState | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

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
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Loading conversation...
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

  return (
    <div className="flex h-full flex-col">
      {/* Thread header */}
      <div className="border-b px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold">{customerName}</h2>
            <p className="text-xs text-muted-foreground">{conversationId}</p>
          </div>
          <div className="flex items-center gap-2">
            {state?.routed_agent && <Badge>{state.routed_agent}</Badge>}
            {thread.is_escalated && <Badge variant="destructive">Escalated</Badge>}
            <Badge variant="outline">{thread.status}</Badge>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="message" className="flex-1 flex flex-col min-h-0">
        <TabsList className="w-full justify-start rounded-none border-b bg-transparent px-4 h-10">
          <TabsTrigger value="message" className="text-xs">
            Message
          </TabsTrigger>
          <TabsTrigger value="trace" className="text-xs">
            Agent Trace
          </TabsTrigger>
          <TabsTrigger value="logs" className="text-xs">
            Raw Logs
          </TabsTrigger>
        </TabsList>
        <TabsContent value="message" className="flex-1 mt-0 min-h-0">
          <MessageTab thread={thread} />
        </TabsContent>
        <TabsContent value="trace" className="flex-1 mt-0 min-h-0">
          <TraceTab state={state} />
        </TabsContent>
        <TabsContent value="logs" className="flex-1 mt-0 min-h-0">
          <LogsTab state={state} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
