import * as React from "react";
import { cn } from "@/lib/utils";

type BadgeVariant =
  | "default"
  | "secondary"
  | "outline"
  | "success"
  | "warning"
  | "danger";

const variants: Record<BadgeVariant, string> = {
  default: "bg-brand-600 text-white border-transparent",
  secondary: "bg-muted text-muted-foreground border-transparent",
  outline: "text-foreground border-border",
  success: "bg-green-100 text-green-800 border-green-200",
  warning: "bg-amber-100 text-amber-800 border-amber-200",
  danger: "bg-red-100 text-red-800 border-red-200",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

/** Map a severity string from the API to a badge variant. */
export function severityVariant(severity: string): BadgeVariant {
  const s = severity.toLowerCase();
  if (s.includes("alto") || s.includes("alta") || s === "high") return "danger";
  if (s.includes("moder") || s === "medium") return "warning";
  if (s.includes("baix") || s === "low") return "success";
  return "secondary";
}
