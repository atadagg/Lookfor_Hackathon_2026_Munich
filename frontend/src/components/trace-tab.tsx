"use client";

import { AgentTurnRecord, ThreadState, ToolTrace } from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface TraceTabProps {
  state: ThreadState | null;
}

/* ── Build real graph nodes from actual DB state ── */

interface GraphNode {
  id: string;
  label: string;
  sublabel?: string;
  status: "completed" | "active" | "pending";
  type: "start" | "route" | "tool" | "decision" | "end" | "escalation";
}

function buildGraphNodes(state: ThreadState): GraphNode[] {
  const nodes: GraphNode[] = [];
  const history = state.agent_turn_history || [];
  const internalData = state.internal_data || {};

  // When we have per-turn history, show each turn (route + tools) so agent changes are visible
  if (history.length > 0) {
    history.forEach((turn, turnIdx) => {
      const isLastTurn = turnIdx === history.length - 1;
      nodes.push({
        id: `route-${turnIdx}`,
        label: "Routed",
        sublabel: turn.agent,
        status: "completed",
        type: "route",
      });
      (turn.tool_traces || []).forEach((trace, i) => {
        const isSuccess =
          trace.output &&
          typeof trace.output === "object" &&
          "success" in trace.output &&
          (trace.output as Record<string, unknown>).success === true;
        nodes.push({
          id: `turn-${turnIdx}-tool-${i}`,
          label: trace.name,
          sublabel: isSuccess ? "success" : "failed",
          status: "completed",
          type: "tool",
        });
      });
      if (isLastTurn && (state.is_escalated || state.workflow_step)) {
        if (state.is_escalated) {
          nodes.push({
            id: "escalated",
            label: "Escalated",
            sublabel: "Handed to human agent",
            status: "active",
            type: "escalation",
          });
        } else {
          nodes.push({
            id: "responded",
            label: "Response Sent",
            sublabel: (state.workflow_step || "").replace(/_/g, " "),
            status: "active",
            type: "end",
          });
        }
      }
    });
    if (nodes.length > 0) return nodes;
  }

  // Fallback: single-agent view (no agent_turn_history)
  const traces: ToolTrace[] = state.internal_data?.tool_traces || [];
  nodes.push({
    id: "intent",
    label: "Intent Classified",
    sublabel: state.intent || "unknown",
    status: "completed",
    type: "start",
  });
  if (state.routed_agent) {
    nodes.push({
      id: "route",
      label: "Routed",
      sublabel: state.routed_agent,
      status: "completed",
      type: "route",
    });
  }
  traces.forEach((trace, i) => {
    const isSuccess =
      trace.output &&
      typeof trace.output === "object" &&
      "success" in trace.output &&
      (trace.output as Record<string, unknown>).success === true;
    nodes.push({
      id: `tool-${i}`,
      label: trace.name,
      sublabel: isSuccess ? "success" : "failed",
      status: "completed",
      type: "tool",
    });
  });
  const decisionKeys = ["decided_action", "order_status", "promise_day_label", "wait_promise_until"];
  for (const key of decisionKeys) {
    if (internalData[key] !== undefined) {
      nodes.push({
        id: `decision-${key}`,
        label: key.replace(/_/g, " "),
        sublabel: String(internalData[key]),
        status: "completed",
        type: "decision",
      });
    }
  }
  if (state.is_escalated) {
    nodes.push({
      id: "escalated",
      label: "Escalated",
      sublabel: "Handed to human agent",
      status: "active",
      type: "escalation",
    });
  } else if (state.workflow_step) {
    nodes.push({
      id: "responded",
      label: "Response Sent",
      sublabel: state.workflow_step.replace(/_/g, " "),
      status: "active",
      type: "end",
    });
  }

  return nodes;
}

const nodeIcons: Record<string, string> = {
  start: "M13 10V3L4 14h7v7l9-11h-7z",
  route: "M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5",
  tool: "M14.25 9.75L16.5 12l-2.25 2.25m-4.5 0L7.5 12l2.25-2.25M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z",
  decision: "M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z",
  end: "M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  escalation: "M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z",
};

