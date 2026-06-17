"use client";

import * as React from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ApiError,
  api,
  type Farm,
  type FarmProfile,
  type PersonalizedIntelligence,
} from "@/lib/api";
import {
  ActualVsFittedChart,
  ResidualPctChart,
} from "@/components/adaptive-charts";
import { PageHeader } from "@/components/page-header";
import { ErrorBlock, LoadingBlock, Spinner } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { formatNumber, formatDateBR } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function adaptationVariant(level: string): BadgeProps["variant"] {
  switch (level.toLowerCase()) {
    case "alta":
      return "success";
    case "moderada":
      return "default"; // brand (blue-ish) tone
    case "baixa":
      return "warning";
    default:
      return "secondary";
  }
}

function pctLabel(value: number, digits = 1): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumber(value, digits)}%`;
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

function isNotFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

// ---------------------------------------------------------------------------
// Prediction comparison
// ---------------------------------------------------------------------------

function PredictionCard({
  title,
  highlight,
  point,
  interval,
}: {
  title: string;
  highlight?: boolean;
  point: number;
  interval: [number, number];
}) {
  const width = interval[1] - interval[0];
  return (
    <div
      className={
        "flex-1 rounded-lg border p-5 " +
        (highlight
          ? "border-brand-200 bg-brand-50"
          : "border-border bg-muted/20")
      }
    >
      <div className="text-sm font-medium text-muted-foreground">{title}</div>
      <div className="mt-1 text-3xl font-semibold tabular-nums text-foreground">
        {formatNumber(point)}{" "}
        <span className="text-base font-normal text-muted-foreground">
          sc/ha
        </span>
      </div>
      <div className="mt-2 text-sm text-muted-foreground">
        Intervalo:{" "}
        <span className="font-medium text-foreground tabular-nums">
          [{formatNumber(interval[0])} – {formatNumber(interval[1])}]
        </span>{" "}
        sc/ha
      </div>
      <div className="mt-1 text-xs text-muted-foreground">
        Largura do intervalo:{" "}
        <span className="tabular-nums">{formatNumber(width)} sc/ha</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AdaptivePage() {
  const qc = useQueryClient();

  const farmsQuery = useQuery<Farm[]>({
    queryKey: ["farms"],
    queryFn: () => api.getFarms(),
  });

  const [farmId, setFarmId] = React.useState<number | null>(null);
  const [season, setSeason] = React.useState("2026/27");

  // Default the selected farm to the first one once farms load.
  React.useEffect(() => {
    if (farmId === null && farmsQuery.data && farmsQuery.data.length > 0) {
      setFarmId(farmsQuery.data[0].id);
    }
  }, [farmsQuery.data, farmId]);

  const profileQuery = useQuery<FarmProfile>({
    queryKey: ["farm-profile", farmId],
    queryFn: () => api.getFarmProfile(farmId as number),
    enabled: farmId !== null,
    retry: (failureCount, error) => {
      if (isNotFound(error)) return false; // don't retry "not computed yet"
      return failureCount < 2;
    },
  });

  const recompute = useMutation<FarmProfile>({
    mutationFn: () => api.recomputeFarmProfile(farmId as number),
    onSuccess: (data) => {
      qc.setQueryData(["farm-profile", farmId], data);
      qc.invalidateQueries({ queryKey: ["farm-profile", farmId] });
    },
  });

  const intelligence = useMutation<PersonalizedIntelligence>({
    mutationFn: () =>
      api.personalizedIntelligence({
        farm_id: farmId as number,
        season,
      }),
  });

  const profile = profileQuery.data;
  const intel = intelligence.data;

  const noProfile = profileQuery.isError && isNotFound(profileQuery.error);

  return (
    <div>
      <PageHeader
        title="Inteligência Adaptativa"
        description="Combina a previsão regional com o histórico real da fazenda para gerar uma previsão personalizada — e mostra o quanto a fazenda se desvia da média regional."
      />

      {/* INPUTS */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Parâmetros</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3 md:items-end">
            <div className="space-y-2">
              <Label htmlFor="farm">Fazenda</Label>
              {farmsQuery.isLoading ? (
                <LoadingBlock label="Carregando fazendas..." />
              ) : farmsQuery.isError ? (
                <ErrorBlock error={farmsQuery.error} />
              ) : farmsQuery.data && farmsQuery.data.length > 0 ? (
                <Select
                  id="farm"
                  value={farmId ?? ""}
                  onChange={(e) => {
                    setFarmId(Number(e.target.value));
                    intelligence.reset();
                    recompute.reset();
                  }}
                >
                  {farmsQuery.data.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name} (#{f.id})
                    </option>
                  ))}
                </Select>
              ) : (
                <div className="space-y-2">
                  <Input
                    id="farm"
                    type="number"
                    min="1"
                    placeholder="ID da fazenda"
                    value={farmId ?? ""}
                    onChange={(e) =>
                      setFarmId(e.target.value ? Number(e.target.value) : null)
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    Nenhuma fazenda cadastrada. Crie uma em{" "}
                    <Link
                      href="/farms"
                      className="font-medium text-brand-700 underline"
                    >
                      Captura de Dados
                    </Link>
                    .
                  </p>
                </div>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="season">Safra</Label>
              <Input
                id="season"
                value={season}
                onChange={(e) => setSeason(e.target.value)}
                placeholder="Ex.: 2026/27"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                disabled={farmId === null || recompute.isPending}
                onClick={() => recompute.mutate()}
              >
                {recompute.isPending && <Spinner />}
                Recalcular perfil
              </Button>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            O perfil exige fazendas com produtividades reais registradas. Cadastre
            os dados de safra em{" "}
            <Link
              href="/safra"
              className="font-medium text-brand-700 underline"
            >
              Safra
            </Link>
            .
          </p>
          {recompute.isError && <ErrorBlock error={recompute.error} />}
        </CardContent>
      </Card>

      {farmId === null ? (
        <p className="text-sm text-muted-foreground">
          Selecione uma fazenda para começar.
        </p>
      ) : (
        <div className="space-y-6">
          {/* PROFILE STATUS */}
          {profileQuery.isLoading && (
            <LoadingBlock label="Carregando perfil de desempenho..." />
          )}

          {noProfile && (
            <Card>
              <CardContent className="space-y-3 pt-6">
                <p className="text-sm text-foreground">
                  Esta fazenda ainda não possui um perfil de desempenho
                  calculado.
                </p>
                <p className="text-sm text-muted-foreground">
                  Clique em{" "}
                  <span className="font-medium">Recalcular perfil</span> acima
                  para computá-lo. É necessário que a fazenda tenha safras com
                  produtividades reais registradas em{" "}
                  <Link
                    href="/safra"
                    className="font-medium text-brand-700 underline"
                  >
                    Safra
                  </Link>
                  .
                </p>
                <Button
                  disabled={recompute.isPending}
                  onClick={() => recompute.mutate()}
                >
                  {recompute.isPending && <Spinner />}
                  Recalcular perfil
                </Button>
              </CardContent>
            </Card>
          )}

          {profileQuery.isError && !noProfile && (
            <ErrorBlock error={profileQuery.error} />
          )}

          {profile && (
            <>
              {/* DEVIATION FROM REGIONAL MEAN */}
              <Card>
                <CardHeader>
                  <CardTitle>
                    Quanto a fazenda se desvia da média regional
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap items-baseline gap-3">
                    <span
                      className={
                        "text-4xl font-bold tabular-nums " +
                        (profile.bias_percentage >= 0
                          ? "text-green-700"
                          : "text-red-700")
                      }
                    >
                      {pctLabel(profile.bias_percentage)}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {profile.bias_percentage >= 0
                        ? "acima da média regional (em média)"
                        : "abaixo da média regional (em média)"}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                    <Stat
                      label="Safras utilizadas"
                      value={profile.number_of_cycles}
                    />
                    <Stat
                      label="Resíduo médio"
                      value={`${formatNumber(
                        profile.mean_residual_sc_ha
                      )} sc/ha`}
                      hint={`Mediana: ${formatNumber(
                        profile.median_residual_sc_ha
                      )} sc/ha`}
                    />
                    <Stat
                      label="Resíduo relativo médio"
                      value={pctLabel(profile.mean_relative_residual)}
                    />
                    <Stat
                      label="Variância relativa"
                      value={formatNumber(profile.variance_relative, 3)}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Última atualização: {formatDateBR(profile.last_updated)}
                  </p>
                </CardContent>
              </Card>

              {/* RESIDUAL EVOLUTION CHART */}
              <Card>
                <CardHeader>
                  <CardTitle>Evolução do desvio (resíduos)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-8">
                  <div>
                    <h3 className="mb-2 text-sm font-medium text-foreground">
                      Desvio relativo por safra (%)
                    </h3>
                    <ResidualPctChart history={profile.residual_history} />
                    <p className="mt-1 text-xs text-muted-foreground">
                      Verde = acima do ajuste regional · Vermelho = abaixo. A
                      linha em zero marca o desempenho regional esperado.
                    </p>
                  </div>
                  <div>
                    <h3 className="mb-2 text-sm font-medium text-foreground">
                      Produtividade real vs. ajuste regional (sc/ha)
                    </h3>
                    <ActualVsFittedChart history={profile.residual_history} />
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {/* PERSONALIZED PREDICTION */}
          <Card>
            <CardHeader>
              <CardTitle>Previsão personalizada</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                <div className="flex-1 space-y-2">
                  <Label htmlFor="season2">Safra</Label>
                  <Input
                    id="season2"
                    value={season}
                    onChange={(e) => setSeason(e.target.value)}
                    placeholder="Ex.: 2026/27"
                  />
                </div>
                <Button
                  disabled={farmId === null || !season || intelligence.isPending}
                  onClick={() => intelligence.mutate()}
                >
                  {intelligence.isPending && <Spinner />}
                  Gerar previsão
                </Button>
              </div>

              {intelligence.isError && (
                <ErrorBlock error={intelligence.error} />
              )}

              {intel && (
                <>
                  {/* COMPARISON */}
                  <div>
                    <h3 className="mb-2 text-sm font-medium text-foreground">
                      Regional vs. Personalizada — safra {intel.season} (colheita{" "}
                      {intel.harvest_year})
                    </h3>
                    <div className="flex flex-col gap-4 md:flex-row">
                      <PredictionCard
                        title="Previsão Regional"
                        point={intel.regional_prediction.point_sc_ha}
                        interval={intel.regional_prediction.interval_sc_ha}
                      />
                      <PredictionCard
                        title="Previsão Personalizada"
                        highlight
                        point={intel.personalized_prediction.point_sc_ha}
                        interval={intel.personalized_prediction.interval_sc_ha}
                      />
                    </div>
                    <p className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                      Nota científica: a personalização ajusta o valor central
                      conforme o histórico da fazenda, mas o intervalo
                      personalizado <strong>não é mais estreito</strong> que o
                      regional — a incerteza não diminui ao personalizar.
                    </p>
                  </div>

                  {/* ADJUSTMENT */}
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                    <div className="rounded-lg border border-border bg-muted/30 p-4">
                      <div className="text-xs uppercase tracking-wide text-muted-foreground">
                        Ajuste aplicado
                      </div>
                      <div className="mt-2">
                        <Badge
                          variant={
                            intel.farm_adjustment.applied_pct > 0
                              ? "success"
                              : intel.farm_adjustment.applied_pct < 0
                                ? "danger"
                                : "secondary"
                          }
                        >
                          {pctLabel(intel.farm_adjustment.applied_pct)}
                        </Badge>
                      </div>
                    </div>
                    <Stat
                      label="Desvio observado"
                      value={pctLabel(intel.farm_adjustment.observed_bias_pct)}
                    />
                    <Stat
                      label="Safras utilizadas"
                      value={intel.farm_adjustment.n_cycles}
                    />
                  </div>

                  {/* CONFIDENCE */}
                  <div className="rounded-lg border border-border bg-muted/20 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="text-sm font-medium text-foreground">
                        Confiança da personalização
                      </div>
                      <Badge variant={adaptationVariant(intel.adaptation_level)}>
                        Adaptação: {intel.adaptation_level}
                      </Badge>
                    </div>
                    <div className="mt-3 flex items-center gap-3">
                      <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-brand-600 transition-all"
                          style={{
                            width: `${Math.max(
                              0,
                              Math.min(100, intel.confidence_score * 100)
                            )}%`,
                          }}
                        />
                      </div>
                      <span className="text-sm font-semibold tabular-nums text-foreground">
                        {formatNumber(intel.confidence_score * 100, 0)}%
                      </span>
                    </div>
                  </div>

                  {/* SCENARIOS */}
                  {intel.personalized_prediction.scenarios.length > 0 && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                          <tr>
                            <th className="px-3 py-2 font-medium">Cenário</th>
                            <th className="px-3 py-2 font-medium">
                              Produtividade (sc/ha)
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {intel.personalized_prediction.scenarios.map((s) => (
                            <tr
                              key={s.name}
                              className="border-t border-border"
                            >
                              <td className="px-3 py-2 font-medium">
                                {s.name}
                              </td>
                              <td className="px-3 py-2 tabular-nums">
                                {formatNumber(s.yield_sc_ha)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* EXPLANATION */}
                  {intel.explanation && (
                    <div className="rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-foreground">
                      {intel.explanation}
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
