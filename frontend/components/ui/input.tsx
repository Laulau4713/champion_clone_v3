import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, icon, iconPosition = "left", ...props }, ref) => {
    const hasIcon = !!icon;

    return (
      <div className="relative w-full">
        {hasIcon && iconPosition === "left" && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 transition-colors peer-focus:text-primary-400">
            {icon}
          </div>
        )}
        <input
          type={type}
          className={cn(
            "peer flex h-11 w-full rounded-lg border bg-slate-800/50 px-4 py-2.5 text-sm text-white placeholder:text-slate-500",
            "transition-all duration-200 ease-out",
            "focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 focus:bg-slate-800/80",
            "disabled:cursor-not-allowed disabled:opacity-50",
            error
              ? "border-error-500 focus:ring-error-500/50 focus:border-error-500"
              : "border-slate-700 hover:border-slate-500 hover:bg-slate-800/60",
            hasIcon && iconPosition === "left" && "pl-10",
            hasIcon && iconPosition === "right" && "pr-10",
            className
          )}
          ref={ref}
          {...props}
        />
        {hasIcon && iconPosition === "right" && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition-colors peer-focus:text-primary-400">
            {icon}
          </div>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement> & { error?: boolean }
>(({ className, error, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        "flex min-h-[120px] w-full rounded-lg border bg-slate-800/50 px-4 py-3 text-sm text-white placeholder:text-slate-500 resize-none",
        "transition-all duration-200 ease-out",
        "focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 focus:bg-slate-800/80",
        "disabled:cursor-not-allowed disabled:opacity-50",
        error
          ? "border-error-500 focus:ring-error-500/50 focus:border-error-500"
          : "border-slate-700 hover:border-slate-500 hover:bg-slate-800/60",
        className
      )}
      ref={ref}
      {...props}
    />
  );
});
Textarea.displayName = "Textarea";

export { Input, Textarea };