function WorkflowNodeGraph({ state }: { state: ThreadState }) {
  const nodes = buildGraphNodes(state);

  if (nodes.length === 0) return null;

  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <div className="px-5 py-3.5 border-b bg-muted/20">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
          </svg>
          Execution Flow
          <span className="text-[10px] font-normal text-muted-foreground ml-auto">
            {nodes.length} step{nodes.length !== 1 ? "s" : ""}
          </span>
        </h3>
      </div>

      <div className="p-5">
        <div className="relative">
          {nodes.map((node, i) => {
            const icon = nodeIcons[node.type] || nodeIcons.tool;
            const isLast = i === nodes.length - 1;
            const isEscalation = node.type === "escalation";
            const isActive = node.status === "active";

            return (
              <div key={node.id} className="relative flex items-start gap-4">
                {/* Vertical connector */}
                {!isLast && (
                  <div className="absolute left-[15px] top-[34px] bottom-0 w-px bg-border" />
                )}

                {/* Node */}
                <div className="relative z-10 shrink-0">
                  <div
                    className={cn(
                      "w-[30px] h-[30px] rounded-lg flex items-center justify-center transition-all",
                      isEscalation
                        ? "bg-red-500/10 border border-red-300 dark:border-red-800"
                        : isActive
                          ? "bg-foreground text-background shadow-sm"
                          : "bg-muted border border-border"
                    )}
                  >
                    <svg
                      className={cn(
                        "w-3.5 h-3.5",
                        isEscalation
                          ? "text-red-500"
                          : isActive
                            ? "text-background"
                            : "text-muted-foreground"
                      )}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={1.5}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
                    </svg>
                  </div>
                </div>

                {/* Content */}
                <div className={cn("flex-1 min-w-0", isLast ? "pb-0" : "pb-5")}>
                  <div className="flex items-center gap-2 flex-wrap mt-1">
                    <span className={cn(
                      "text-[13px] font-medium",
                      isActive ? "text-foreground" : "text-muted-foreground"
                    )}>
                      {node.label}
                    </span>
                    {node.type === "tool" && (
                      <span
                        className={cn(
                          "text-[9px] px-1.5 py-0.5 rounded-full font-medium",
                          node.sublabel === "success"
                            ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                            : "bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400"
                        )}
                      >
                        {node.sublabel === "success" ? "200 OK" : "ERROR"}
                      </span>
                    )}
                    {isActive && !isEscalation && (
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-foreground/40" />
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-foreground" />
                      </span>
                    )}
                  </div>
                  {node.sublabel && node.type !== "tool" && (
                    <p className="text-[11px] text-muted-foreground mt-0.5 truncate font-mono">
                      {node.sublabel}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="text-xs text-muted-foreground w-24 shrink-0">{label}</span>
      <div>{children}</div>
    </div>
  );
}

function TurnTimeline({ turns }: { turns: AgentTurnRecord[] }) {
  if (!turns.length) return null;
  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <div className="px-5 py-3.5 border-b bg-muted/20">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Conversation turns (agent changes)
          <Badge variant="secondary" className="text-[10px] ml-1">{turns.length} turn{turns.length !== 1 ? "s" : ""}</Badge>
        </h3>
      </div>
      <div className="divide-y divide-border">
        {turns.map((turn, idx) => (
          <div key={idx} className="p-4">
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <span className="text-[11px] text-muted-foreground font-mono">Turn {idx + 1}</span>
              <Badge className="text-xs">{turn.agent}</Badge>
              {turn.intent && (
                <span className="text-xs text-muted-foreground truncate max-w-[200px]" title={turn.intent}>
                  {turn.intent}
                </span>
              )}
              {turn.workflow_step && (
                <code className="text-[10px] bg-muted px-1.5 py-0.5 rounded">{turn.workflow_step}</code>
              )}
            </div>
            {(turn.tool_traces?.length ?? 0) > 0 && (
              <div className="mt-2 space-y-1.5">
                {turn.tool_traces.map((t, i) => {
                  const ok =
                    t.output &&
                    typeof t.output === "object" &&
                    "success" in t.output &&
                    (t.output as Record<string, unknown>).success === true;
                  return (
                    <div key={i} className="flex items-center gap-2 text-[11px]">
                      <code className="font-mono text-foreground">{t.name}</code>
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded-full font-medium",
                          ok ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300" : "bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400"
                        )}
                      >
                        {ok ? "OK" : "ERROR"}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
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
  const decisionEntries = Object.entries(internalData).filter(([k]) => k !== "tool_traces");
  const turnHistory = state.agent_turn_history || [];

  return (
    <ScrollArea className="h-full">
      <div className="p-6 max-w-3xl mx-auto space-y-6">
        {/* Per-turn timeline when agent changed (e.g. wismo → refund) */}
        <TurnTimeline turns={turnHistory} />

        {/* Real data-driven execution flow graph */}
        <WorkflowNodeGraph state={state} />

        {/* Session overview card */}
        <div className="rounded-lg border bg-card p-5">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Session Overview
          </h3>
          <div className="divide-y divide-border/50">
            {state.intent && (
              <InfoRow label="Intent">
                <Badge variant="secondary" className="text-xs">{state.intent}</Badge>
              </InfoRow>
            )}
            {state.routed_agent && (
              <InfoRow label="Agent">
                <Badge className="text-xs">{state.routed_agent}</Badge>
              </InfoRow>
            )}
            {state.current_workflow && (
              <InfoRow label="Workflow">
                <Badge variant="outline" className="text-xs">{state.current_workflow}</Badge>
              </InfoRow>
            )}
            {state.workflow_step && (
              <InfoRow label="Step">
                <code className="text-xs bg-muted px-2 py-0.5 rounded-md font-mono">{state.workflow_step}</code>
              </InfoRow>
            )}
            {state.is_escalated && (
              <InfoRow label="Status">
                <Badge variant="destructive" className="text-xs">Escalated</Badge>
              </InfoRow>
            )}
          </div>
        </div>

        {/* Agent decisions */}
        {decisionEntries.length > 0 && (
          <div className="rounded-lg border bg-card p-5">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Agent Decisions
            </h3>
            <div className="space-y-2">
              {decisionEntries.map(([key, value]) => (
                <div key={key} className="flex items-start gap-3 py-1 group">
                  <code className="text-[11px] text-muted-foreground font-mono bg-muted px-1.5 py-0.5 rounded shrink-0">{key}</code>
                  <span className="text-xs text-foreground break-all leading-relaxed">
                    {typeof value === "object" ? JSON.stringify(value, null, 0) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tool calls timeline (all turns when agent_turn_history exists) */}
        <div>
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
            </svg>
            Tool Call Details
            {(turnHistory.length > 0
              ? turnHistory.flatMap((t) => t.tool_traces || []).length
              : traces.length) > 0 && (
              <Badge variant="secondary" className="text-[10px] ml-1">
                {turnHistory.length > 0
                  ? turnHistory.flatMap((t) => t.tool_traces || []).length
                  : traces.length}
              </Badge>
            )}
          </h3>

          {(turnHistory.length > 0 ? turnHistory.flatMap((t) => t.tool_traces || []).length : traces.length) === 0 ? (
            <div className="text-center py-8 text-xs text-muted-foreground">
              No tool calls recorded in this session.
            </div>
          ) : (
            <div className="space-y-3">
              {(turnHistory.length > 0
                ? turnHistory.flatMap((turn, turnIdx) =>
                    (turn.tool_traces || []).map((trace, i) => ({
                      trace,
                      turnAgent: turn.agent,
                      turnIdx: turnIdx + 1,
                      key: `turn-${turnIdx}-tool-${i}`,
                    }))
                  )
                : traces.map((trace, i) => ({ trace, turnAgent: null, turnIdx: null, key: `tool-${i}` }))
              ).map(({ trace, turnAgent, turnIdx, key }) => {
                const isSuccess =
                  trace.output &&
                  typeof trace.output === "object" &&
                  "success" in trace.output &&
                  (trace.output as Record<string, unknown>).success === true;

                return (
                  <div key={key} className="rounded-lg border bg-card overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-2.5 bg-muted/20 border-b">
                      <div className="flex items-center gap-2">
                        <code className="text-xs font-semibold font-mono text-foreground">
                          {trace.name}
                        </code>
                        {turnAgent != null && (
                          <Badge variant="outline" className="text-[9px] font-normal">
                            Turn {turnIdx} · {turnAgent}
                          </Badge>
                        )}
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
                    <div className="p-4 grid grid-cols-1 gap-2">
                      <details className="group">
                        <summary className="text-[11px] font-medium text-muted-foreground cursor-pointer hover:text-foreground transition-colors flex items-center gap-1.5">
                          <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                          </svg>
                          Input
                        </summary>
                        <pre className="mt-2 bg-muted/50 border rounded-md p-3 overflow-x-auto text-[11px] leading-4 font-mono">
                          {JSON.stringify(trace.inputs, null, 2)}
                        </pre>
                      </details>
                      <details className="group">
                        <summary className="text-[11px] font-medium text-muted-foreground cursor-pointer hover:text-foreground transition-colors flex items-center gap-1.5">
                          <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                          </svg>
                          Output
                        </summary>
                        <pre className="mt-2 bg-muted/50 border rounded-md p-3 overflow-x-auto text-[11px] leading-4 font-mono">
                          {JSON.stringify(trace.output, null, 2)}
                        </pre>
                      </details>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </ScrollArea>
  );
}
