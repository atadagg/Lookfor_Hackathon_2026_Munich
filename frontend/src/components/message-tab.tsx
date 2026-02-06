"use client";

import { ThreadDetail } from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface MessageTabProps {
  thread: ThreadDetail;
}

export function MessageTab({ thread }: MessageTabProps) {
  return (
    <ScrollArea className="h-full">
      <div className="flex flex-col gap-3 p-4">
        {thread.messages.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-8">
            No messages in this thread
          </p>
        )}
        {thread.messages.map((msg, i) => {
          const isUser = msg.role === "user";
          return (
            <div
              key={i}
              className={cn("flex", isUser ? "justify-start" : "justify-end")}
            >
              <Card
                className={cn(
                  "max-w-[80%]",
                  isUser
                    ? "bg-muted"
                    : "bg-primary text-primary-foreground"
                )}
              >
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold uppercase">
                      {isUser ? "Customer" : "AI Agent"}
                    </span>
                    {msg.created_at && (
                      <span
                        className={cn(
                          "text-[10px]",
                          isUser ? "text-muted-foreground" : "text-primary-foreground/70"
                        )}
                      >
                        {new Date(msg.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    )}
                  </div>
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">
                    {msg.content}
                  </p>
                </CardContent>
              </Card>
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}
