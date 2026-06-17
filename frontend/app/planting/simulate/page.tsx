"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import {
  api,
  type PlantingDateSimulationRequest,
  type PlantingDateSimulationResponse,
} from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { MunicipalitySelect } from "@/components/municipality-select";
import { ScenarioChart } from "@/components/scenario-chart";
import { ErrorBlock, Spinner } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Stat } from "@/components/stat";
import { formatNumber, formatDateBR } from "@/lib/utils";

export default function SimulatePage() {
  const [municipality, setMunicipality] = React.useState("");
  const [season, setSeason] = React.useState("2026/27");
  const [plantingDate, setPlantingDate] = React.useState("2026-11-01");
  const [riskAversion, setRiskAversion] = React.useState(0.5);

  const mutation = useMutation<
    PlantingDateSimulationResponse,
    Error,
    PlantingDateSimulationRequest
  >({
    mutationFn: api.plantingDateSimulation,
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!municipality || !plantingDate) return;
    mutation.mutate({
      municipality,
      uf: "RS",
      crop: "soja",
      season,
      planting_date: plantingDate,
      risk_aversion: riskAversion,
    });
  };

  const data = mutation.data;

  return (
    <div>
      <PageHeader
        title="Simular Data de Plantio"
        description="Avalie o desempenho esperado da soja para uma data específica de plantio, com risco e fenologia."
      />

      <Card className="mb-8">
        <CardContent className="pt-6">
          <form
            onSubmit={onSubmit}
            className="grid grid-cols-1 gap-4 md:grid-cols-2"
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
              <Label htmlFor="planting_date">Data de plantio</Label>
              <Input
                id="planting_date"
                type="date"
                value={plantingDate}
                onChange={(e) => setPlantingDate(e.target.value)}
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
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0 — só média</span>
                <span>2 — conservador</span>
              </div>
            </div>
            <div className="md:col-span-2">
              <Button
                type="submit"
                disabled={!municipality || !plantingDate || mutation.isPending}
              >
                {mutation.isPending && <Spinner />}
                Simular
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
          <Card className="border-brand-100 bg-brand-50/40">
            <CardContent className="pt-6">
              <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                <div>
                  <div className="text-sm font-medium text-brand-700">
                    Produtividade esperada — plantio em{" "}
                    {formatDateBR(data.evaluated_planting_date)}
                  </div>
                  <div className="mt-1 text-4xl font-bold tabular-nums text-brand-800">
                    {formatNumber(data.expected_yield_sc_ha)}{" "}
                    <span className="text-xl font-medium text-brand-700">
                      sc/ha
                    </span>
                  </div>
                  <div className="mt-1 text-sm text-muted-foreground">
                    IC: {formatNumber(data.confidence_interval_sc_ha[0])} –{" "}
                    {formatNumber(data.confidence_interval_sc_ha[1])} sc/ha
                  </div>
                </div>
                <div className="flex flex-col items-start gap-2 md:items-end">
                  <Badge variant={data.within_zarc ? "success" : "danger"}>
                    {data.within_zarc
                      ? "Dentro do ZARC"
                      : "Fora do ZARC"}
                  </Badge>
                  <div
                    className={
                      "text-sm font-medium tabular-nums " +
                      (data.delta_vs_baseline_sc_ha >= 0
                        ? "text-green-700"
                        : "text-red-700")
                    }
                  >
                    {data.delta_vs_baseline_sc_ha >= 0 ? "+" : ""}
                    {formatNumber(data.delta_vs_baseline_sc_ha)} sc/ha vs.
                    referência
                  </div>
                </div>
              </div>
              {data.snapped_note && (
                <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800">
                  {data.snapped_note}
                </p>
              )}
            </CardContent>
          </Card>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Stat
              label="Downside (P10)"
              value={formatNumber(data.downside_sc_ha)}
              unit="sc/ha"
            />
            <Stat
              label="Estabilidade (IQR)"
              value={formatNumber(data.stability_iqr_sc_ha)}
              unit="sc/ha"
            />
            <Stat
              label="Score de risco"
              value={formatNumber(data.risk_score, 2)}
            />
            <Stat label="Anos simulados" value={String(data.n_years)} />
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Fenologia</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <div className="flex-1 rounded-lg border border-border bg-muted/40 px-4 py-3 text-center">
                    <div className="text-xs uppercase text-muted-foreground">
                      R1 · floração
                    </div>
                    <div className="mt-1 font-semibold">
                      {formatDateBR(data.phenology.r1_begin_flowering)}
                    </div>
                  </div>
                  <span className="text-muted-foreground">→</span>
                  <div className="flex-1 rounded-lg border border-border bg-muted/40 px-4 py-3 text-center">
                    <div className="text-xs uppercase text-muted-foreground">
                      R6 · grão cheio
                    </div>
                    <div className="mt-1 font-semibold">
                      {formatDateBR(data.phenology.r6_full_seed)}
                    </div>
                  </div>
                </div>
                {Object.keys(data.risk_drivers).length > 0 && (
                  <div className="mt-4">
                    <div className="mb-1 text-xs font-medium uppercase text-muted-foreground">
                      Direcionadores de risco
                    </div>
                    <dl className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground">
                      {Object.entries(data.risk_drivers).map(([k, v]) => (
                        <div key={k}>
                          <dt className="inline font-medium text-foreground">
                            {k}:
                          </dt>{" "}
                          <dd className="inline tabular-nums">
                            {formatNumber(v)}
                          </dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cenários</CardTitle>
              </CardHeader>
              <CardContent>
                <ScenarioChart scenarios={data.scenarios} />
              </CardContent>
            </Card>
          </div>

          <div className="rounded-lg border border-brand-100 bg-brand-50 p-5">
            <h3 className="mb-2 text-sm font-semibold text-brand-800">
              Análise
            </h3>
            <p className="whitespace-pre-line text-sm leading-relaxed text-brand-800/90">
              {data.explanation}
            </p>
          </div>

          <p className="text-xs italic text-muted-foreground">
            {data.scope_note}
          </p>
        </div>
      )}
    </div>
  );
}
