"use client";

import { ThreadState } from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

interface TraceTabProps {
  state: ThreadState | null;
}

export function TraceTab({ state }: TraceTabProps) {
  if (!state) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Loading state...
      </div>
    );
  }

  const traces = state.internal_data?.tool_traces || [];
  const internalData = state.internal_data || {};

  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-4">
        {/* Header summary */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Session Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex flex-wrap gap-2">
              {state.intent && (
                <div className="flex items-center gap-1">
                  <span className="text-muted-foreground">Intent:</span>
                  <Badge variant="secondary">{state.intent}</Badge>
                </div>
              )}
              {state.routed_agent && (
                <div className="flex items-center gap-1">
                  <span className="text-muted-foreground">Agent:</span>
                  <Badge>{state.routed_agent}</Badge>
                </div>
              )}
              {state.current_workflow && (
                <div className="flex items-center gap-1">
                  <span className="text-muted-foreground">Workflow:</span>
                  <Badge variant="outline">{state.current_workflow}</Badge>
                </div>
              )}
            </div>
            {state.workflow_step && (
              <div className="flex items-center gap-1">
                <span className="text-muted-foreground">Step:</span>
                <code className="bg-muted px-1.5 py-0.5 rounded text-xs">{state.workflow_step}</code>
              </div>
            )}
            {state.is_escalated && (
              <Badge variant="destructive">Escalated</Badge>
            )}
          </CardContent>
        </Card>

        <Separator />

        {/* Agent decisions / internal data */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Agent Decisions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {Object.entries(internalData)
              .filter(([k]) => k !== "tool_traces")
              .map(([key, value]) => (
                <div key={key} className="flex items-start gap-2">
                  <span className="text-muted-foreground min-w-[120px] font-mono text-xs">{key}:</span>
                  <span className="text-xs break-all">
                    {typeof value === "object" ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            {Object.entries(internalData).filter(([k]) => k !== "tool_traces").length === 0 && (
              <p className="text-xs text-muted-foreground">No additional decisions recorded.</p>
            )}
          </CardContent>
        </Card>

        <Separator />

        {/* Tool trace timeline */}
        <div>
          <h3 className="text-sm font-semibold mb-3">Tool Calls Timeline</h3>
          {traces.length === 0 ? (
            <p className="text-xs text-muted-foreground">No tool calls recorded.</p>
          ) : (
            <div className="relative border-l-2 border-muted-foreground/20 ml-2 space-y-4">
              {traces.map((trace, i) => (
                <div key={i} className="relative pl-6">
                  <div className="absolute left-[-5px] top-1.5 h-2.5 w-2.5 rounded-full bg-primary" />
                  <Card>
                    <CardContent className="p-3 space-y-1.5">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs font-mono">
                          {trace.name}
                        </Badge>
                        <span className="text-[10px] text-muted-foreground">Step {i + 1}</span>
                      </div>
                      <details className="text-xs">
                        <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                          Inputs
                        </summary>
                        <pre className="mt-1 bg-muted p-2 rounded overflow-x-auto text-[10px]">
                          {JSON.stringify(trace.inputs, null, 2)}
                        </pre>
                      </details>
                      <details className="text-xs">
                        <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                          Output
                        </summary>
                        <pre className="mt-1 bg-muted p-2 rounded overflow-x-auto text-[10px]">
                          {JSON.stringify(trace.output, null, 2)}
                        </pre>
                      </details>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </ScrollArea>
  );
}
