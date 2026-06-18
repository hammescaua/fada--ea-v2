"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { ApiError, api, type Calibration, type CalibrationReport } from "@/lib/api";
import {
  AccuracyComparisonChart,
  IntervalWidthChart,
  ReliabilityChart,
} from "@/components/calibration-charts";
import { PageHeader } from "@/components/page-header";
import { ErrorBlock, LoadingBlock } from "@/components/states";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { formatNumber } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Coverage / observed values arrive as fractions in 0..1. */
function pct(value: number, digits = 1): string {
  return `${formatNumber(value * 100, digits)}%`;
}

function calibrationBadge(report: CalibrationReport): {
  variant: BadgeProps["variant"];
  label: string;
} {
  if (report.overconfident)
    return { variant: "danger", label: "Superconfiante" };
  if (report.underconfident)
    return { variant: "warning", label: "Subconfiante" };
  return { variant: "success", label: "Calibrado" };
}

function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
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

function InterpretationBox({
  report,
}: {
  report: CalibrationReport;
}) {
  const badge = calibrationBadge(report);
  return (
    <div className="rounded-lg border border-brand-200 bg-brand-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-semibold text-foreground">
          {report.label}
        </div>
        <Badge variant={badge.variant}>{badge.label}</Badge>
      </div>
      <p className="mt-2 text-sm text-foreground">{report.interpretation}</p>
      <p className="mt-2 text-xs text-muted-foreground">
        {report.n_predictions} previsões avaliadas
      </p>
    </div>
  );
}

