"use client";

import React, { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { User, Bot } from "lucide-react";
import type { ChatMessage } from "@/types";
import { cn, formatRelativeTime } from "@/lib/utils";

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isTyping?: boolean;
}

const TypingIndicator: React.FC = () => (
  <div className="flex items-center gap-3 p-4">
    <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
      <Bot className="h-4 w-4 text-slate-400" />
    </div>
    <div className="flex gap-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-2 h-2 rounded-full bg-slate-500"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 0.8,
            repeat: Infinity,
            delay: i * 0.2,
          }}
        />
      ))}
    </div>
  </div>
);

const MessageBubble: React.FC<{
  message: ChatMessage;
  showTimestamp?: boolean;
}> = ({ message, showTimestamp }) => {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.2 }}
      className={cn("flex gap-3 group", isUser ? "flex-row-reverse" : "flex-row")}
    >
      {/* Avatar */}
      <div
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
          isUser
            ? "bg-gradient-to-br from-primary-500 to-secondary-500"
            : "bg-slate-700"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-slate-400" />
        )}
      </div>

      {/* Content */}
      <div className={cn("flex flex-col max-w-[75%]", isUser ? "items-end" : "items-start")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3",
            isUser
              ? "bg-primary-500 text-white rounded-br-md"
              : "bg-slate-700/80 text-slate-200 rounded-bl-md"
          )}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Timestamp (on hover) */}
        <span
          className={cn(
            "text-xs text-slate-500 mt-1 opacity-0 group-hover:opacity-100 transition-opacity",
            showTimestamp && "opacity-100"
          )}
        >
          {formatRelativeTime(message.timestamp)}
        </span>

        {/* Score indicator for user messages */}
        {isUser && message.score !== undefined && (
          <div
            className={cn(
              "mt-2 px-2 py-1 rounded-full text-xs font-medium",
              message.score >= 8
                ? "bg-success-500/20 text-success-400"
                : message.score >= 6
                ? "bg-warning-500/20 text-warning-400"
                : "bg-error-500/20 text-error-400"
            )}
          >
            Score: {message.score}/10
          </div>
        )}
      </div>
    </motion.div>
  );
};

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages, isTyping }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent"
    >
      <div className="p-4 space-y-4 min-h-full">
        {/* Welcome message */}
        {messages.length === 0 && !isTyping && (
          <div className="text-center py-12">
            <Bot className="h-12 w-12 text-slate-500 mx-auto mb-4" />
            <p className="text-slate-400">La conversation va commencer...</p>
          </div>
        )}

        {/* Messages */}
        <AnimatePresence mode="popLayout">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
        </AnimatePresence>

        {/* Typing indicator */}
        {isTyping && <TypingIndicator />}

        {/* Scroll anchor */}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

export default ChatInterface;
