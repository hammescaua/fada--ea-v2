"use client";

import * as React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  api,
  type Farm,
  type FieldAnalytics,
  type Insights,
} from "@/lib/api";
import { FieldBiasChart } from "@/components/insights-charts";
import { PageHeader } from "@/components/page-header";
import { ErrorBlock, LoadingBlock } from "@/components/states";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { EvidenceRows } from "@/components/how-we-got-here";
import { formatBRL, formatNumber } from "@/lib/utils";

function confidenceVariant(c: string): BadgeProps["variant"] {
  if (c === "alta") return "success";
  if (c === "moderada") return "warning";
  return "secondary";
}

export default function InsightsPage() {
  const [farmId, setFarmId] = React.useState<number | null>(null);

  const farmsQuery = useQuery({ queryKey: ["farms"], queryFn: api.getFarms });

  React.useEffect(() => {
    if (farmId === null && farmsQuery.data && farmsQuery.data.length > 0) {
      setFarmId(farmsQuery.data[0].id);
    }
  }, [farmsQuery.data, farmId]);

  const analyticsQuery = useQuery<FieldAnalytics>({
    queryKey: ["field-analytics", farmId],
    queryFn: () => api.getFieldAnalytics(farmId as number),
    enabled: farmId !== null,
  });

  const insightsQuery = useQuery<Insights>({
    queryKey: ["insights", farmId],
    queryFn: () => api.getInsights(farmId as number),
    enabled: farmId !== null,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Inteligência por Talhão"
        description="Comparação entre talhões e insights determinísticos — a partir do dado real registrado, com N e tamanho de efeito."
      />

      <Card>
        <CardContent className="pt-6">
          {farmsQuery.isLoading ? (
            <LoadingBlock label="Carregando fazendas…" />
          ) : farmsQuery.isError ? (
            <ErrorBlock error={farmsQuery.error} />
          ) : !farmsQuery.data || farmsQuery.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Nenhuma fazenda cadastrada. Cadastre em{" "}
              <Link href="/farms" className="text-brand-700 underline">
                Captura de Dados
              </Link>{" "}
              e registre safras com produtividade real em{" "}
              <Link href="/safra" className="text-brand-700 underline">
                Safra
              </Link>
              .
            </p>
          ) : (
            <div className="max-w-sm space-y-2">
              <Label htmlFor="farm">Fazenda</Label>
              <Select
                id="farm"
                value={farmId ?? ""}
                onChange={(e) => setFarmId(Number(e.target.value))}
              >
                {farmsQuery.data.map((f: Farm) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </Select>
            </div>
          )}
        </CardContent>
      </Card>

      {farmId !== null && (
        <>
          {/* Field analytics */}
          <Card>
            <CardHeader>
              <CardTitle>Talhões</CardTitle>
            </CardHeader>
            <CardContent>
              {analyticsQuery.isLoading ? (
                <LoadingBlock label="Calculando…" />
              ) : analyticsQuery.isError ? (
                <ErrorBlock error={analyticsQuery.error} />
              ) : !analyticsQuery.data || analyticsQuery.data.n_fields === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Nenhum talhão com safra registrada. Registre colheitas reais para
                  comparar talhões.
                </p>
              ) : (
                <div className="space-y-6">
                  <FieldBiasChart fields={analyticsQuery.data.fields} />
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border text-left text-muted-foreground">
                          <th className="py-2 pr-4 font-medium">Talhão</th>
                          <th className="py-2 pr-4 font-medium">Safras</th>
                          <th className="py-2 pr-4 font-medium">Prod. média</th>
                          <th className="py-2 pr-4 font-medium">Bias vs. região</th>
                          <th className="py-2 pr-4 font-medium">Estabilidade</th>
                          <th className="py-2 pr-4 font-medium">Custo/ha</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analyticsQuery.data.fields.map((f) => (
                          <tr key={f.field_id} className="border-b border-border/60">
                            <td className="py-2 pr-4 font-medium">{f.field_name}</td>
                            <td className="py-2 pr-4 tabular-nums">{f.n_seasons}</td>
                            <td className="py-2 pr-4 tabular-nums">
                              {formatNumber(f.mean_actual_sc_ha)} sc/ha
                            </td>
                            <td className="py-2 pr-4 tabular-nums">
                              <span
                                className={
                                  f.bias_vs_region_pct >= 0
                                    ? "text-green-700"
                                    : "text-red-700"
                                }
                              >
                                {f.bias_vs_region_pct >= 0 ? "+" : ""}
                                {formatNumber(f.bias_vs_region_pct)}%
                              </span>
                            </td>
                            <td className="py-2 pr-4 tabular-nums">
                              {f.yield_stability_std_pct === null
                                ? "—"
                                : `±${formatNumber(f.yield_stability_std_pct)}%`}
                            </td>
                            <td className="py-2 pr-4 tabular-nums">
                              {f.mean_cost_per_ha === null
                                ? "—"
                                : formatBRL(f.mean_cost_per_ha)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Estabilidade = desvio dos resíduos ajustados ao clima (menor = mais
                    consistente). &quot;—&quot; indica dados insuficientes (&lt; 2 safras
                    ou sem custo).
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Insights */}
          <Card>
            <CardHeader>
              <CardTitle>Insights</CardTitle>
            </CardHeader>
            <CardContent>
              {insightsQuery.isLoading ? (
                <LoadingBlock label="Gerando insights…" />
              ) : insightsQuery.isError ? (
                <ErrorBlock error={insightsQuery.error} />
              ) : !insightsQuery.data || insightsQuery.data.n_insights === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Ainda não há insights — eles surgem quando há safras suficientes
                  (evidence gating). Registre mais colheitas reais.
                </p>
              ) : (
                <div className="space-y-3">
                  {insightsQuery.data.insights.map((i, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-border bg-card px-4 py-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="font-medium">{i.title}</div>
                        <Badge variant={confidenceVariant(i.confidence)}>
                          {i.confidence}
                        </Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{i.detail}</p>
                      {i.evidence && Object.keys(i.evidence).length > 0 && (
                        <details className="mt-1">
                          <summary className="cursor-pointer text-xs text-brand-700">
                            Ver dados
                          </summary>
                          <div className="mt-1 rounded-md bg-muted/50 px-3 py-2">
                            <EvidenceRows evidence={i.evidence} />
                          </div>
                        </details>
                      )}
                    </div>
                  ))}
                  <p className="text-xs text-muted-foreground">
                    {insightsQuery.data.note}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