function isUnavailable(error: unknown): boolean {
  return error instanceof ApiError && error.status === 503;
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function CalibrationPage() {
  const [showPersonalized, setShowPersonalized] = React.useState(true);

  const query = useQuery<Calibration>({
    queryKey: ["calibration"],
    queryFn: () => api.getCalibration(),
    retry: (failureCount, error) => {
      if (isUnavailable(error)) return false; // artifact missing — don't retry
      return failureCount < 2;
    },
  });

  const data = query.data;

  return (
    <div>
      <PageHeader
        title="Calibração"
        description="Backtest dos preditores regional e personalizado: as previsões são honestas? Avaliamos cobertura dos intervalos, acurácia (MAE/RMSE) e regras de pontuação próprias (pinball) contra a verdade-terreno."
      />

      {query.isLoading && (
        <LoadingBlock label="Carregando relatório de calibração..." />
      )}

      {query.isError && isUnavailable(query.error) && (
        <Card>
          <CardContent className="space-y-3 pt-6">
            <p className="text-sm text-foreground">
              O artefato de calibração ainda não foi gerado.
            </p>
            <p className="text-sm text-muted-foreground">
              Execute o backtest no backend para produzir o relatório de
              calibração e, em seguida, recarregue esta página.
            </p>
            {query.error instanceof ApiError && (
              <p className="text-xs text-muted-foreground">
                Detalhe da API: {query.error.message}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {query.isError && !isUnavailable(query.error) && (
        <ErrorBlock error={query.error} />
      )}

      {data && (
        <div className="space-y-6">
          {/* INTERPRETATION */}
          <Card>
            <CardHeader>
              <CardTitle>Veredito de calibração</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <InterpretationBox report={data.regional} />
                <InterpretationBox report={data.personalized} />
              </div>
              <p className="text-xs text-muted-foreground">
                Método: {data.method} · Verdade-terreno: {data.ground_truth}
              </p>
            </CardContent>
          </Card>

          {/* REGIONAL COVERAGE / ACCURACY CARDS */}
          <Card>
            <CardHeader>
              <CardTitle>Resumo — preditor regional</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Stat
                  label="Cobertura 80%"
                  value={pct(data.regional.coverage_80)}
                  hint="IC80 deveria cobrir ~80%"
                />
                <Stat
                  label="Cobertura 90%"
                  value={pct(data.regional.coverage_90)}
                  hint="IC90 deveria cobrir ~90%"
                />
                <Stat
                  label="MAE"
                  value={`${formatNumber(data.regional.mae)} sc/ha`}
                  hint="Erro absoluto médio"
                />
                <Stat
                  label="RMSE"
                  value={`${formatNumber(data.regional.rmse)} sc/ha`}
                  hint="Raiz do erro quadrático médio"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Uma cobertura observada próxima do nominal indica intervalos
                honestos. Coberturas muito abaixo do nominal indicam
                superconfiança (intervalos estreitos demais).
              </p>
            </CardContent>
          </Card>

          {/* RELIABILITY DIAGRAM */}
          <Card>
            <CardHeader>
              <CardTitle>Diagrama de confiabilidade</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <label className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  checked={showPersonalized}
                  onChange={(e) => setShowPersonalized(e.target.checked)}
                  className="h-4 w-4 rounded border-border accent-brand-600"
                />
                Mostrar curva personalizada
              </label>
              <ReliabilityChart
                regional={data.regional.reliability_curve}
                personalized={data.personalized.reliability_curve}
                showPersonalized={showPersonalized}
              />
              <p className="text-xs text-muted-foreground">
                Cobertura observada (eixo y) versus nominal (eixo x). A diagonal
                tracejada é a calibração perfeita (y = x). Pontos{" "}
                <strong>acima</strong> da diagonal indicam intervalos
                conservadores (subconfiança); <strong>abaixo</strong>, intervalos
                estreitos demais (superconfiança). A banda cinza é o intervalo de
                Wilson da cobertura observada (regional).
              </p>
            </CardContent>
          </Card>

          {/* INTERVAL WIDTH COMPARISON */}
          <Card>
            <CardHeader>
              <CardTitle>Largura média do intervalo</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <IntervalWidthChart
                regional={data.regional}
                personalized={data.personalized}
              />
              <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                A personalização não estreita o intervalo — a incerteza climática
                é irredutível. O preditor personalizado ajusta o valor central
                conforme o histórico da fazenda, mas a largura do intervalo
                permanece comparável à regional.
              </p>
            </CardContent>
          </Card>

          {/* ACCURACY COMPARISON */}
          <Card>
            <CardHeader>
              <CardTitle>Regional vs. Personalizada — acurácia</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <AccuracyComparisonChart
                regional={data.regional}
                personalized={data.personalized}
              />
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2 font-medium">Métrica</th>
                      <th className="px-3 py-2 font-medium">Regional</th>
                      <th className="px-3 py-2 font-medium">Personalizada</th>
                      <th className="px-3 py-2 font-medium">Melhor</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(
                      [
                        ["MAE", data.regional.mae, data.personalized.mae],
                        ["RMSE", data.regional.rmse, data.personalized.rmse],
                        [
                          "Pinball (média)",
                          data.regional.pinball.mean ?? 0,
                          data.personalized.pinball.mean ?? 0,
                        ],
                      ] as const
                    ).map(([metric, reg, pers]) => {
                      const persWins = pers < reg;
                      return (
                        <tr key={metric} className="border-t border-border">
                          <td className="px-3 py-2 font-medium">{metric}</td>
                          <td className="px-3 py-2 tabular-nums">
                            {formatNumber(reg, 2)}
                          </td>
                          <td className="px-3 py-2 tabular-nums">
                            {formatNumber(pers, 2)}
                          </td>
                          <td className="px-3 py-2">
                            <Badge
                              variant={persWins ? "success" : "secondary"}
                            >
                              {persWins ? "Personalizada" : "Regional"}
                            </Badge>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-muted-foreground">
                Menor é melhor. O pinball loss é uma regra de pontuação própria
                (proper scoring rule) para previsões probabilísticas: penaliza
                conjuntamente o viés e a calibração dos quantis, então não é
                possível &quot;enganá-la&quot; com intervalos arbitrariamente
                largos ou estreitos. A personalização deve vencer em MAE e
                pinball ao corrigir o viés específico da fazenda.
              </p>
            </CardContent>
          </Card>

          {/* NOTE / DISCLAIMER */}
          {data.note && (
            <p className="text-xs text-muted-foreground">{data.note}</p>
          )}
        </div>
      )}
    </div>
  );
}
