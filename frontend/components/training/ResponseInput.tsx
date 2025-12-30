"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ResponseInputProps {
  onSubmit: (response: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export const ResponseInput: React.FC<ResponseInputProps> = ({
  onSubmit,
  isLoading,
  disabled,
  placeholder = "Votre réponse...",
}) => {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [value]);

  // Focus on mount
  useEffect(() => {
    if (!disabled && !isLoading) {
      textareaRef.current?.focus();
    }
  }, [disabled, isLoading]);

  const handleSubmit = () => {
    const trimmedValue = value.trim();
    if (trimmedValue && !isLoading && !disabled) {
      onSubmit(trimmedValue);
      setValue("");
      // Reset height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="border-t border-slate-700/50 bg-slate-800/80 backdrop-blur-sm p-4"
    >
      <div className="flex gap-3 items-end max-w-4xl mx-auto">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading || disabled}
            rows={1}
            className={cn(
              "w-full resize-none rounded-xl border bg-slate-900/50 px-4 py-3 text-sm text-white",
              "placeholder:text-slate-500 transition-all",
              "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "border-slate-700 hover:border-slate-600"
            )}
          />

          {/* Character count */}
          <div className="absolute bottom-2 right-3 text-xs text-slate-500">
            {value.length > 0 && `${value.length}/500`}
          </div>
        </div>

        <Button
          onClick={handleSubmit}
          disabled={!value.trim() || isLoading || disabled}
          size="icon"
          className={cn(
            "h-11 w-11 rounded-xl flex-shrink-0",
            "bg-primary-500 hover:bg-primary-600 disabled:bg-slate-700"
          )}
        >
          {isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </Button>
      </div>

      {/* Hint */}
      <p className="text-xs text-slate-500 text-center mt-2">
        Appuyez sur Entrée pour envoyer, Shift+Entrée pour un saut de ligne
      </p>
    </motion.div>
  );
};

export default ResponseInput;
