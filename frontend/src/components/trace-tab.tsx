"use client";

import { AgentTurnRecord, ThreadState, ToolTrace } from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useMemo } from "react";

interface TraceTabProps {
  state: ThreadState | null;
}

/* ── Build real graph nodes from actual DB state ── */

interface GraphNode {
  id: string;
  label: string;
  sublabel?: string;
  status: "completed" | "active" | "pending" | "error";
  type: "start" | "route" | "tool" | "decision" | "llm" | "end" | "escalation";
  metadata?: Record<string, unknown>;
  timestamp?: string;
  duration_ms?: number;
}

interface ExecutionMetrics {
  total_tools_called: number;
  successful_tools: number;
  failed_tools: number;
  total_turns: number;
  agents_involved: string[];
  total_messages: number;
  has_escalation: boolean;
  workflow_steps: string[];
  execution_path: string[];
}

function calculateMetrics(state: ThreadState): ExecutionMetrics {
  const history = state.agent_turn_history || [];
  const traces = state.internal_data?.tool_traces || [];
  
  const allTraces = history.length > 0 
    ? history.flatMap(t => t.tool_traces || [])
    : traces;
  
  const successfulTools = allTraces.filter(t => 
    t.output && typeof t.output === 'object' && 'success' in t.output && t.output.success === true
  ).length;
  
  const agents = history.length > 0
    ? Array.from(new Set(history.map(t => t.agent)))
    : state.routed_agent ? [state.routed_agent] : [];
  
  const workflowSteps = history.length > 0
    ? history.map(t => t.workflow_step).filter(Boolean) as string[]
    : state.workflow_step ? [state.workflow_step] : [];
  
  const executionPath = history.length > 0
    ? history.flatMap(t => [
        `Route → ${t.agent}`,
        ...(t.tool_traces || []).map(trace => `Tool → ${trace.name}`)
      ])
    : [
        state.intent ? `Intent → ${state.intent}` : '',
        state.routed_agent ? `Route → ${state.routed_agent}` : '',
        ...allTraces.map(t => `Tool → ${t.name}`)
      ].filter(Boolean);

  return {
    total_tools_called: allTraces.length,
    successful_tools: successfulTools,
    failed_tools: allTraces.length - successfulTools,
    total_turns: history.length || 1,
    agents_involved: agents,
    total_messages: state.messages?.length || 0,
    has_escalation: state.is_escalated || false,
    workflow_steps: workflowSteps,
    execution_path: executionPath,
  };
}

