"use client";

import { ThreadState, ToolTrace } from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface LogsTabProps {
  state: ThreadState | null;
}

function JsonBlock({ data, label }: { data: unknown; label: string }) {
  return (
    <details className="text-xs">
      <summary className="cursor-pointer text-muted-foreground hover:text-foreground font-medium">
        {label}
      </summary>
      <pre className="mt-1 bg-muted p-3 rounded overflow-x-auto max-h-[300px] text-[11px] leading-4">
        {JSON.stringify(data, null, 2)}
      </pre>
    </details>
  );
}

function ToolTraceCard({ trace, index }: { trace: ToolTrace; index: number }) {
  const isSuccess =
    trace.output &&
    typeof trace.output === "object" &&
    "success" in trace.output &&
    (trace.output as Record<string, unknown>).success === true;

  return (
    <Card className="border-muted">
      <CardContent className="p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">#{index + 1}</span>
            <code className="text-xs font-semibold font-mono">{trace.name}</code>
          </div>
          <Badge variant={isSuccess ? "secondary" : "destructive"} className="text-[10px]">
            {isSuccess ? "success" : "failed"}
          </Badge>
        </div>
        <Separator />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <div>
            <span className="text-[10px] font-medium text-muted-foreground uppercase">Input</span>
            <pre className="mt-1 bg-muted p-2 rounded overflow-x-auto max-h-[200px] text-[10px] leading-3.5">
              {JSON.stringify(trace.inputs, null, 2)}
            </pre>
          </div>
          <div>
            <span className="text-[10px] font-medium text-muted-foreground uppercase">Output</span>
            <pre className="mt-1 bg-muted p-2 rounded overflow-x-auto max-h-[200px] text-[10px] leading-3.5">
              {JSON.stringify(trace.output, null, 2)}
            </pre>
          </div>
        </div>
      </CardContent>
    </Card>
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
      <div className="p-4 space-y-4">
        {/* Tool calls */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Tool Calls ({traces.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {traces.length === 0 ? (
              <p className="text-xs text-muted-foreground">No tool calls in this session.</p>
            ) : (
              traces.map((t, i) => <ToolTraceCard key={i} trace={t} index={i} />)
            )}
          </CardContent>
        </Card>

        <Separator />

        {/* Full JSON state */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Full State Snapshot</CardTitle>
          </CardHeader>
          <CardContent>
            <JsonBlock data={stateSnapshot} label="Expand full JSON state" />
          </CardContent>
        </Card>

        {/* Slots */}
        {state.slots && Object.keys(state.slots).length > 0 && (
          <>
            <Separator />
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold">Slots</CardTitle>
              </CardHeader>
              <CardContent>
                <JsonBlock data={state.slots} label="Expand slot data" />
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </ScrollArea>
  );
}
