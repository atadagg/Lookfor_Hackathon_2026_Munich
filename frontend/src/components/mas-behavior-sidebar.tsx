"use client";

import { useState, useEffect, useCallback } from "react";
import { X, Wand2, RefreshCw, ChevronDown, ChevronRight, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import {
  fetchMASBehavior,
  interpretMASBehavior,
  updateMASBehavior,
  type MASConfig,
  type MASInterpretResult,
} from "@/lib/api";

interface MASBehaviorSidebarProps {
  onClose: () => void;
}

export function MASBehaviorSidebar({ onClose }: MASBehaviorSidebarProps) {
  const [config, setConfig] = useState<MASConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [prompt, setPrompt] = useState("");
  const [interpreting, setInterpreting] = useState(false);
  const [lastResult, setLastResult] = useState<MASInterpretResult | null>(null);
  const [showGlobalPolicies, setShowGlobalPolicies] = useState(true);
  const [showAgentPolicies, setShowAgentPolicies] = useState(true);
  const [showOverrides, setShowOverrides] = useState(true);
  const [removing, setRemoving] = useState<string | null>(null);

  const loadConfig = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchMASBehavior();
      setConfig(data);
    } catch (e) {
      console.error("Failed to load MAS config:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  const handleInterpret = async () => {
    const text = prompt.trim();
    if (!text) return;
    setInterpreting(true);
    setLastResult(null);
    try {
      const result = await interpretMASBehavior({ prompt: text });
      setLastResult(result);
      setConfig(result.config);
      if (!result.error) setPrompt("");
    } catch (e) {
      setLastResult({
        config: config || {},
        applied: {},
        error: e instanceof Error ? e.message : "Interpret failed",
      });
    } finally {
      setInterpreting(false);
    }
  };

  const removeGlobalPolicy = async (index: number) => {
    const key = `global-${index}`;
    setRemoving(key);
    try {
      await updateMASBehavior({ remove_prompt_policy_index: index });
      await loadConfig();
    } catch (e) {
      console.error("Failed to remove policy:", e);
    } finally {
      setRemoving(null);
    }
  };

  const removeAgentPolicy = async (agent: string, index: number) => {
    const key = `agent-${agent}-${index}`;
    setRemoving(key);
    try {
      await updateMASBehavior({ remove_agent_policy: { agent, index } });
      await loadConfig();
    } catch (e) {
      console.error("Failed to remove agent policy:", e);
    } finally {
      setRemoving(null);
    }
  };

  const removeOverride = async (agent: string, trigger: string) => {
    const key = `override-${agent}-${trigger}`;
    setRemoving(key);
    try {
      await updateMASBehavior({ remove_behavior_override: { agent, trigger } });
      await loadConfig();
    } catch (e) {
      console.error("Failed to remove override:", e);
    } finally {
      setRemoving(null);
    }
  };

  const globalPolicies = config?.prompt_policies ?? [];
  const agentPolicies = config?.agent_prompt_policies ?? {};
  const overrides = config?.behavior_overrides ?? {};
  const hasAgentPolicies = Object.keys(agentPolicies).length > 0 && Object.values(agentPolicies).some((arr) => arr?.length > 0);
  const hasOverrides = Object.keys(overrides).length > 0 && Object.values(overrides).some((arr) => arr?.length > 0);

  return (
    <div className="fixed inset-y-0 right-0 w-[480px] bg-background border-l shadow-2xl z-50 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20 shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
              <Wand2 className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold">MAS Behavior</h2>
              <p className="text-xs text-muted-foreground">Update agent behavior with natural language</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="shrink-0">
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Natural language input */}
        <div className="mt-3 space-y-2">
          <textarea
            placeholder="e.g. If a customer wants to update their order address, do not update it directly. Mark as NEEDS_ATTENTION and escalate."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="w-full min-h-[80px] px-3 py-2 text-sm border rounded-md bg-background resize-y focus:outline-none focus:ring-2 focus:ring-ring"
            disabled={interpreting}
          />
          <div className="flex gap-2">
            <Button
              onClick={handleInterpret}
              disabled={!prompt.trim() || interpreting}
              size="sm"
              className="flex-1 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600"
            >
              <Wand2 className={cn("w-3.5 h-3.5 mr-2", interpreting && "animate-pulse")} />
              {interpreting ? "Interpreting..." : "Interpret & Apply"}
            </Button>
            <Button variant="outline" size="sm" onClick={loadConfig} disabled={loading}>
              <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
            </Button>
          </div>
        </div>

        {/* Last result */}
        {lastResult && (
          <div className={cn(
            "mt-3 px-3 py-2 rounded-md text-xs",
            lastResult.error ? "bg-destructive/10 text-destructive" : "bg-green-500/10 text-green-800 dark:text-green-300"
          )}>
            {lastResult.error ? (
              <span>{lastResult.error}</span>
            ) : (
              <span>
                {lastResult.applied.removed && "Removed. "}
                {lastResult.applied.instruction && "Added prompt policy. "}
                {lastResult.applied.behavior_override && "Added behavior override."}
                {!lastResult.applied.instruction && !lastResult.applied.behavior_override && !lastResult.applied.removed && "No changes."}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Config summary */}
      <div className="flex-1 overflow-y-auto">
        <ScrollArea className="h-full">
          <div className="p-6 space-y-4">
            {loading ? (
              <p className="text-sm text-muted-foreground">Loading config...</p>
            ) : (
              <>
                {/* Global policies */}
                <div className="space-y-2">
                  <button
                    onClick={() => setShowGlobalPolicies(!showGlobalPolicies)}
                    className="flex items-center gap-2 w-full text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider"
                  >
                    {showGlobalPolicies ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    Global policies ({globalPolicies.length})
                  </button>
                  {showGlobalPolicies && (
                    <ul className="space-y-1.5 pl-4 text-sm">
                      {globalPolicies.length === 0 ? (
                        <li className="text-muted-foreground">None</li>
                      ) : (
                        globalPolicies.map((p, i) => (
                          <li key={i} className="flex items-start gap-2 border-l-2 border-amber-200 dark:border-amber-800 pl-2 py-1 text-muted-foreground group">
                            <span className="flex-1 min-w-0">{p}</span>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 text-destructive hover:text-destructive"
                              onClick={() => removeGlobalPolicy(i)}
                              disabled={removing === `global-${i}`}
                              title="Remove this policy"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </li>
                        ))
                      )}
                    </ul>
                  )}
                </div>

                {/* Per-agent policies */}
                <div className="space-y-2">
                  <button
                    onClick={() => setShowAgentPolicies(!showAgentPolicies)}
                    className="flex items-center gap-2 w-full text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider"
                  >
                    {showAgentPolicies ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    Per-agent policies
                  </button>
                  {showAgentPolicies && (
                    <div className="space-y-2 pl-4">
                      {!hasAgentPolicies ? (
                        <p className="text-sm text-muted-foreground">None</p>
                      ) : (
                        Object.entries(agentPolicies).map(([agent, list]) =>
                          list?.length ? (
                            <div key={agent}>
                              <p className="text-xs font-medium text-muted-foreground capitalize">{agent.replace("_", " ")}</p>
                              <ul className="mt-1 space-y-1 text-sm">
                                {list.map((p, i) => (
                                  <li key={`${agent}-${i}`} className="flex items-start gap-2 border-l-2 border-orange-200 dark:border-orange-800 pl-2 py-1 text-muted-foreground group">
                                    <span className="flex-1 min-w-0">{p}</span>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 text-destructive hover:text-destructive"
                                      onClick={() => removeAgentPolicy(agent, i)}
                                      disabled={removing === `agent-${agent}-${i}`}
                                      title="Remove this policy"
                                    >
                                      <Trash2 className="w-3 h-3" />
                                    </Button>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ) : null
                        )
                      )}
                    </div>
                  )}
                </div>

                {/* Behavior overrides */}
                <div className="space-y-2">
                  <button
                    onClick={() => setShowOverrides(!showOverrides)}
                    className="flex items-center gap-2 w-full text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider"
                  >
                    {showOverrides ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    Behavior overrides
                  </button>
                  {showOverrides && (
                    <div className="space-y-2 pl-4 text-sm">
                      {!hasOverrides ? (
                        <p className="text-muted-foreground">None</p>
                      ) : (
                        Object.entries(overrides).map(([agent, rules]) =>
                          rules?.length ? (
                            <div key={agent}>
                              <p className="text-xs font-medium text-muted-foreground capitalize">{agent.replace("_", " ")}</p>
                              <ul className="mt-1 space-y-1">
                                {rules.map((r, i) => {
                                  const trigger = typeof r === "object" && r !== null && "trigger" in r ? (r as { trigger: string }).trigger : "";
                                  return (
                                    <li key={`${agent}-${i}`} className="flex items-center gap-2 bg-muted/50 rounded px-2 py-1.5 font-mono text-xs group">
                                      <span className="flex-1">
                                        {r.trigger} → {r.action} {r.tag ? `(tag: ${r.tag})` : ""}
                                      </span>
                                      {trigger && (
                                        <Button
                                          variant="ghost"
                                          size="icon"
                                          className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 text-destructive hover:text-destructive"
                                          onClick={() => removeOverride(agent, trigger)}
                                          disabled={removing === `override-${agent}-${trigger}`}
                                          title="Remove this override"
                                        >
                                          <Trash2 className="w-3 h-3" />
                                        </Button>
                                      )}
                                    </li>
                                  );
                                })}
                              </ul>
                            </div>
                          ) : null
                        )
                      )}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </ScrollArea>
      </div>

      <div className="px-6 py-3 border-t bg-muted/30 shrink-0">
        <p className="text-xs text-muted-foreground text-center">
          Describe how agents should behave in plain language. The interpreter adds prompt policies and/or behavior overrides.
        </p>
      </div>
    </div>
  );
}
