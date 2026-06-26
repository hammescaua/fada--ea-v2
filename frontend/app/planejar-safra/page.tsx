"use client";

import * as React from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, type Farm, type Field, type SeasonBrief } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { MunicipalitySelect } from "@/components/municipality-select";
import { ErrorBlock, Spinner } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { formatBRL, formatNumber } from "@/lib/utils";

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
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums text-foreground">{value}</div>
      {hint && <div className="mt-1 text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}

const mmddToBR = (s: string) => {
  const [m, d] = s.split("-");
  return `${d}/${m}`;
};

export default function PlanejarSafraPage() {
  const [municipality, setMunicipality] = React.useState("");
  const [season, setSeason] = React.useState("2026/27");
  const [price, setPrice] = React.useState("");
  const [farmId, setFarmId] = React.useState<number | null>(null);
  const [fieldId, setFieldId] = React.useState<number | null>(null);

  const farms = useQuery<Farm[]>({ queryKey: ["farms"], queryFn: api.getFarms });
  const fields = useQuery<Field[]>({
    queryKey: ["fields", farmId],
    queryFn: () => api.getFields(farmId as number),
    enabled: farmId !== null,
  });

  const mutation = useMutation<SeasonBrief, Error>({
    mutationFn: () => {
      const p = price ? Number(price) : undefined;
      // Talhão escolhido → brief personalizado pelo perfil; senão, regional pelo município.
      return fieldId !== null
        ? api.getSeasonBriefForField(fieldId, season, p)
        : api.getSeasonBrief(municipality, season, p);
    },
  });

  const b = mutation.data;
  const canSubmit = fieldId !== null || municipality !== "";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Planejar a Safra"
        description="Antes de plantar: produtividade esperada, janela oficial ZARC, preço, custo de referência e a margem projetada — em um só lugar, com dado público oficial. Escolha um talhão para personalizar pelo seu perfil agronômico."
      />

      <Card>
        <CardContent className="space-y-4 pt-6">
          {farms.data && farms.data.length > 0 && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="farm">Fazenda (opcional — personaliza)</Label>
                <Select
                  id="farm"
                  value={farmId ?? ""}
                  onChange={(e) => {
                    setFarmId(e.target.value ? Number(e.target.value) : null);
                    setFieldId(null);
                  }}
                >
                  <option value="">— usar município —</option>
                  {farms.data.map((f) => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="field">Talhão</Label>
                <Select
                  id="field"
                  value={fieldId ?? ""}
                  onChange={(e) => setFieldId(e.target.value ? Number(e.target.value) : null)}
                  disabled={farmId === null}
                >
                  <option value="">— selecione —</option>
                  {(fields.data ?? []).map((f) => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </Select>
              </div>
            </div>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (canSubmit) mutation.mutate();
            }}
            className="grid grid-cols-1 gap-4 md:grid-cols-4 md:items-end"
          >
            <div className="space-y-2">
              <Label htmlFor="municipality">Município</Label>
              <MunicipalitySelect
                id="municipality"
                value={municipality}
                onChange={setMunicipality}
                disabled={fieldId !== null}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="season">Safra</Label>
              <Input id="season" value={season} onChange={(e) => setSeason(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="price">
                Preço (R$/sc){" "}
                <span className="font-normal text-muted-foreground">— vazio: CEPEA</span>
              </Label>
              <Input
                id="price"
                type="number"
                value={price}
                placeholder="cotação ao vivo"
                onChange={(e) => setPrice(e.target.value)}
              />
            </div>
            <Button type="submit" disabled={!canSubmit || mutation.isPending}>
              {mutation.isPending && <Spinner />}
              Gerar plano
            </Button>
          </form>
        </CardContent>
      </Card>

      {mutation.isError && <ErrorBlock error={mutation.error} />}

      {b && (
        <div className="space-y-6">
          {/* LEITURA DA SAFRA — explicação em linguagem natural das projeções */}
          <Card className="border-brand-200 bg-brand-50/40">
            <CardHeader>
              <CardTitle>Leitura da safra</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(b.narrative ?? [b.verdict]).map((p, i) => (
                <p
                  key={i}
                  className={
                    "text-sm leading-relaxed " +
                    (i === b.narrative.length - 1
                      ? "italic text-muted-foreground"
                      : "text-foreground")
                  }
                >
                  {p}
                </p>
              ))}
            </CardContent>
          </Card>

          {/* PRODUTIVIDADE */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Quanto devo colher
                {b.yield.personalized ? (
                  <Badge variant="success">
                    personalizado pelo perfil ({b.yield.adjustment?.total_effect_pct! > 0 ? "+" : ""}
                    {formatNumber(b.yield.adjustment?.total_effect_pct ?? 0)}%)
                  </Badge>
                ) : (
                  <Badge variant="secondary">média regional</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <Stat
                  label="Esperado"
                  value={`${formatNumber(b.yield.expected_sc_ha)} sc/ha`}
                  hint={`${b.yield.n_years} anos de histórico`}
                />
                <Stat
                  label="Intervalo (~80%)"
                  value={`${formatNumber(b.yield.interval_sc_ha[0])}–${formatNumber(
                    b.yield.interval_sc_ha[1]
                  )}`}
                  hint="sc/ha"
                />
                <Stat
                  label="Cenários"
                  value={b.yield.scenarios
                    .map((s) => formatNumber(s.yield_sc_ha))
                    .join(" · ")}
                  hint={b.yield.scenarios.map((s) => s.name).join(" · ")}
                />
              </div>
              {b.yield.risks.length > 0 && (
                <ul className="list-inside list-disc text-xs text-muted-foreground">
                  {b.yield.risks.map((r, i) => (
                    <li key={i}>
                      <span className="font-medium">{r.factor}</span> ({r.severity}) —{" "}
                      {r.description}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          {/* PLANTIO: ZARC oficial + melhor data */}
          <Card>
            <CardHeader>
              <CardTitle>Quando plantar</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {b.planting.zarc ? (
                <div className="space-y-1">
                  <Badge variant="secondary">
                    ZARC oficial · safra {b.planting.zarc.safra}
                  </Badge>
                  <div className="flex flex-wrap gap-x-6 gap-y-1">
                    {Object.entries(b.planting.zarc.windows_by_risk).map(([risk, wins]) => (
                      <div key={risk}>
                        <span className="font-medium">Risco {risk}%: </span>
                        {wins.length === 0
                          ? "—"
                          : wins.map((w) => `${mmddToBR(w.start)}–${mmddToBR(w.end)}`).join(", ")}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground">Janela ZARC indisponível para o município.</p>
              )}
              {b.planting.best_date && (
                <p>
                  <span className="text-muted-foreground">Data mais robusta (otimizador): </span>
                  <span className="font-medium">{b.planting.best_date.planting_date}</span> —
                  esperado {formatNumber(b.planting.best_date.expected_yield_sc_ha)} sc/ha, piso{" "}
                  {formatNumber(b.planting.best_date.downside_sc_ha)} (P10).
                </p>
              )}
            </CardContent>
          </Card>

          {/* MARGEM: preço + custo + break-even */}
          {b.margin && b.price && b.cost ? (
            <Card>
              <CardHeader>
                <CardTitle>Vale a conta?</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <Stat
                    label="Preço considerado"
                    value={`${formatBRL(b.margin.price_per_bag)}/sc`}
                    hint={b.price.source + (b.price.day ? ` · ${b.price.day}` : "")}
                  />
                  <Stat
                    label="Custo de referência (COT)"
                    value={`${formatBRL(b.margin.cost_per_ha_cot)}/ha`}
                    hint={
                      b.margin.cost_adjustment
                        ? `personalizado (${b.margin.cost_adjustment.total_effect_pct > 0 ? "+" : ""}${formatNumber(b.margin.cost_adjustment.total_effect_pct)}% vs CONAB)`
                        : `CONAB · safra ${b.cost.safra}`
                    }
                  />
                  <Stat
                    label="Margem esperada"
                    value={
                      <span
                        className={
                          b.margin.expected.profit_per_ha >= 0
                            ? "text-green-700"
                            : "text-red-700"
                        }
                      >
                        {formatBRL(b.margin.expected.profit_per_ha)}/ha
                      </span>
                    }
                    hint={`${formatNumber(b.margin.expected.margin_pct)}% sobre o COT`}
                  />
                </div>

                <div>
                  <h3 className="mb-1 text-sm font-medium">Ponto de equilíbrio (sc/ha)</h3>
                  <div className="flex flex-wrap gap-x-6 text-sm">
                    <span>COE (caixa): <b>{b.margin.break_even_yield_sc_ha.coe}</b></span>
                    <span>COT (+deprec.): <b>{b.margin.break_even_yield_sc_ha.cot}</b></span>
                    <span>CT (total): <b>{b.margin.break_even_yield_sc_ha.ct}</b></span>
                  </div>
                </div>

                {b.margin.cost_adjustment && b.margin.cost_adjustment.factors.length > 0 && (
                  <div className="rounded-md bg-muted/40 p-3 text-xs">
                    <span className="font-medium">
                      Custo personalizado pelo perfil do talhão (vs referência CONAB):
                    </span>
                    <ul className="mt-1 space-y-0.5">
                      {b.margin.cost_adjustment.factors.map((f) => (
                        <li key={f.key} className="text-muted-foreground">
                          <span
                            className={
                              "font-medium " +
                              (f.effect_pct >= 0 ? "text-red-700" : "text-green-700")
                            }
                          >
                            {f.effect_pct > 0 ? "+" : ""}
                            {f.effect_pct}%
                          </span>{" "}
                          — {f.rationale}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                      <tr>
                        <th className="px-3 py-2 font-medium">Cenário</th>
                        <th className="px-3 py-2 font-medium">Prod. (sc/ha)</th>
                        <th className="px-3 py-2 font-medium">Receita/ha</th>
                        <th className="px-3 py-2 font-medium">Lucro/ha</th>
                        <th className="px-3 py-2 font-medium">Margem</th>
                      </tr>
                    </thead>
                    <tbody>
                      {b.margin.scenarios.map((s) => (
                        <tr key={s.name} className="border-t border-border">
                          <td className="px-3 py-2 font-medium">{s.name}</td>
                          <td className="px-3 py-2 tabular-nums">{formatNumber(s.yield_sc_ha)}</td>
                          <td className="px-3 py-2 tabular-nums">{formatBRL(s.revenue)}</td>
                          <td
                            className={
                              "px-3 py-2 font-medium tabular-nums " +
                              (s.profit >= 0 ? "text-green-700" : "text-red-700")
                            }
                          >
                            {formatBRL(s.profit_per_hectare)}
                          </td>
                          <td className="px-3 py-2 tabular-nums">{formatNumber(s.margin_pct)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6 text-sm text-muted-foreground">
                Para projetar a margem, é preciso preço e custo de referência. Rode os
                pipelines de cotação (CEPEA) e custo (CONAB) para popular os artefatos.
              </CardContent>
            </Card>
          )}

          {/* O QUE FAZER E QUANTO VALE (ganho líquido R$/ha) */}
          {b.recommendations && b.recommendations.length > 0 && (
            <Card className="border-green-200">
              <CardHeader>
                <CardTitle>O que fazer e quanto vale (R$/ha líquido)</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="mb-3 text-xs text-muted-foreground">
                  Ações de manejo ordenadas pelo ganho <b>líquido</b> (produtividade ao preço
                  atual, menos o custo de adotar). Estimativa — confirme com seu agrônomo.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                      <tr>
                        <th className="px-3 py-2 font-medium">Líquido</th>
                        <th className="px-3 py-2 font-medium">Ação</th>
                        <th className="px-3 py-2 font-medium">+Produtividade</th>
                        <th className="px-3 py-2 font-medium">Custo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {b.recommendations.map((r) => (
                        <tr key={r.key} className="border-t border-border">
                          <td className="px-3 py-2 font-semibold tabular-nums text-green-700">
                            +{formatBRL(r.net_gain_rs_ha)}/ha
                          </td>
                          <td className="px-3 py-2">
                            {r.question}
                            <span className="block text-xs text-muted-foreground">
                              {r.current_label} → {r.target_label} (+{formatNumber(r.gain_sc_ha)} sc/ha)
                            </span>
                          </td>
                          <td className="px-3 py-2 tabular-nums text-green-700">
                            +{formatBRL(r.yield_gain_rs_ha)}
                          </td>
                          <td className="px-3 py-2 tabular-nums text-muted-foreground">
                            {r.cost_change_rs_ha > 0 ? "+" : ""}
                            {formatBRL(r.cost_change_rs_ha)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          <p className="text-xs italic text-muted-foreground">
            Fontes: {b.data_sources.join(" · ")}. {b.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
}
