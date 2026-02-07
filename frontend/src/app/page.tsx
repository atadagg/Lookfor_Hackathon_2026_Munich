"use client";

import { useEffect, useState, useCallback } from "react";
import { ConversationList } from "@/components/conversation-list";
import { ConversationDetail } from "@/components/conversation-detail";
import { PlaygroundSidebar } from "@/components/playground-sidebar";
import { MASBehaviorSidebar } from "@/components/mas-behavior-sidebar";
import { fetchThreads, ThreadSummary } from "@/lib/api";
import { Gamepad2, SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Home() {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [showPlayground, setShowPlayground] = useState(false);
  const [showMASBehavior, setShowMASBehavior] = useState(false);

  const loadThreads = async () => {
    try {
      const data = await fetchThreads();
      setThreads(data);
    } catch {
      // silently retry later
    }
  };

  useEffect(() => {
    // Initial load
    loadThreads();
    
    // Set up polling interval
    const interval = setInterval(() => {
      loadThreads();
    }, 5000);
    
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps - we want this to run once on mount

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
          {/* Search & Playground */}
          <div className="flex gap-2 items-center">
            <div className="relative flex-1">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground"
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
                placeholder="Search conversations..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full h-9 rounded-md border bg-muted/50 pl-9 pr-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring focus:bg-background transition-all placeholder:text-muted-foreground/60"
              />
            </div>
            <Button
              variant="outline"
              onClick={() => setShowPlayground(true)}
              className="h-9 px-3 shrink-0 border-purple-200 bg-gradient-to-r from-purple-50 to-blue-50 hover:from-purple-100 hover:to-blue-100 dark:from-purple-950/20 dark:to-blue-950/20 dark:hover:from-purple-950/30 dark:hover:to-blue-950/30 dark:border-purple-800 transition-all shadow-sm hover:shadow-md"
              title="Open Agent Playground"
            >
              <Gamepad2 className="w-4 h-4 text-purple-600 dark:text-purple-400 mr-1.5" />
              <span className="text-xs font-medium bg-gradient-to-r from-purple-600 to-blue-600 dark:from-purple-400 dark:to-blue-400 bg-clip-text text-transparent">
                Playground
              </span>
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowMASBehavior(true)}
              className="h-9 px-3 shrink-0 border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 hover:from-amber-100 hover:to-orange-100 dark:from-amber-950/20 dark:to-orange-950/20 dark:hover:from-amber-950/30 dark:hover:to-orange-950/30 dark:border-amber-800 transition-all shadow-sm hover:shadow-md"
              title="MAS Behavior"
            >
              <SlidersHorizontal className="w-4 h-4 text-amber-600 dark:text-amber-400 mr-1.5" />
              <span className="text-xs font-medium bg-gradient-to-r from-amber-600 to-orange-600 dark:from-amber-400 dark:to-orange-400 bg-clip-text text-transparent">
                Behavior
              </span>
            </Button>
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

      {/* Playground Sidebar */}
      {showPlayground && (
        <PlaygroundSidebar
          onClose={() => setShowPlayground(false)}
          onTicketSent={(conversationId) => {
            // Auto-select the new conversation
            setSelectedId(conversationId);
            // Reload threads to show the new one
            loadThreads();
          }}
        />
      )}

      {/* MAS Behavior Sidebar */}
      {showMASBehavior && <MASBehaviorSidebar onClose={() => setShowMASBehavior(false)} />}
    </div>
  );
}
