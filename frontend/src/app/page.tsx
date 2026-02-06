"use client";

import { useEffect, useState, useCallback } from "react";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { ConversationList } from "@/components/conversation-list";
import { ConversationDetail } from "@/components/conversation-detail";
import { fetchThreads, ThreadSummary } from "@/lib/api";
import { Separator } from "@/components/ui/separator";

export default function Home() {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const loadThreads = useCallback(async () => {
    try {
      const data = await fetchThreads();
      setThreads(data);
    } catch {
      // silently retry later
    }
  }, []);

  useEffect(() => {
    loadThreads();
    const interval = setInterval(loadThreads, 5000);
    return () => clearInterval(interval);
  }, [loadThreads]);

  const filtered = threads.filter((t) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      t.conversation_id.toLowerCase().includes(q) ||
      t.customer_email?.toLowerCase().includes(q) ||
      t.customer_name?.toLowerCase().includes(q) ||
      t.routed_agent?.toLowerCase().includes(q) ||
      t.intent?.toLowerCase().includes(q) ||
      t.first_message?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="h-screen flex flex-col">
      {/* Top bar */}
      <header className="border-b px-4 py-2 flex items-center justify-between shrink-0">
        <h1 className="text-sm font-bold tracking-tight">
          Fidelio Support Dashboard
        </h1>
        <span className="text-xs text-muted-foreground">
          {threads.length} thread{threads.length !== 1 ? "s" : ""}
        </span>
      </header>

      {/* Main content */}
      <ResizablePanelGroup orientation="horizontal" className="flex-1 min-h-0">
        {/* Left panel - conversation list */}
        <ResizablePanel defaultSize={30} minSize={20} maxSize={45}>
          <div className="flex h-full flex-col">
            {/* Search */}
            <div className="p-2">
              <input
                type="text"
                placeholder="Search conversations..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
            <Separator />
            <div className="flex-1 min-h-0">
              <ConversationList
                threads={filtered}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Right panel - detail */}
        <ResizablePanel defaultSize={70}>
          {selectedId ? (
            <ConversationDetail
              key={selectedId}
              conversationId={selectedId}
            />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              Select a conversation to view details
            </div>
          )}
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