function buildGraphNodes(state: ThreadState): GraphNode[] {
  const nodes: GraphNode[] = [];
  const history = state.agent_turn_history || [];
  const internalData = state.internal_data || {};

  // Start node
  nodes.push({
    id: "start",
    label: "Request Received",
    sublabel: state.intent || "Analyzing intent...",
    status: "completed",
    type: "start",
  });

  // When we have per-turn history, show each turn (route + tools) so agent changes are visible
  if (history.length > 0) {
    history.forEach((turn, turnIdx) => {
      const isLastTurn = turnIdx === history.length - 1;
      
      // LLM classification for this turn
      if (turn.intent) {
        nodes.push({
          id: `llm-classify-${turnIdx}`,
          label: "LLM Classification",
          sublabel: turn.intent,
          status: "completed",
          type: "llm",
        });
      }
      
      // Route to agent
      nodes.push({
        id: `route-${turnIdx}`,
        label: "Routed to Agent",
        sublabel: turn.agent,
        status: "completed",
        type: "route",
        metadata: {
          turn: turnIdx + 1,
          workflow: turn.current_workflow,
        },
      });
      
      // Tool calls
      (turn.tool_traces || []).forEach((trace, i) => {
        const isSuccess =
          trace.output &&
          typeof trace.output === "object" &&
          "success" in trace.output &&
          (trace.output as Record<string, unknown>).success === true;
        
        const errorMsg = !isSuccess && trace.output && typeof trace.output === 'object' && 'error' in trace.output
          ? String(trace.output.error)
          : undefined;
        
        nodes.push({
          id: `turn-${turnIdx}-tool-${i}`,
          label: trace.name,
          sublabel: isSuccess ? "success" : errorMsg || "failed",
          status: isSuccess ? "completed" : "error",
          type: "tool",
          metadata: {
            inputs: trace.inputs,
            output: trace.output,
          },
        });
      });
      
      // Workflow step decision
      if (turn.workflow_step) {
        nodes.push({
          id: `decision-${turnIdx}`,
          label: "Workflow Decision",
          sublabel: turn.workflow_step.replace(/_/g, " "),
          status: "completed",
          type: "decision",
        });
      }
      
      // Final state
      if (isLastTurn) {
        if (state.is_escalated) {
          nodes.push({
            id: "escalated",
            label: "Escalated to Human",
            sublabel: state.escalation_summary?.reason ? String(state.escalation_summary.reason) : "Manual review required",
            status: "active",
            type: "escalation",
            metadata: state.escalation_summary,
          });
        } else {
          // Get last assistant message
          const lastAssistantMsg = state.messages
            ?.slice()
            .reverse()
            .find(m => m.role === "assistant");
          const msgPreview = lastAssistantMsg?.content 
            ? (lastAssistantMsg.content.substring(0, 60) + "...") 
            : "Sent to customer";
          
          nodes.push({
            id: "responded",
            label: "Response Generated",
            sublabel: msgPreview,
            status: "active",
            type: "end",
          });
        }
      }
    });
    
    return nodes;
  }

  // Fallback: single-agent view (no agent_turn_history)
  const traces: ToolTrace[] = state.internal_data?.tool_traces || [];
  
  if (state.routed_agent) {
    nodes.push({
      id: "route",
      label: "Routed to Agent",
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
    
    const errorMsg = !isSuccess && trace.output && typeof trace.output === 'object' && 'error' in trace.output
      ? String(trace.output.error)
      : undefined;
    
    nodes.push({
      id: `tool-${i}`,
      label: trace.name,
      sublabel: isSuccess ? "success" : errorMsg || "failed",
      status: isSuccess ? "completed" : "error",
      type: "tool",
      metadata: {
        inputs: trace.inputs,
        output: trace.output,
      },
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
      label: "Escalated to Human",
      sublabel: state.escalation_summary?.reason ? String(state.escalation_summary.reason) : "Manual review required",
      status: "active",
      type: "escalation",
      metadata: state.escalation_summary,
    });
  } else if (state.workflow_step) {
    nodes.push({
      id: "responded",
      label: "Response Generated",
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
  llm: "M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z",
  end: "M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  escalation: "M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z",
};

function MetricsCard({ metrics }: { metrics: ExecutionMetrics }) {
  const successRate = metrics.total_tools_called > 0 
    ? Math.round((metrics.successful_tools / metrics.total_tools_called) * 100)
    : 0;
  
  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <div className="px-5 py-3.5 border-b bg-muted/20">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Execution Metrics
        </h3>
      </div>
      
      <div className="p-5 grid grid-cols-2 sm:grid-cols-4 gap-4">
        {/* Tool Calls */}
        <div className="flex flex-col gap-1">
          <div className="text-2xl font-bold text-foreground">{metrics.total_tools_called}</div>
          <div className="text-xs text-muted-foreground">Tool Calls</div>
          <div className="flex items-center gap-1 mt-1">
            <div className="h-1 flex-1 bg-muted rounded-full overflow-hidden">
              <div 
                className="h-full bg-emerald-500" 
                style={{ width: `${successRate}%` }}
              />
            </div>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
              {successRate}%
            </span>
          </div>
        </div>
        
        {/* Conversation Turns */}
        <div className="flex flex-col gap-1">
          <div className="text-2xl font-bold text-foreground">{metrics.total_turns}</div>
          <div className="text-xs text-muted-foreground">
            {metrics.total_turns === 1 ? "Turn" : "Turns"}
          </div>
          {metrics.agents_involved.length > 1 && (
            <div className="text-[10px] text-amber-600 dark:text-amber-400 mt-1">
              Multi-agent
            </div>
          )}
        </div>
        
        {/* Messages */}
        <div className="flex flex-col gap-1">
          <div className="text-2xl font-bold text-foreground">{metrics.total_messages}</div>
          <div className="text-xs text-muted-foreground">Messages</div>
          <div className="text-[10px] text-muted-foreground mt-1">
            {Math.floor(metrics.total_messages / 2)} exchanges
          </div>
        </div>
        
        {/* Status */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            {metrics.has_escalation ? (
              <>
                <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                <span className="text-sm font-semibold text-amber-600 dark:text-amber-400">
                  Escalated
                </span>
              </>
            ) : (
              <>
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                  Active
                </span>
              </>
            )}
          </div>
          <div className="text-xs text-muted-foreground">Status</div>
        </div>
      </div>
      
      {/* Agents Involved */}
      {metrics.agents_involved.length > 0 && (
        <div className="px-5 pb-4">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-muted-foreground">Agents:</span>
            {metrics.agents_involved.map((agent, i) => (
              <Badge key={i} variant={i === metrics.agents_involved.length - 1 ? "default" : "secondary"} className="text-xs">
                {agent}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

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
            const isError = node.status === "error";
            const isActive = node.status === "active";

            return (
              <div key={node.id} className="relative flex items-start gap-4">
                {/* Vertical connector */}
                {!isLast && (
                  <div 
                    className={cn(
                      "absolute left-[15px] top-[34px] bottom-0 w-px",
                      isError ? "bg-red-300 dark:bg-red-800" : "bg-border"
                    )} 
                  />
                )}

                {/* Node */}
                <div className="relative z-10 shrink-0">
                  <div
                    className={cn(
                      "w-[30px] h-[30px] rounded-lg flex items-center justify-center transition-all",
                      isEscalation
                        ? "bg-amber-500/10 border border-amber-300 dark:border-amber-800"
                        : isError
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
                          ? "text-amber-500"
                          : isError
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
                          !isError
                            ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                            : "bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400"
                        )}
                      >
                        {!isError ? "200 OK" : "ERROR"}
                      </span>
                    )}
                    {node.type === "llm" && (
                      <Badge variant="outline" className="text-[9px]">
                        GPT-4o-mini
                      </Badge>
                    )}
                    {isActive && !isEscalation && (
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-foreground/40" />
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-foreground" />
                      </span>
                    )}
                  </div>
                  {node.sublabel && (
                    <p className={cn(
                      "text-[11px] mt-0.5 font-mono",
                      isError ? "text-red-600 dark:text-red-400" : "text-muted-foreground",
                      node.type === "end" && !isError ? "line-clamp-2" : "truncate"
                    )}>
                      {node.sublabel}
                    </p>
                  )}
                  
                  {/* Show metadata for tools */}
                  {node.metadata && node.type === "tool" && (
                    <details className="mt-2 group/details">
                      <summary className="text-[10px] text-muted-foreground cursor-pointer hover:text-foreground transition-colors flex items-center gap-1">
                        <svg className="w-3 h-3 transition-transform group-open/details:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                        View I/O
                      </summary>
                      <div className="mt-2 space-y-2">
                        <div>
                          <div className="text-[10px] text-blue-600 dark:text-blue-400 font-medium mb-1">Input:</div>
                          <pre className="bg-muted/50 border rounded-md p-2 overflow-x-auto text-[10px] leading-4 font-mono max-h-32">
                            {JSON.stringify(node.metadata.inputs, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <div className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium mb-1">Output:</div>
                          <pre className="bg-muted/50 border rounded-md p-2 overflow-x-auto text-[10px] leading-4 font-mono max-h-32">
                            {JSON.stringify(node.metadata.output, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </details>
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
      <span className="text-xs text-muted-foreground w-32 shrink-0">{label}</span>
      <div className="flex-1 min-w-0">{children}</div>
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
          Conversation Turns (Agent Handoffs)
          <Badge variant="secondary" className="text-[10px] ml-1">{turns.length} turn{turns.length !== 1 ? "s" : ""}</Badge>
        </h3>
      </div>
      <div className="divide-y divide-border">
        {turns.map((turn, idx) => {
          const toolCount = turn.tool_traces?.length || 0;
          const successCount = (turn.tool_traces || []).filter(t => 
            t.output && typeof t.output === 'object' && 'success' in t.output && t.output.success === true
          ).length;
          
          return (
            <div key={idx} className="p-4 hover:bg-muted/20 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[11px] text-muted-foreground font-mono bg-muted px-1.5 py-0.5 rounded">
                    Turn {idx + 1}
                  </span>
                  <Badge className="text-xs">{turn.agent}</Badge>
                  {turn.intent && (
                    <span className="text-xs text-muted-foreground truncate max-w-[200px]" title={turn.intent}>
                      {`&quot;${turn.intent}&quot;`}
                    </span>
                  )}
                </div>
                {toolCount > 0 && (
                  <div className="flex items-center gap-1">
                    <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
                      {successCount}/{toolCount} OK
                    </span>
                  </div>
                )}
              </div>
              
              {turn.workflow_step && (
                <div className="mb-2">
                  <code className="text-[10px] bg-muted/50 px-1.5 py-0.5 rounded text-foreground">
                    {turn.workflow_step}
                  </code>
                </div>
              )}
              
              {toolCount > 0 && (
                <div className="mt-2 space-y-1.5">
                  {turn.tool_traces.map((t, i) => {
                    const ok =
                      t.output &&
                      typeof t.output === "object" &&
                      "success" in t.output &&
                      (t.output as Record<string, unknown>).success === true;
                    
                    return (
                      <div key={i} className="flex items-center gap-2 text-[11px]">
                        <span className="text-muted-foreground">{i + 1}.</span>
                        <code className="font-mono text-foreground flex-1">{t.name}</code>
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded-full font-medium text-[9px]",
                            ok 
                              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300" 
                              : "bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400"
                          )}
                        >
                          {ok ? "OK" : "ERR"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ExecutionPathTimeline({ metrics }: { metrics: ExecutionMetrics }) {
  if (metrics.execution_path.length === 0) return null;
  
  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <div className="px-5 py-3.5 border-b bg-muted/20">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
          Execution Path
        </h3>
      </div>
      <div className="p-4">
        <div className="flex items-center gap-2 flex-wrap">
          {metrics.execution_path.map((step, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground font-mono bg-muted px-2 py-1 rounded">
                {step}
              </span>
              {i < metrics.execution_path.length - 1 && (
                <svg className="w-3 h-3 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PerformanceTimeline({ state }: { state: ThreadState }) {
  const turnHistory = state.agent_turn_history || [];
  const traces = state.internal_data?.tool_traces || [];
  
  const allTraces = turnHistory.length > 0
    ? turnHistory.flatMap((turn, turnIdx) =>
        (turn.tool_traces || []).map((trace, i) => ({
          trace,
          turnAgent: turn.agent,
          turnIdx: turnIdx + 1,
        }))
      )
    : traces.map((trace, i) => ({ trace, turnAgent: null, turnIdx: null }));
  
  // Filter traces with duration
  const tracesWithDuration = allTraces.filter(({ trace }) => 
    trace.duration_ms !== undefined && trace.duration_ms > 0
  );
  
  if (tracesWithDuration.length === 0) return null;
  
  const maxDuration = Math.max(...tracesWithDuration.map(({ trace }) => trace.duration_ms || 0));
  const totalDuration = tracesWithDuration.reduce((sum, { trace }) => sum + (trace.duration_ms || 0), 0);
  
  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <div className="px-5 py-3.5 border-b bg-muted/20">
        <h3 className="text-sm font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />
            </svg>
            Performance Timeline
          </div>
          <span className="text-[10px] font-normal text-muted-foreground">
            Total: <span className="font-mono font-medium">{totalDuration.toFixed(0)}ms</span>
          </span>
        </h3>
      </div>
      <div className="p-4 space-y-2">
        {tracesWithDuration.map(({ trace, turnAgent, turnIdx }, i) => {
          const duration = trace.duration_ms || 0;
          const percentage = (duration / maxDuration) * 100;
          const isSuccess = trace.output && typeof trace.output === 'object' && 
            'success' in trace.output && trace.output.success === true;
          
          return (
            <div key={i} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <code className="font-mono text-foreground truncate">{trace.name}</code>
                  {turnAgent && (
                    <Badge variant="outline" className="text-[9px] shrink-0">
                      {turnAgent}
                    </Badge>
                  )}
                </div>
                <span className="font-mono text-muted-foreground ml-2 shrink-0">
                  {duration < 1000 ? `${duration.toFixed(0)}ms` : `${(duration / 1000).toFixed(2)}s`}
                </span>
              </div>
              <div className="h-6 bg-muted/30 rounded-md overflow-hidden relative">
                <div 
                  className={cn(
                    "h-full transition-all duration-500 rounded-md flex items-center justify-end pr-2",
                    isSuccess
                      ? "bg-gradient-to-r from-emerald-500/80 to-emerald-600/80"
                      : "bg-gradient-to-r from-red-500/80 to-red-600/80"
                  )}
                  style={{ width: `${percentage}%` }}
                >
                  <span className="text-[10px] font-medium text-white">
                    {percentage.toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SessionOverviewCard({ state }: { state: ThreadState }) {
  const internalData = state.internal_data || {};
  const decisionEntries = Object.entries(internalData).filter(([k]) => 
    k !== "tool_traces" && k !== "photos_received" && k !== "photo_urls"
  );
  
  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <div className="px-5 py-3.5 border-b bg-muted/20">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Session State
        </h3>
      </div>
      <div className="p-4 space-y-3">
        {/* Core routing info */}
        <div className="space-y-1.5">
          {state.intent && (
            <InfoRow label="Intent">
              <Badge variant="secondary" className="text-xs">{state.intent}</Badge>
            </InfoRow>
          )}
          {state.routed_agent && (
            <InfoRow label="Current Agent">
              <Badge className="text-xs">{state.routed_agent}</Badge>
            </InfoRow>
          )}
          {state.current_workflow && (
            <InfoRow label="Workflow">
              <Badge variant="outline" className="text-xs">{state.current_workflow}</Badge>
            </InfoRow>
          )}
          {state.workflow_step && (
            <InfoRow label="Workflow Step">
              <code className="text-xs bg-muted px-2 py-0.5 rounded-md font-mono">{state.workflow_step}</code>
            </InfoRow>
          )}
          {state.is_escalated && (
            <InfoRow label="Escalation">
              <div className="flex items-center gap-2">
                <Badge variant="destructive" className="text-xs">Escalated</Badge>
                {(state.escalation_summary?.reason && typeof state.escalation_summary.reason === 'string') ? (
                  <span className="text-xs text-muted-foreground">
                    Reason: {state.escalation_summary.reason}
                  </span>
                ) : null}
              </div>
            </InfoRow>
          )}
        </div>
        
        {/* Customer info */}
        {state.customer_info && Object.keys(state.customer_info).length > 0 && (
          <div className="border-t pt-3">
            <div className="text-xs font-medium text-muted-foreground mb-2">Customer Info</div>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(state.customer_info).map(([key, value]) => (
                <div key={key} className="text-xs">
                  <span className="text-muted-foreground">{key}:</span>{" "}
                  <span className="font-mono">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Agent decisions */}
        {decisionEntries.length > 0 && (
          <div className="border-t pt-3">
            <div className="text-xs font-medium text-muted-foreground mb-2">Agent Decisions</div>
            <div className="space-y-1.5">
              {decisionEntries.map(([key, value]) => (
                <div key={key} className="flex items-start gap-2 group">
                  <code className="text-[10px] text-muted-foreground font-mono bg-muted px-1.5 py-0.5 rounded shrink-0">
                    {key}
                  </code>
                  <span className="text-xs text-foreground break-all leading-relaxed">
                    {typeof value === "object" ? JSON.stringify(value, null, 0) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Slots */}
        {state.slots && Object.keys(state.slots).length > 0 && (
          <div className="border-t pt-3">
            <div className="text-xs font-medium text-muted-foreground mb-2">Extracted Slots</div>
            <div className="space-y-1.5">
              {Object.entries(state.slots).map(([key, value]) => (
                <div key={key} className="flex items-start gap-2">
                  <code className="text-[10px] text-blue-600 dark:text-blue-400 font-mono bg-blue-50 dark:bg-blue-950 px-1.5 py-0.5 rounded shrink-0">
                    {key}
                  </code>
                  <span className="text-xs text-foreground break-all">
                    {typeof value === "object" ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ToolCallsDetailed({ state }: { state: ThreadState }) {
  const turnHistory = state.agent_turn_history || [];
  const traces = state.internal_data?.tool_traces || [];
  
  const allTraces = turnHistory.length > 0
    ? turnHistory.flatMap((turn, turnIdx) =>
        (turn.tool_traces || []).map((trace, i) => ({
          trace,
          turnAgent: turn.agent,
          turnIdx: turnIdx + 1,
          key: `turn-${turnIdx}-tool-${i}`,
        }))
      )
    : traces.map((trace, i) => ({ trace, turnAgent: null, turnIdx: null, key: `tool-${i}` }));
  
  if (allTraces.length === 0) return null;
  
  // Calculate total duration
  const totalDuration = allTraces.reduce((sum, { trace }) => 
    sum + (trace.duration_ms || 0), 0
  );
  
  const avgDuration = allTraces.length > 0 ? totalDuration / allTraces.length : 0;
  
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
          </svg>
          Tool Call Details
          <Badge variant="secondary" className="text-[10px] ml-1">{allTraces.length}</Badge>
        </h3>
        {totalDuration > 0 && (
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Total: <span className="font-mono font-medium">{totalDuration.toFixed(0)}ms</span></span>
            </div>
            <div className="h-3 w-px bg-border" />
            <div>
              <span>Avg: <span className="font-mono font-medium">{avgDuration.toFixed(0)}ms</span></span>
            </div>
          </div>
        )}
      </div>

      <div className="space-y-3">
        {allTraces.map(({ trace, turnAgent, turnIdx, key }) => {
          const isSuccess =
            trace.output &&
            typeof trace.output === "object" &&
            "success" in trace.output &&
            (trace.output as Record<string, unknown>).success === true;
          
          const errorMsg = !isSuccess && trace.output && typeof trace.output === 'object' && 'error' in trace.output
            ? String(trace.output.error)
            : null;
          
          const outputData: Record<string, unknown> | null = 
            trace.output && typeof trace.output === 'object' && 'data' in trace.output && trace.output.data && typeof trace.output.data === 'object'
              ? (trace.output.data as Record<string, unknown>)
              : null;

          const duration = trace.duration_ms;
          const timestamp = trace.timestamp;
          
          return (
            <div key={key} className="rounded-lg border bg-card overflow-hidden hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between px-4 py-2.5 bg-muted/20 border-b">
                <div className="flex items-center gap-2 flex-wrap">
                  <code className="text-xs font-semibold font-mono text-foreground">
                    {trace.name}
                  </code>
                  {turnAgent != null && (
                    <Badge variant="outline" className="text-[9px] font-normal">
                      Turn {turnIdx} · {turnAgent}
                    </Badge>
                  )}
                  {duration !== undefined && (
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="font-mono font-medium">
                        {duration < 1000 ? `${duration.toFixed(0)}ms` : `${(duration / 1000).toFixed(2)}s`}
                      </span>
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {timestamp && (
                    <span className="text-[9px] text-muted-foreground font-mono">
                      {new Date(timestamp).toLocaleTimeString()}
                    </span>
                  )}
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
              </div>
              
              <div className="p-4 space-y-3">
                {/* Input Parameters */}
                <details className="group open" open>
                  <summary className="text-[11px] font-medium text-blue-600 dark:text-blue-400 cursor-pointer hover:text-blue-700 dark:hover:text-blue-300 transition-colors flex items-center gap-1.5">
                    <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                    Input Parameters
                    <Badge variant="secondary" className="text-[9px] ml-1">
                      {Object.keys(trace.inputs || {}).length} param{Object.keys(trace.inputs || {}).length !== 1 ? 's' : ''}
                    </Badge>
                  </summary>
                  <pre className="mt-2 bg-blue-50/50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-md p-3 overflow-x-auto text-[11px] leading-5 font-mono">
                    {JSON.stringify(trace.inputs, null, 2)}
                  </pre>
                </details>
                
                <details className="group">
                  <summary className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400 cursor-pointer hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors flex items-center gap-1.5">
                    <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                    Output Response
                  </summary>
                  <pre className={cn(
                    "mt-2 border rounded-md p-3 overflow-x-auto text-[11px] leading-5 font-mono",
                    isSuccess 
                      ? "bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800"
                      : "bg-red-50/50 dark:bg-red-950/20 border-red-200 dark:border-red-800"
                  )}>
                    {JSON.stringify(trace.output, null, 2)}
                  </pre>
                </details>
                
                {/* Show data preview if available */}
                {outputData && typeof outputData === 'object' && (
                  <div className="pt-2 border-t">
                    <div className="text-[10px] font-medium text-muted-foreground mb-1.5">
                      Response Data Preview:
                    </div>
                    <div className="bg-muted/30 rounded p-2 text-[10px] font-mono text-foreground">
                      <div className="space-y-0.5">
                        {Object.entries(outputData as Record<string, unknown>).slice(0, 3).map(([k, v]) => (
                          <div key={k}>
                            <span className="text-muted-foreground">{k}:</span>{" "}
                            {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                          </div>
                        ))}
                        {Object.keys(outputData as Record<string, unknown>).length > 3 && (
                          <div className="text-muted-foreground">
                            ... {Object.keys(outputData as Record<string, unknown>).length - 3} more
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Error details */}
                {errorMsg && (
                  <div className="pt-2 border-t border-red-200 dark:border-red-800">
                    <div className="flex items-start gap-2">
                      <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <div className="flex-1">
                        <div className="text-[10px] font-semibold text-red-600 dark:text-red-400 mb-1">
                          Error Details:
                        </div>
                        <p className="text-[11px] text-red-700 dark:text-red-300 leading-relaxed">
                          {errorMsg}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
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

  const metrics = calculateMetrics(state);
  const turnHistory = state.agent_turn_history || [];

  return (
    <ScrollArea className="h-full">
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        {/* Execution Metrics - LangChain style overview */}
        <MetricsCard metrics={metrics} />
        
        {/* Performance Timeline - Visual duration chart */}
        <PerformanceTimeline state={state} />
        
        {/* Execution Path - Quick visual timeline */}
        <ExecutionPathTimeline metrics={metrics} />
        
        {/* Per-turn timeline when agent changed (e.g. wismo → refund) */}
        <TurnTimeline turns={turnHistory} />

        {/* Real data-driven execution flow graph */}
        <WorkflowNodeGraph state={state} />

        {/* Session overview card with all state */}
        <SessionOverviewCard state={state} />
        
        {/* Detailed tool traces with expanded I/O */}
        <ToolCallsDetailed state={state} />
      </div>
    </ScrollArea>
  );
}
