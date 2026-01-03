"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
  {
    variants: {
      variant: {
        default:
          "bg-primary-500 text-white hover:bg-primary-600 hover:shadow-xl hover:shadow-primary-500/30 hover:-translate-y-0.5 active:bg-primary-700 active:translate-y-0 shadow-lg shadow-primary-500/25",
        secondary:
          "bg-secondary-500 text-white hover:bg-secondary-600 hover:shadow-xl hover:shadow-secondary-500/30 hover:-translate-y-0.5 active:bg-secondary-700 active:translate-y-0 shadow-lg shadow-secondary-500/25",
        destructive:
          "bg-error-500 text-white hover:bg-error-600 hover:shadow-lg hover:shadow-error-500/30 hover:-translate-y-0.5 active:bg-error-700 active:translate-y-0",
        outline:
          "border border-slate-600 bg-transparent text-slate-200 hover:bg-slate-800/80 hover:border-primary-500/50 hover:text-white hover:-translate-y-0.5 active:translate-y-0",
        ghost:
          "bg-transparent text-slate-200 hover:bg-slate-800/80 hover:text-white",
        link:
          "text-primary-400 underline-offset-4 hover:underline hover:text-primary-300",
        success:
          "bg-success-500 text-white hover:bg-success-600 hover:shadow-lg hover:shadow-success-500/30 hover:-translate-y-0.5 active:bg-success-700 active:translate-y-0",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-12 rounded-lg px-8 text-base",
        xl: "h-14 rounded-xl px-10 text-lg",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading, children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";

    // When using asChild, we can't add loading spinner as it breaks single child requirement
    if (asChild) {
      return (
        <Comp
          className={cn(buttonVariants({ variant, size, className }))}
          ref={ref}
          {...props}
        >
          {children}
        </Comp>
      );
    }

    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {children}
      </Comp>
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
