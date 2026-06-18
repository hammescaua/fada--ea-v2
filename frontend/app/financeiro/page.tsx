"use client";

import * as React from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  api,
  type CostBreakdown,
  type Financials,
} from "@/lib/api";
import {
  CostByCategoryChart,
  ProfitScenarioChart,
} from "@/components/financial-charts";
import { PageHeader } from "@/components/page-header";
import { ErrorBlock, LoadingBlock, Spinner } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatNumber, formatBRL } from "@/lib/utils";

function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-4">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold tabular-nums text-foreground">
        {value}
      </div>
      {hint && <div className="mt-1 text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}

export default function FinanceiroPage() {
  const [cycleInput, setCycleInput] = React.useState("");
  const [cycleId, setCycleId] = React.useState<number | null>(null);
  const [priceInput, setPriceInput] = React.useState("125");

  const costQuery = useQuery<CostBreakdown>({
    queryKey: ["crop-cycle-cost", cycleId],
    queryFn: () => api.getCropCycleCost(cycleId as number),
    enabled: cycleId !== null,
  });

  const financials = useMutation<Financials>({
    mutationFn: () =>
      api.getCropCycleFinancials(cycleId as number, {
        price_per_bag: Number(priceInput),
      }),
  });

  const fin = financials.data;

  return (
    <div>
      <PageHeader
        title="Financeiro — Gêmeo Digital"
        description="Custos de produção, ponto de equilíbrio e cenários de lucro de um ciclo de cultivo."
      />

      {/* INPUTS */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Parâmetros</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const id = Number(cycleInput);
              if (!cycleInput || Number.isNaN(id)) return;
              setCycleId(id);
              financials.reset();
            }}
            className="grid grid-cols-1 gap-4 md:grid-cols-3 md:items-end"
          >
            <div className="space-y-2">
              <Label htmlFor="cycleId">ID do ciclo de cultivo</Label>
              <Input
                id="cycleId"
                type="number"
                min="1"
                value={cycleInput}
                onChange={(e) => setCycleInput(e.target.value)}
                placeholder="Ex.: 1"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="price">Preço da saca (R$/sc)</Label>
              <Input
                id="price"
                type="number"
                min="0"
                step="0.01"
                value={priceInput}
                onChange={(e) => setPriceInput(e.target.value)}
              />
            </div>
            <div>
              <Button type="submit" disabled={!cycleInput}>
                Carregar custos
              </Button>
            </div>
          </form>
          <p className="text-xs text-muted-foreground">
            Crie ciclos na página{" "}
            <span className="font-medium">Captura de Dados</span> e registre
            eventos com custo na página <span className="font-medium">Safra</span>.
          </p>
        </CardContent>
      </Card>

      {cycleId === null ? (
        <p className="text-sm text-muted-foreground">
          Informe um ID de ciclo para começar.
        </p>
      ) : (
        <div className="space-y-6">
          {/* COST BREAKDOWN */}
          <Card>
            <CardHeader>
              <CardTitle>Custos de produção</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {costQuery.isLoading && (
                <LoadingBlock label="Carregando custos..." />
              )}
              {costQuery.isError && <ErrorBlock error={costQuery.error} />}
              {costQuery.data && (
                <>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <Stat
                      label="Custo total"
                      value={formatBRL(costQuery.data.total_cost)}
                      hint={`${formatNumber(costQuery.data.area_ha)} ha`}
                    />
                    <Stat
                      label="Custo por hectare"
                      value={formatBRL(costQuery.data.cost_per_hectare)}
                    />
                    <Stat
                      label="Custo por saca"
                      value={
                        costQuery.data.cost_per_bag != null
                          ? formatBRL(costQuery.data.cost_per_bag)
                          : "—"
                      }
                      hint={
                        costQuery.data.cost_per_bag == null
                          ? "Requer produtividade (real ou esperada)."
                          : costQuery.data.yield_sc_ha != null
                            ? `Base: ${formatNumber(
                                costQuery.data.yield_sc_ha
                              )} sc/ha`
                            : undefined
                      }
                    />
                    <Stat
                      label="Aplicações"
                      value={costQuery.data.n_applications}
                    />
                  </div>

                  <div>
                    <h3 className="mb-2 text-sm font-medium text-foreground">
                      Custo por categoria
                    </h3>
                    <CostByCategoryChart breakdown={costQuery.data} />
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* FINANCIALS / SCENARIOS */}
          <Card>
            <CardHeader>
              <CardTitle>Cenários de lucratividade</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!priceInput) return;
                  financials.mutate();
                }}
                className="flex flex-col gap-3 sm:flex-row sm:items-end"
              >
                <div className="flex-1 space-y-2">
                  <Label htmlFor="price2">Preço da saca (R$/sc)</Label>
                  <Input
                    id="price2"
                    type="number"
                    min="0"
                    step="0.01"
                    value={priceInput}
                    onChange={(e) => setPriceInput(e.target.value)}
                  />
                </div>
                <Button
                  type="submit"
                  disabled={!priceInput || financials.isPending}
                >
                  {financials.isPending && <Spinner />}
                  Calcular cenários
                </Button>
              </form>

              {financials.isError && <ErrorBlock error={financials.error} />}

              {fin && (
                <>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <Stat
                      label="Ponto de equilíbrio"
                      value={`${formatNumber(
                        fin.break_even_yield_sc_ha
                      )} sc/ha`}
                      hint={`Fonte da produtividade: ${fin.yield_source}`}
                    />
                    <Stat
                      label="Preço considerado"
                      value={`${formatBRL(fin.price_per_bag)}/sc`}
                    />
                  </div>

                  <div>
                    <h3 className="mb-2 text-sm font-medium text-foreground">
                      Lucro por cenário
                    </h3>
                    <ProfitScenarioChart scenarios={fin.scenarios} />
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                        <tr>
                          <th className="px-3 py-2 font-medium">Cenário</th>
                          <th className="px-3 py-2 font-medium">
                            Prod. (sc/ha)
                          </th>
                          <th className="px-3 py-2 font-medium">Receita</th>
                          <th className="px-3 py-2 font-medium">Custo</th>
                          <th className="px-3 py-2 font-medium">Lucro</th>
                          <th className="px-3 py-2 font-medium">Margem</th>
                          <th className="px-3 py-2 font-medium">Lucro/ha</th>
                        </tr>
                      </thead>
                      <tbody>
                        {fin.scenarios.map((s) => (
                          <tr key={s.name} className="border-t border-border">
                            <td className="px-3 py-2 font-medium">{s.name}</td>
                            <td className="px-3 py-2 tabular-nums">
                              {formatNumber(s.yield_sc_ha)}
                            </td>
                            <td className="px-3 py-2 tabular-nums">
                              {formatBRL(s.revenue)}
                            </td>
                            <td className="px-3 py-2 tabular-nums">
                              {formatBRL(s.total_cost)}
                            </td>
                            <td
                              className={
                                "px-3 py-2 font-medium tabular-nums " +
                                (s.profit >= 0
                                  ? "text-green-700"
                                  : "text-red-700")
                              }
                            >
                              {formatBRL(s.profit)}
                            </td>
                            <td className="px-3 py-2 tabular-nums">
                              {formatNumber(s.margin_pct)}%
                            </td>
                            <td className="px-3 py-2 tabular-nums">
                              {formatBRL(s.profit_per_hectare)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
