import * as React from "react";
import { ApiError } from "@/lib/api";

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={
        "inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent " +
        (className ?? "")
      }
      aria-label="carregando"
    />
  );
}

export function LoadingBlock({ label = "Carregando..." }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/40 px-4 py-3 text-sm text-muted-foreground">
      <Spinner /> {label}
    </div>
  );
}

export function ErrorBlock({ error }: { error: unknown }) {
  let message = "Ocorreu um erro inesperado.";
  if (error instanceof ApiError) {
    message = error.message;
  } else if (error instanceof Error) {
    message =
      error.message === "Failed to fetch"
        ? "Não foi possível conectar à API. Verifique se o backend está em execução (NEXT_PUBLIC_API_URL)."
        : error.message;
  }
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
      {message}
    </div>
  );
}
