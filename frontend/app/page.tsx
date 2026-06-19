"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import {
  api,
  type RegionalIntelligenceRequest,
  type RegionalIntelligenceResponse,
} from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { MunicipalitySelect } from "@/components/municipality-select";
import { ScenarioChart } from "@/components/scenario-chart";
import { HowWeGotHere } from "@/components/how-we-got-here";
import { ErrorBlock, Spinner } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge, severityVariant } from "@/components/ui/badge";
import { Stat } from "@/components/stat";
import { formatNumber, formatDateBR } from "@/lib/utils";

export default function RegionalIntelligencePage() {
  const [municipality, setMunicipality] = React.useState("");
  const [season, setSeason] = React.useState("2026/27");

  const mutation = useMutation<
    RegionalIntelligenceResponse,
    Error,
    RegionalIntelligenceRequest
  >({
    mutationFn: api.regionalIntelligence,
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!municipality) return;
    mutation.mutate({ municipality, uf: "RS", crop: "soja", season });
  };

  const data = mutation.data;

  return (
    <div>
      <PageHeader
        title="Inteligência Regional"
        description="Estimativa de produtividade de soja por município no Rio Grande do Sul, com cenários, riscos climáticos e janela de plantio."
      />

      <Card className="mb-8">
        <CardContent className="pt-6">
          <form
            onSubmit={onSubmit}
            className="grid grid-cols-1 gap-4 md:grid-cols-4 md:items-end"
          >
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="municipality">Município</Label>
              <MunicipalitySelect
                id="municipality"
                value={municipality}
                onChange={setMunicipality}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="crop">Cultura</Label>
              <Input id="crop" value="soja" disabled readOnly />
            </div>
            <div className="space-y-2">
              <Label htmlFor="season">Safra</Label>
              <Input
                id="season"
                value={season}
                onChange={(e) => setSeason(e.target.value)}
                placeholder="2026/27"
              />
            </div>
            <div className="md:col-span-4">
              <Button type="submit" disabled={!municipality || mutation.isPending}>
                {mutation.isPending && <Spinner />}
                Gerar inteligência
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
            <CardContent className="flex flex-col gap-2 pt-6 md:flex-row md:items-end md:justify-between">
              <div>
                <div className="text-sm font-medium text-brand-700">
                  Produtividade esperada — {data.municipality} · safra{" "}
                  {data.season}
                </div>
                <div className="mt-1 text-4xl font-bold tabular-nums text-brand-800">
                  {formatNumber(data.estimated_yield_sc_ha)}{" "}
                  <span className="text-xl font-medium text-brand-700">
                    sc/ha
                  </span>
                </div>
              </div>
              <div className="text-sm text-muted-foreground">
                Intervalo de confiança:{" "}
                <span className="font-medium text-foreground tabular-nums">
                  {formatNumber(data.confidence_interval_sc_ha[0])} –{" "}
                  {formatNumber(data.confidence_interval_sc_ha[1])} sc/ha
                </span>
                <div className="mt-1">Colheita prevista: {data.harvest_year}</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Cenários de produtividade</CardTitle>
            </CardHeader>
            <CardContent>
              <ScenarioChart scenarios={data.scenarios} />
            </CardContent>
          </Card>

          <div>
            <h2 className="mb-3 text-lg font-semibold">Riscos climáticos</h2>
            {data.climatic_risks.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Nenhum risco climático relevante identificado.
              </p>
            ) : (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {data.climatic_risks.map((risk, i) => (
                  <Card key={`${risk.factor}-${i}`}>
                    <CardContent className="pt-6">
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <span className="font-medium">{risk.factor}</span>
                        <Badge variant={severityVariant(risk.severity)}>
                          {risk.severity}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {risk.description}
                      </p>
                      {Object.keys(risk.metric).length > 0 && (
                        <dl className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground">
                          {Object.entries(risk.metric).map(([k, v]) => (
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
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Janela de plantio</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <Stat
                  label="Início"
                  value={formatDateBR(data.planting_window.start)}
                />
                <Stat
                  label="Ótimo (início)"
                  value={formatDateBR(data.planting_window.optimal_start)}
                />
                <Stat
                  label="Ótimo (fim)"
                  value={formatDateBR(data.planting_window.optimal_end)}
                />
                <Stat
                  label="Fim"
                  value={formatDateBR(data.planting_window.end)}
                />
              </div>
              <p className="text-sm text-muted-foreground">
                {data.planting_window.rationale}
              </p>
            </CardContent>
          </Card>

          <div className="rounded-lg border border-brand-100 bg-brand-50 p-5">
            <h3 className="mb-2 text-sm font-semibold text-brand-800">
              Análise
            </h3>
            <p className="whitespace-pre-line text-sm leading-relaxed text-brand-800/90">
              {data.explanation}
            </p>
          </div>

          <HowWeGotHere
            rows={[
              {
                label: "Anos de dados históricos",
                value: data.n_years,
                hint: "IBGE/PAM + clima",
              },
              { label: "Método", value: data.reasoning.method },
              { label: "Base do intervalo", value: data.reasoning.interval_basis },
              {
                label: "Fontes",
                value: data.data_sources.join(", "),
              },
            ]}
          />

          {data.data_sources.length > 0 && (
            <p className="text-xs text-muted-foreground">
              Fontes de dados: {data.data_sources.join(", ")}
            </p>
          )}
          <p className="text-xs text-muted-foreground">{data.disclaimer}</p>
        </div>
      )}
    </div>
  );
}
