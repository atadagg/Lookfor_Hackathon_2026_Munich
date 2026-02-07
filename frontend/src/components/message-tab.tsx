"use client";

import React from "react";
import { API_URL, ThreadDetail } from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

interface MessageTabProps {
  thread: ThreadDetail;
  customerName?: string;
}

/**
 * Parse message text and turn URLs + markdown links into clickable <a> tags.
 * Handles:  [label](url)  and  bare https://... urls
 */
function renderContent(text: string, isUser: boolean) {
  // Combined regex: markdown links first, then bare URLs
  const regex = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|(https?:\/\/[^\s)<]+)/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    // Push text before this match
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    const linkClass = cn(
      "underline underline-offset-2 break-all",
      isUser
        ? "text-blue-600 dark:text-blue-400 hover:text-blue-700"
        : "text-primary-foreground/90 hover:text-primary-foreground"
    );

    if (match[1] && match[2]) {
      // Markdown-style [label](url)
      parts.push(
        <a key={match.index} href={match[2]} target="_blank" rel="noopener noreferrer" className={linkClass}>
          {match[1]}
        </a>
      );
    } else if (match[3]) {
      // Bare URL
      parts.push(
        <a key={match.index} href={match[3]} target="_blank" rel="noopener noreferrer" className={linkClass}>
          {match[3]}
        </a>
      );
    }

    lastIndex = regex.lastIndex;
  }

  // Push remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

export function MessageTab({ thread, customerName }: MessageTabProps) {
  const displayName = customerName || "Customer";

  return (
    <ScrollArea className="h-full">
      <div className="flex flex-col gap-4 p-6 max-w-3xl mx-auto">
        {thread.messages.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-12">
            No messages in this thread
          </p>
        )}
        {thread.messages.map((msg, i) => {
          const isUser = msg.role === "user";
          const time = msg.created_at
            ? new Date(msg.created_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })
            : null;

          return (
            <div key={i} className={cn("flex gap-3", isUser ? "justify-start" : "justify-end")}>
              {/* User avatar */}
              {isUser && (
                <div className="shrink-0 w-8 h-8 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 flex items-center justify-center mt-1">
                  <svg className="w-[18px] h-[18px] text-zinc-400 dark:text-zinc-500" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v1.2c0 .7.5 1.2 1.2 1.2h16.8c.7 0 1.2-.5 1.2-1.2v-1.2c0-3.2-6.4-4.8-9.6-4.8z" />
                  </svg>
                </div>
              )}

              <div
                className={cn(
                  "max-w-[75%] rounded-2xl px-4 py-3",
                  isUser
                    ? "bg-muted rounded-tl-sm"
                    : "bg-primary text-primary-foreground rounded-tr-sm"
                )}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <span
                    className={cn(
                      "text-[11px] font-semibold uppercase tracking-wide",
                      !isUser && "text-primary-foreground/80"
                    )}
                  >
                    {isUser ? displayName : "Customer Support"}
                  </span>
                  {time && (
                    <span
                      className={cn(
                        "text-[10px]",
                        isUser ? "text-muted-foreground" : "text-primary-foreground/60"
                      )}
                    >
                      {time}
                    </span>
                  )}
                </div>
                <div
                  className={cn(
                    "text-[13px] leading-relaxed whitespace-pre-wrap",
                    isUser ? "text-foreground" : "text-primary-foreground"
                  )}
                >
                  {renderContent(msg.content, isUser)}
                </div>
                {msg.attachments && msg.attachments.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {msg.attachments.map((att, j) => {
                      const src = att.url.startsWith("http") ? att.url : `${API_URL}${att.url}`;
                      const isImage = (att.content_type || "").startsWith("image/");
                      if (isImage) {
                        return (
                          <a key={j} href={src} target="_blank" rel="noopener noreferrer" className="block">
                            <img
                              src={src}
                              alt={att.filename || "Attachment"}
                              className="max-h-48 rounded-lg border object-contain hover:opacity-90"
                            />
                          </a>
                        );
                      }
                      return (
                        <a
                          key={j}
                          href={src}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs underline text-muted-foreground hover:text-foreground"
                        >
                          {att.filename || "View attachment"}
                        </a>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Agent avatar */}
              {!isUser && (
                <div className="shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center mt-1">
                  <svg className="w-[14px] h-[14px] text-primary-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
                  </svg>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}
