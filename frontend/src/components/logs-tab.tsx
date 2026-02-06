"use client";

import { ThreadState, ToolTrace } from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface LogsTabProps {
  state: ThreadState | null;
}

function ToolTraceCard({ trace, index }: { trace: ToolTrace; index: number }) {
  const isSuccess =
    trace.output &&
    typeof trace.output === "object" &&
    "success" in trace.output &&
    (trace.output as Record<string, unknown>).success === true;

  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-muted/30 border-b">
        <div className="flex items-center gap-2.5">
          <span className="text-[10px] text-muted-foreground font-mono w-5 text-right">
            {String(index + 1).padStart(2, "0")}
          </span>
          <code className="text-xs font-semibold font-mono">{trace.name}</code>
        </div>
        <div
          className={cn(
            "text-[10px] font-medium px-2 py-0.5 rounded-full",
            isSuccess
              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
              : "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
          )}
        >
          {isSuccess ? "200 OK" : "ERROR"}
        </div>
      </div>

      {/* Body: side-by-side input/output */}
      <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-border">
        <div className="p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <svg className="w-3 h-3 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14" />
            </svg>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Request
            </span>
          </div>
          <pre className="bg-muted/50 rounded-md p-2.5 overflow-x-auto max-h-[220px] text-[11px] leading-4 font-mono text-foreground">
            {JSON.stringify(trace.inputs, null, 2)}
          </pre>
        </div>
        <div className="p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <svg className="w-3 h-3 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4" />
            </svg>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Response
            </span>
          </div>
          <pre className="bg-muted/50 rounded-md p-2.5 overflow-x-auto max-h-[220px] text-[11px] leading-4 font-mono text-foreground">
            {JSON.stringify(trace.output, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}

export function LogsTab({ state }: LogsTabProps) {
  if (!state) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Loading state...
      </div>
    );
  }

  const traces = state.internal_data?.tool_traces || [];

  // Build a clean state snapshot without messages (they're in the Message tab)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { messages: _msgs, ...stateSnapshot } = state;

  return (
    <ScrollArea className="h-full">
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        {/* Tool calls section */}
        <div>
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
            </svg>
            Tool Calls
            <Badge variant="secondary" className="text-[10px]">{traces.length}</Badge>
          </h3>

          {traces.length === 0 ? (
            <div className="rounded-lg border bg-card p-8 text-center">
              <p className="text-xs text-muted-foreground">No tool calls in this session.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {traces.map((t, i) => (
                <ToolTraceCard key={i} trace={t} index={i} />
              ))}
            </div>
          )}
        </div>

        {/* Full JSON state */}
        <div className="rounded-lg border bg-card overflow-hidden">
          <details className="group">
            <summary className="px-4 py-3 cursor-pointer hover:bg-muted/30 transition-colors flex items-center gap-2">
              <svg className="w-3.5 h-3.5 transition-transform group-open:rotate-90 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
              <span className="text-sm font-semibold">Full State Snapshot</span>
              <span className="text-[10px] text-muted-foreground ml-1">JSON</span>
            </summary>
            <div className="border-t px-4 py-3">
              <pre className="bg-muted/50 rounded-md p-4 overflow-x-auto max-h-[400px] text-[11px] leading-4 font-mono">
                {JSON.stringify(stateSnapshot, null, 2)}
              </pre>
            </div>
          </details>
        </div>

        {/* Slots */}
        {state.slots && Object.keys(state.slots).length > 0 && (
          <div className="rounded-lg border bg-card overflow-hidden">
            <details className="group">
              <summary className="px-4 py-3 cursor-pointer hover:bg-muted/30 transition-colors flex items-center gap-2">
                <svg className="w-3.5 h-3.5 transition-transform group-open:rotate-90 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
                <span className="text-sm font-semibold">Slots</span>
              </summary>
              <div className="border-t px-4 py-3">
                <pre className="bg-muted/50 rounded-md p-4 overflow-x-auto max-h-[300px] text-[11px] leading-4 font-mono">
                  {JSON.stringify(state.slots, null, 2)}
                </pre>
              </div>
            </details>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
