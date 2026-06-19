"use client";

import * as React from "react";

type Row = { label: string; value: React.ReactNode; hint?: string };

/**
 * Bloco expansível "Como chegamos nisso" — mostra a cadeia de raciocínio
 * (entrada, método, ajustes) de forma auditável. Genérico: aceita linhas
 * estruturadas e/ou conteúdo livre.
 */
export function HowWeGotHere({
  title = "Como chegamos nisso",
  rows,
  children,
  defaultOpen = false,
}: {
  title?: string;
  rows?: Row[];
  children?: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = React.useState(defaultOpen);
  return (
    <div className="rounded-lg border border-border bg-card">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium hover:bg-muted/50"
        aria-expanded={open}
      >
        <span>{title}</span>
        <span aria-hidden className="text-muted-foreground">
          {open ? "▾" : "▸"}
        </span>
      </button>
      {open && (
        <div className="space-y-3 border-t border-border px-4 py-3 text-sm">
          {rows && rows.length > 0 && (
            <dl className="space-y-2">
              {rows.map((r, i) => (
                <div
                  key={i}
                  className="flex flex-col gap-0.5 sm:flex-row sm:justify-between sm:gap-4"
                >
                  <dt className="text-muted-foreground">{r.label}</dt>
                  <dd className="font-medium sm:text-right">
                    {r.value}
                    {r.hint && (
                      <span className="ml-1 text-xs font-normal text-muted-foreground">
                        {r.hint}
                      </span>
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          )}
          {children}
        </div>
      )}
    </div>
  );
}

/** Renderiza um dicionário de evidências (chave → valor) em linhas legíveis. */
export function EvidenceRows({ evidence }: { evidence: Record<string, unknown> }) {
  const entries = Object.entries(evidence ?? {});
  if (entries.length === 0) {
    return <p className="text-xs text-muted-foreground">Sem dados detalhados.</p>;
  }
  return (
    <dl className="space-y-1">
      {entries.map(([k, v]) => (
        <div key={k} className="flex justify-between gap-4 text-xs">
          <dt className="text-muted-foreground">{k}</dt>
          <dd className="font-medium tabular-nums">{String(v)}</dd>
        </div>
      ))}
    </dl>
  );
}
