"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import {
  api,
  type PlantingWindowOptimizationRequest,
  type PlantingWindowOptimizationResponse,
  type PlantingRecommendation,
  type Scenario,
} from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { MunicipalitySelect } from "@/components/municipality-select";
import { ErrorBlock, Spinner } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Stat } from "@/components/stat";
import { formatNumber, formatDateBR } from "@/lib/utils";

function upsideFromScenarios(scenarios: Scenario[]): number | null {
  const otimista = scenarios.find((s) => s.name.toLowerCase() === "otimista");
  return otimista ? otimista.yield_sc_ha : null;
}

function dominantRisk(rec: PlantingRecommendation): number | null {
  const v = rec.risk_drivers["deficit_reprodutivo_mediano_mm"];
  return typeof v === "number" ? v : null;
}

export default function OptimizePage() {
  const [municipality, setMunicipality] = React.useState("");
  const [season, setSeason] = React.useState("2026/27");
  const [riskAversion, setRiskAversion] = React.useState(0.5);

  const mutation = useMutation<
    PlantingWindowOptimizationResponse,
    Error,
    PlantingWindowOptimizationRequest
  >({
    mutationFn: api.plantingWindowOptimization,
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!municipality) return;
    mutation.mutate({
      municipality,
      uf: "RS",
      crop: "soja",
      season,
      risk_aversion: riskAversion,
      top_n: 5,
    });
  };

  const data = mutation.data;

  return (
    <div>
      <PageHeader
        title="Otimizar Janela de Plantio"
        description="Ranqueamento das melhores datas de plantio de soja por produtividade ajustada ao risco."
      />

      <Card className="mb-8">
        <CardContent className="pt-6">
          <form
            onSubmit={onSubmit}
            className="grid grid-cols-1 gap-4 md:grid-cols-3 md:items-end"
          >
            <div className="space-y-2">
              <Label htmlFor="municipality">Município</Label>
              <MunicipalitySelect
                id="municipality"
                value={municipality}
                onChange={setMunicipality}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="season">Safra</Label>
              <Input
                id="season"
                value={season}
                onChange={(e) => setSeason(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="risk">Aversão ao risco</Label>
                <span className="text-sm tabular-nums text-muted-foreground">
                  {riskAversion.toFixed(1)}
                </span>
              </div>
              <Slider
                id="risk"
                value={riskAversion}
                onChange={setRiskAversion}
                min={0}
                max={2}
                step={0.1}
              />
            </div>
            <div className="md:col-span-3">
              <Button type="submit" disabled={!municipality || mutation.isPending}>
                {mutation.isPending && <Spinner />}
                Otimizar janela
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {mutation.isError && (
        <div className="mb-6">
          <ErrorBlock error={mutation.error} />
        </div>
      )}

      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <Stat
              label="Produtividade de referência"
              value={formatNumber(data.baseline_expected_sc_ha)}
              unit="sc/ha"
            />
            <Stat label="Janela ZARC" value={data.zarc_window} />
            <Stat label="Aversão ao risco" value={data.risk_aversion.toFixed(1)} />
          </div>

          <div className="rounded-lg border border-brand-100 bg-brand-50 p-4 text-sm text-brand-800">
            <span className="font-semibold">Objetivo: </span>
            {data.objective}
          </div>

          <div>
            <h2 className="mb-3 text-lg font-semibold">
              Top {data.top_recommendations.length} recomendações
            </h2>

            {/* Desktop table */}
            <div className="hidden overflow-x-auto rounded-lg border border-border md:block">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">#</th>
                    <th className="px-3 py-2 font-medium">Plantio</th>
                    <th className="px-3 py-2 font-medium">Risco</th>
                    <th className="px-3 py-2 font-medium">Esperado</th>
                    <th className="px-3 py-2 font-medium">Downside (P10)</th>
                    <th className="px-3 py-2 font-medium">Upside (P90)</th>
                    <th className="px-3 py-2 font-medium">Estab. (IQR)</th>
                    <th className="px-3 py-2 font-medium">Déficit rep. (mm)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_recommendations.map((rec, i) => {
                    const upside = upsideFromScenarios(rec.scenarios);
                    const deficit = dominantRisk(rec);
                    return (
                      <tr
                        key={rec.planting_date}
                        className="border-t border-border"
                      >
                        <td className="px-3 py-2 font-semibold">{i + 1}</td>
                        <td className="px-3 py-2 font-medium">
                          {formatDateBR(rec.planting_date)}
                        </td>
                        <td className="px-3 py-2 tabular-nums">
                          {formatNumber(rec.risk_score, 2)}
                        </td>
                        <td className="px-3 py-2 tabular-nums font-medium text-brand-700">
                          {formatNumber(rec.expected_yield_sc_ha)}
                        </td>
                        <td className="px-3 py-2 tabular-nums">
                          {formatNumber(rec.downside_sc_ha)}
                        </td>
                        <td className="px-3 py-2 tabular-nums">
                          {upside === null ? "—" : formatNumber(upside)}
                        </td>
                        <td className="px-3 py-2 tabular-nums">
                          {formatNumber(rec.stability_iqr_sc_ha)}
                        </td>
                        <td className="px-3 py-2 tabular-nums">
                          {deficit === null ? "—" : formatNumber(deficit)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="space-y-4 md:hidden">
              {data.top_recommendations.map((rec, i) => {
                const upside = upsideFromScenarios(rec.scenarios);
                const deficit = dominantRisk(rec);
                return (
                  <Card key={rec.planting_date}>
                    <CardContent className="space-y-3 pt-6">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">
                          #{i + 1} · {formatDateBR(rec.planting_date)}
                        </span>
                        <Badge variant="secondary">
                          risco {formatNumber(rec.risk_score, 2)}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-muted-foreground">Esperado: </span>
                          {formatNumber(rec.expected_yield_sc_ha)} sc/ha
                        </div>
                        <div>
                          <span className="text-muted-foreground">P10: </span>
                          {formatNumber(rec.downside_sc_ha)}
                        </div>
                        <div>
                          <span className="text-muted-foreground">P90: </span>
                          {upside === null ? "—" : formatNumber(upside)}
                        </div>
                        <div>
                          <span className="text-muted-foreground">IQR: </span>
                          {formatNumber(rec.stability_iqr_sc_ha)}
                        </div>
                        <div className="col-span-2">
                          <span className="text-muted-foreground">
                            Déficit rep.:{" "}
                          </span>
                          {deficit === null ? "—" : formatNumber(deficit)} mm
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-muted-foreground">
              Justificativas
            </h3>
            {data.top_recommendations.map((rec, i) => (
              <div
                key={rec.planting_date}
                className="rounded-lg border border-border bg-card p-4"
              >
                <div className="mb-1 text-sm font-medium">
                  #{i + 1} · {formatDateBR(rec.planting_date)} ·{" "}
                  R1 {formatDateBR(rec.phenology.r1_begin_flowering)} → R6{" "}
                  {formatDateBR(rec.phenology.r6_full_seed)}
                </div>
                <p className="text-sm text-muted-foreground">
                  {rec.justification}
                </p>
              </div>
            ))}
          </div>

          <p className="text-xs italic text-muted-foreground">
            {data.scope_note}
          </p>
        </div>
      )}
    </div>
  );
}
