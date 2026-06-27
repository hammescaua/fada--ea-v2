"use client";

import * as React from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  api,
  type CompareCropsResult,
  type CreditCatalog,
  type FinancingResult,
} from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { ErrorBlock, LoadingBlock } from "@/components/states";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Stat } from "@/components/stat";
import { formatBRL } from "@/lib/utils";

type CropRow = { name: string; yield_sc_ha: string; price_per_bag: string; cost_per_ha: string };

const DEFAULT_ROWS: CropRow[] = [
  { name: "Trigo", yield_sc_ha: "", price_per_bag: "", cost_per_ha: "" },
  { name: "Milho 2ª safra", yield_sc_ha: "", price_per_bag: "", cost_per_ha: "" },
];

export default function CreditoPage() {
  const lines = useQuery<CreditCatalog>({
    queryKey: ["credit-lines"],
    queryFn: api.getCreditLines,
    retry: false,
  });

  // --- Simulador de financiamento -----------------------------------------
  const [principal, setPrincipal] = React.useState("");
  const [rate, setRate] = React.useState("");
  const [term, setTerm] = React.useState("12");
  const [system, setSystem] = React.useState("price");
  const [area, setArea] = React.useState("");
  const sim = useMutation<FinancingResult>({
    mutationFn: () =>
      api.simulateFinancing({
        principal: Number(principal),
        annual_rate_pct: Number(rate),
        term_months: Number(term),
        system,
        area_ha: area ? Number(area) : undefined,
      }),
  });

  // --- Comparar 2ª safra ----------------------------------------------------
  const [rows, setRows] = React.useState<CropRow[]>(DEFAULT_ROWS);
  const cmp = useMutation<CompareCropsResult>({
    mutationFn: () =>
      api.compareCrops(
        rows
          .filter((r) => r.name.trim())
          .map((r) => ({
            name: r.name.trim(),
            yield_sc_ha: Number(r.yield_sc_ha || 0),
            price_per_bag: Number(r.price_per_bag || 0),
            cost_per_ha: Number(r.cost_per_ha || 0),
          }))
      ),
  });

  function updateRow(i: number, patch: Partial<CropRow>) {
    setRows((s) => s.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Crédito & 2ª safra"
        description="Simule o financiamento da safra (custeio/investimento) e compare a margem das opções de inverno/2ª safra — para decidir com a conta na mão."
      />

      {/* Simulador de financiamento */}
      <Card>
        <CardHeader>
          <CardTitle>Simulador de financiamento (Plano Safra)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <form
            className="flex flex-wrap items-end gap-3"
            onSubmit={(e) => {
              e.preventDefault();
              if (principal && rate && term) sim.mutate();
            }}
          >
            <div className="space-y-1">
              <Label htmlFor="principal">Valor (R$)</Label>
              <Input
                id="principal"
                type="number"
                value={principal}
                onChange={(e) => setPrincipal(e.target.value)}
                placeholder="Ex.: 300000"
                className="w-36"
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="rate">Juros (% a.a.)</Label>
              <Input
                id="rate"
                type="number"
                step="0.01"
                value={rate}
                onChange={(e) => setRate(e.target.value)}
                placeholder="Ex.: 8"
                className="w-28"
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="term">Prazo (meses)</Label>
              <Input
                id="term"
                type="number"
                value={term}
                onChange={(e) => setTerm(e.target.value)}
                className="w-28"
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="system">Sistema</Label>
              <Select id="system" value={system} onChange={(e) => setSystem(e.target.value)}>
                <option value="price">Price (parcela fixa)</option>
                <option value="sac">SAC (decrescente)</option>
              </Select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="area">Área (ha, opcional)</Label>
              <Input
                id="area"
                type="number"
                value={area}
                onChange={(e) => setArea(e.target.value)}
                placeholder="p/ R$/ha"
                className="w-28"
              />
            </div>
            <Button type="submit" disabled={sim.isPending}>
              {sim.isPending ? "Calculando…" : "Simular"}
            </Button>
          </form>

          {/* Linhas de referência — preenche a taxa ao clicar */}
          {lines.data && lines.data.lines.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">
                Taxas de <strong>referência</strong> (clique para preencher). Confirme a
                taxa vigente com seu agente financeiro.
              </p>
              <div className="flex flex-wrap gap-2">
                {lines.data.lines.map((ln) => {
                  const mid =
                    (ln.ref_rate_pct_year[0] + ln.ref_rate_pct_year[1]) / 2;
                  return (
                    <button
                      key={ln.key}
                      type="button"
                      onClick={() => setRate(String(mid))}
                      title={ln.note ?? ""}
                      className="rounded-md border border-border px-2.5 py-1 text-xs hover:bg-muted"
                    >
                      {ln.name} · {ln.ref_rate_pct_year[0]}–{ln.ref_rate_pct_year[1]}% a.a.
                    </button>
                  );
                })}
              </div>
              <p className="text-[11px] text-muted-foreground">
                Fonte: {lines.data.source} · {lines.data.fetched_at}
                {lines.data.safra ? ` · safra ${lines.data.safra}` : ""}
                {lines.data.vigencia ? ` · vigência ${lines.data.vigencia}` : ""}.
              </p>
              <details className="text-xs">
                <summary className="cursor-pointer text-brand-700">
                  Ver linhas, taxas e limites de referência
                </summary>
                <div className="mt-2 overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border text-left text-muted-foreground">
                        <th className="py-1.5 pr-3">Linha</th>
                        <th className="py-1.5 pr-3">Finalidade</th>
                        <th className="py-1.5 pr-3">Taxa ref. (% a.a.)</th>
                        <th className="py-1.5 pr-3">Público / limite</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lines.data.lines.map((ln) => (
                        <tr key={ln.key} className="border-b border-border last:border-0 align-top">
                          <td className="py-1.5 pr-3 font-medium">{ln.name}</td>
                          <td className="py-1.5 pr-3 capitalize">{ln.purpose}</td>
                          <td className="py-1.5 pr-3 tabular-nums">
                            {ln.ref_rate_pct_year[0] === ln.ref_rate_pct_year[1]
                              ? `${ln.ref_rate_pct_year[0]}`
                              : `${ln.ref_rate_pct_year[0]}–${ln.ref_rate_pct_year[1]}`}
                          </td>
                          <td className="py-1.5 pr-3 text-muted-foreground">
                            {ln.audience}
                            {ln.limit ? ` · ${ln.limit}` : ""}
                            {ln.note ? ` — ${ln.note}` : ""}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
              {lines.data.note && (
                <p className="rounded-md bg-amber-50 p-2 text-[11px] text-amber-900">
                  {lines.data.note}
                </p>
              )}
            </div>
          )}

          {sim.isError && <ErrorBlock error={sim.error} />}
          {sim.data && (
            <div className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <Stat
                  label={system === "sac" ? "1ª parcela" : "Parcela"}
                  value={formatBRL(sim.data.first_installment)}
                />
                {system === "sac" && (
                  <Stat label="Última parcela" value={formatBRL(sim.data.last_installment)} />
                )}
                <Stat label="Juros totais" value={formatBRL(sim.data.total_interest)} />
                <Stat label="Total pago" value={formatBRL(sim.data.total_paid)} />
                <Stat
                  label="Juros sobre o valor"
                  value={`${sim.data.interest_over_principal_pct}%`}
                />
                {sim.data.principal_per_ha != null && (
                  <Stat label="Financiado por ha" value={formatBRL(sim.data.principal_per_ha)} />
                )}
                {sim.data.total_interest_per_ha != null && (
                  <Stat label="Juros por ha" value={formatBRL(sim.data.total_interest_per_ha)} />
                )}
              </div>
              <p className="text-xs text-muted-foreground">{sim.data.disclaimer}</p>
            </div>
          )}
          {lines.isLoading && <LoadingBlock label="Carregando linhas…" />}
        </CardContent>
      </Card>

      {/* Comparar 2ª safra / inverno */}
      <Card>
        <CardHeader>
          <CardTitle>Comparar 2ª safra / inverno (margem por hectare)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-xs text-muted-foreground">
            Informe produtividade, preço e custo de cada opção (trigo, milho 2ª safra,
            aveia/cobertura…). O FADA mostra quanto sobra por hectare em cada uma. São
            seus números — não uma previsão.
          </p>
          <div className="space-y-2">
            {rows.map((r, i) => (
              <div key={i} className="flex flex-wrap items-end gap-2">
                <div className="space-y-1">
                  <Label htmlFor={`name-${i}`}>Cultura</Label>
                  <Input
                    id={`name-${i}`}
                    value={r.name}
                    onChange={(e) => updateRow(i, { name: e.target.value })}
                    className="w-40"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor={`y-${i}`}>Produt. (sc/ha)</Label>
                  <Input
                    id={`y-${i}`}
                    type="number"
                    value={r.yield_sc_ha}
                    onChange={(e) => updateRow(i, { yield_sc_ha: e.target.value })}
                    className="w-28"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor={`p-${i}`}>Preço (R$/sc)</Label>
                  <Input
                    id={`p-${i}`}
                    type="number"
                    value={r.price_per_bag}
                    onChange={(e) => updateRow(i, { price_per_bag: e.target.value })}
                    className="w-28"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor={`c-${i}`}>Custo (R$/ha)</Label>
                  <Input
                    id={`c-${i}`}
                    type="number"
                    value={r.cost_per_ha}
                    onChange={(e) => updateRow(i, { cost_per_ha: e.target.value })}
                    className="w-28"
                  />
                </div>
                {rows.length > 1 && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setRows((s) => s.filter((_, idx) => idx !== i))}
                  >
                    Remover
                  </Button>
                )}
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                setRows((s) => [...s, { name: "", yield_sc_ha: "", price_per_bag: "", cost_per_ha: "" }])
              }
            >
              + Adicionar opção
            </Button>
            <Button type="button" onClick={() => cmp.mutate()} disabled={cmp.isPending}>
              {cmp.isPending ? "Comparando…" : "Comparar margens"}
            </Button>
          </div>

          {cmp.isError && <ErrorBlock error={cmp.error} />}
          {cmp.data && (
            <div className="space-y-3">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="py-2 pr-3">#</th>
                      <th className="py-2 pr-3">Cultura</th>
                      <th className="py-2 pr-3">Receita/ha</th>
                      <th className="py-2 pr-3">Custo/ha</th>
                      <th className="py-2 pr-3">Margem/ha</th>
                      <th className="py-2 pr-3">vs. 1º</th>
                      <th className="py-2 pr-3">Empata em</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cmp.data.options.map((o) => (
                      <tr key={o.name} className="border-b border-border last:border-0">
                        <td className="py-2 pr-3">
                          {o.rank === 1 ? <Badge variant="success">1º</Badge> : o.rank}
                        </td>
                        <td className="py-2 pr-3 font-medium">{o.name}</td>
                        <td className="py-2 pr-3 tabular-nums">{formatBRL(o.revenue_per_ha)}</td>
                        <td className="py-2 pr-3 tabular-nums">{formatBRL(o.cost_per_ha)}</td>
                        <td
                          className={
                            "py-2 pr-3 tabular-nums font-medium " +
                            (o.margin_per_ha >= 0 ? "text-emerald-700" : "text-red-700")
                          }
                        >
                          {formatBRL(o.margin_per_ha)}
                        </td>
                        <td className="py-2 pr-3 tabular-nums text-muted-foreground">
                          {o.rank === 1 ? "—" : formatBRL(o.delta_vs_best_per_ha)}
                        </td>
                        <td className="py-2 pr-3 tabular-nums text-muted-foreground">
                          {o.break_even_sc_ha !== null ? `${o.break_even_sc_ha} sc/ha` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-muted-foreground">{cmp.data.disclaimer}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
