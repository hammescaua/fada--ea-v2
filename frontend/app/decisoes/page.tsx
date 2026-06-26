"use client";

import * as React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  api,
  type Decisions,
  type DecisionCards,
  type Farm,
  type Field,
} from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { ErrorBlock, LoadingBlock } from "@/components/states";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { EvidenceRows } from "@/components/how-we-got-here";
import { DecisionCardItem } from "@/components/decision-card";
import { formatNumber } from "@/lib/utils";

function levelVariant(level: string): BadgeProps["variant"] {
  if (level === "alta") return "danger";
  if (level === "média") return "warning";
  return "success";
}

function levelBorder(level: string): string {
  if (level === "alta") return "border-l-4 border-l-red-500";
  if (level === "média") return "border-l-4 border-l-amber-500";
  return "border-l-4 border-l-green-500";
}

const RANKING_LABELS: Record<string, string> = {
  custo_por_hectare: "Maior custo por hectare (R$/ha)",
  distancia_da_meta_pct: "Mais distante da meta (%)",
  pct_orcamento_consumido: "Mais orçamento consumido (%)",
  desvio_vs_regiao_pct: "Mais abaixo da região (%)",
};

export default function DecisoesPage() {
  const [farmId, setFarmId] = React.useState<number | null>(null);
  const farmsQuery = useQuery({ queryKey: ["farms"], queryFn: api.getFarms });

  React.useEffect(() => {
    if (farmId === null && farmsQuery.data && farmsQuery.data.length > 0) {
      setFarmId(farmsQuery.data[0].id);
    }
  }, [farmsQuery.data, farmId]);

  const [fieldId, setFieldId] = React.useState<number | null>(null);
  const fieldsQuery = useQuery<Field[]>({
    queryKey: ["fields", farmId],
    queryFn: () => api.getFields(farmId as number),
    enabled: farmId !== null,
  });

  const query = useQuery<Decisions>({
    queryKey: ["decisions", farmId],
    queryFn: () => api.getDecisions(farmId as number),
    enabled: farmId !== null,
  });

  const cardsQuery = useQuery<DecisionCards>({
    queryKey: ["decision-cards", farmId, fieldId],
    queryFn: () => api.getDecisionCards(farmId as number, fieldId ?? undefined),
    enabled: farmId !== null,
    retry: false,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Decisões — onde olhar e o que está em jogo"
        description="O hub de decisão: clima (proativo), manejo (efeito em R$/ha) e histórico, no mesmo formato. Cada efeito vem com intervalo; previsão e estimativas nunca como certeza."
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
              </Link>
              .
            </p>
          ) : (
            <div className="grid max-w-xl grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="farm">Fazenda</Label>
                <Select
                  id="farm"
                  value={farmId ?? ""}
                  onChange={(e) => {
                    setFarmId(Number(e.target.value));
                    setFieldId(null);
                  }}
                >
                  {farmsQuery.data.map((f: Farm) => (
                    <option key={f.id} value={f.id}>
                      {f.name}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="field">Talhão (habilita cartões de manejo)</Label>
                <Select
                  id="field"
                  value={fieldId ?? ""}
                  onChange={(e) => setFieldId(e.target.value ? Number(e.target.value) : null)}
                >
                  <option value="">— todos / só clima e histórico —</option>
                  {(fieldsQuery.data ?? []).map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* HUB: cartões de decisão unificados */}
      {farmId !== null && cardsQuery.data && cardsQuery.data.cards.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Cartões de decisão {fieldId === null && "(selecione um talhão para ver o manejo em R$/ha)"}
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {cardsQuery.data.cards.map((c) => (
              <DecisionCardItem key={c.id} card={c} />
            ))}
          </div>
        </div>
      )}

      {farmId !== null && (
        <>
          {query.isLoading ? (
            <LoadingBlock label="Avaliando talhões…" />
          ) : query.isError ? (
            <ErrorBlock error={query.error} />
          ) : !query.data || query.data.n_fields === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">
                  Nenhum talhão com safra registrada. Registre safras e operações para
                  receber a priorização de atenção.
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Heatmap de atenção */}
              <div className="grid gap-4 md:grid-cols-2">
                {query.data.fields.map((f) => (
                  <Card key={f.field_id} className={levelBorder(f.attention_level)}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0">
                      <CardTitle className="text-base">{f.field_name}</CardTitle>
                      <Badge variant={levelVariant(f.attention_level)}>
                        atenção {f.attention_level}
                      </Badge>
                    </CardHeader>
                    <CardContent>
                      {f.flags.length === 0 ? (
                        <p className="text-sm text-muted-foreground">
                          Sem alertas com os dados atuais.
                        </p>
                      ) : (
                        <ul className="space-y-3">
                          {f.flags.map((fl, idx) => (
                            <li key={idx} className="text-sm">
                              <div className="flex items-center gap-2">
                                <Badge variant={levelVariant(fl.severity)}>
                                  {fl.severity}
                                </Badge>
                                <span className="font-medium">{fl.title}</span>
                                <span className="text-xs text-muted-foreground">
                                  · confiança {fl.confidence}
                                </span>
                              </div>
                              <p className="mt-1 text-muted-foreground">{fl.detail}</p>
                              {fl.evidence && Object.keys(fl.evidence).length > 0 && (
                                <details className="mt-1">
                                  <summary className="cursor-pointer text-xs text-brand-700">
                                    Ver dados
                                  </summary>
                                  <div className="mt-1 rounded-md bg-muted/50 px-3 py-2">
                                    <EvidenceRows evidence={fl.evidence} />
                                  </div>
                                </details>
                              )}
                            </li>
                          ))}
                        </ul>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Rankings multi-critério */}
              <Card>
                <CardHeader>
                  <CardTitle>Rankings (uma dimensão por vez)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-6 sm:grid-cols-2">
                    {Object.entries(query.data.rankings).map(([key, items]) => (
                      <div key={key}>
                        <h3 className="mb-2 text-sm font-medium">
                          {RANKING_LABELS[key] ?? key}
                        </h3>
                        {items.length === 0 ? (
                          <p className="text-xs text-muted-foreground">Sem dados.</p>
                        ) : (
                          <ol className="space-y-1 text-sm">
                            {items.map((it, idx) => (
                              <li
                                key={it.field_id}
                                className="flex justify-between tabular-nums"
                              >
                                <span>
                                  {idx + 1}. {it.field_name}
                                </span>
                                <span className="text-muted-foreground">
                                  {formatNumber(it.value)}
                                </span>
                              </li>
                            ))}
                          </ol>
                        )}
                      </div>
                    ))}
                  </div>
                  <p className="mt-4 text-xs text-muted-foreground">{query.data.note}</p>
                </CardContent>
              </Card>
            </>
          )}
        </>
      )}
    </div>
  );
}
