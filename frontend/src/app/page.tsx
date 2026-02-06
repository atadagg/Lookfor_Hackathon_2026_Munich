"use client";

import { useEffect, useState, useCallback } from "react";
import { ConversationList } from "@/components/conversation-list";
import { ConversationDetail } from "@/components/conversation-detail";
import { fetchThreads, ThreadSummary } from "@/lib/api";

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
    <div className="h-screen flex bg-background">
      {/* Left panel - fixed width sidebar */}
      <div className="w-[360px] shrink-0 flex flex-col border-r">
        {/* Header */}
        <div className="px-4 py-3 border-b">
          <div className="flex items-center justify-between mb-2.5">
            <h1 className="text-sm font-bold tracking-tight">Lookfor Digital Support</h1>
            <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full font-medium">
              {threads.length} thread{threads.length !== 1 ? "s" : ""}
            </span>
          </div>
          {/* Search */}
          <div className="relative">
            <svg
              className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-md border bg-muted/50 pl-8 pr-3 py-1.5 text-xs outline-none focus:ring-1 focus:ring-ring focus:bg-background transition-colors placeholder:text-muted-foreground/60"
            />
          </div>
        </div>

        {/* List */}
        <div className="flex-1 min-h-0">
          <ConversationList
            threads={filtered}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>
      </div>

      {/* Right panel - detail */}
      <div className="flex-1 min-w-0">
        {selectedId ? (
          <ConversationDetail key={selectedId} conversationId={selectedId} />
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto">
                <svg className="w-6 h-6 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <p className="text-sm text-muted-foreground">
                Select a conversation to view details
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
