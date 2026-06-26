"use client";

import * as React from "react";
import { type DecisionCard } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { formatBRL, formatNumber } from "@/lib/utils";

const SOURCE_LABEL: Record<string, string> = {
  clima: "Clima",
  manejo: "Manejo",
  historico: "Histórico",
};

function severityVariant(sev: string): BadgeProps["variant"] {
  if (sev === "alerta") return "danger";
  if (sev === "atenção") return "warning";
  return "secondary";
}

function sourceBorder(source: string): string {
  if (source === "clima") return "border-l-4 border-l-sky-500";
  if (source === "manejo") return "border-l-4 border-l-green-500";
  return "border-l-4 border-l-amber-500";
}

function Range({ low, point, high, fmt }: { low: number; point: number; high: number; fmt: (n: number) => string }) {
  return (
    <span className="tabular-nums">
      <span className="font-semibold">{fmt(point)}</span>{" "}
      <span className="text-xs text-muted-foreground">({fmt(low)} – {fmt(high)})</span>
    </span>
  );
}

export function DecisionCardItem({ card }: { card: DecisionCard }) {
  return (
    <Card className={sourceBorder(card.source)}>
      <CardContent className="space-y-2 pt-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{SOURCE_LABEL[card.source] ?? card.source}</Badge>
          <Badge variant={severityVariant(card.severity)}>{card.severity}</Badge>
          <span className="text-xs text-muted-foreground">
            confiança {card.confidence} · {card.horizon}
          </span>
        </div>

        <div>
          <div className="text-sm font-medium text-foreground">{card.decision}</div>
          <div className="text-sm text-muted-foreground">{card.recommendation}</div>
        </div>

        {card.effect && (
          <div className="rounded-md bg-muted/40 px-3 py-2 text-sm">
            <span className="text-xs uppercase text-muted-foreground">
              Efeito esperado ({card.effect.basis})
            </span>
            <div className="mt-1 flex flex-wrap gap-x-6 gap-y-1">
              {card.effect.profit_brl_ha && (
                <span className="text-green-700">
                  Lucro:{" "}
                  <Range
                    low={card.effect.profit_brl_ha[0]}
                    point={card.effect.profit_brl_ha[1]}
                    high={card.effect.profit_brl_ha[2]}
                    fmt={(n) => `${formatBRL(n)}/ha`}
                  />
                </span>
              )}
              {card.effect.yield_sc_ha && (
                <span>
                  Produtividade:{" "}
                  <Range
                    low={card.effect.yield_sc_ha[0]}
                    point={card.effect.yield_sc_ha[1]}
                    high={card.effect.yield_sc_ha[2]}
                    fmt={(n) => `${formatNumber(n)} sc/ha`}
                  />
                </span>
              )}
            </div>
          </div>
        )}

        {card.why.length > 0 && (
          <details>
            <summary className="cursor-pointer text-xs text-brand-700">Por quê</summary>
            <ul className="mt-1 space-y-0.5 text-xs text-muted-foreground">
              {card.why.map((e, i) => (
                <li key={i}>
                  <span className="font-medium">{e.label}:</span> {e.detail}
                </li>
              ))}
            </ul>
          </details>
        )}

        <p className="text-xs italic text-muted-foreground">{card.disclaimer}</p>
      </CardContent>
    </Card>
  );
}
