"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ApiError,
  api,
  type Agenda,
  type EventType,
  type PlanVsActual,
} from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { ErrorBlock, LoadingBlock } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Stat } from "@/components/stat";
import { EVENT_TYPES, EVENT_TYPE_LABELS } from "@/lib/events";
import { formatBRL, formatNumber } from "@/lib/utils";

function statusVariant(status: string): BadgeProps["variant"] {
  if (status === "concluída") return "success";
  if (status === "atrasada") return "danger";
  return "warning";
}

function typeLabel(t: string): string {
  return EVENT_TYPE_LABELS[t as EventType] ?? t;
}

export default function PlanejamentoPage() {
  const [cycleInput, setCycleInput] = React.useState("");
  const [cycleId, setCycleId] = React.useState<number | null>(null);
  const queryClient = useQueryClient();

  const pvaQuery = useQuery<PlanVsActual>({
    queryKey: ["plan-vs-actual", cycleId],
    queryFn: () => api.getPlanVsActual(cycleId as number),
    enabled: cycleId !== null,
    retry: false,
  });

  const agendaQuery = useQuery<Agenda>({
    queryKey: ["agenda", cycleId],
    queryFn: () => api.getAgenda(cycleId as number),
    enabled: cycleId !== null,
    retry: false,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["plan-vs-actual", cycleId] });
    queryClient.invalidateQueries({ queryKey: ["agenda", cycleId] });
  };

  // Quick-log form
  const [logType, setLogType] = React.useState<EventType>("FUNGICIDE");
  const [logDate, setLogDate] = React.useState("");
  const [logCost, setLogCost] = React.useState("");
  const quickLog = useMutation({
    mutationFn: () =>
      api.quickLog({
        crop_cycle_ids: [cycleId as number],
        event_date: logDate,
        event_type: logType,
        cost: logCost ? Number(logCost) : undefined,
      }),
    onSuccess: invalidate,
  });

  // Planned-event form
  const [planType, setPlanType] = React.useState<EventType>("FUNGICIDE");
  const [planDate, setPlanDate] = React.useState("");
  const [planCost, setPlanCost] = React.useState("");
  const addPlanned = useMutation({
    mutationFn: () =>
      api.createPlannedEvent(cycleId as number, {
        event_type: planType,
        planned_date: planDate,
        expected_cost: planCost ? Number(planCost) : undefined,
      }),
    onSuccess: invalidate,
  });

  const pva = pvaQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Plano & Orçamento"
        description="Acompanhe planejado x realizado e a agenda da safra. O plano é opcional — a captura funciona sem ele."
      />

      <Card>
        <CardContent className="pt-6">
          <form
            className="flex flex-wrap items-end gap-3"
            onSubmit={(e) => {
              e.preventDefault();
              const n = Number(cycleInput);
              setCycleId(Number.isFinite(n) && n > 0 ? n : null);
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="cycle">Safra (crop_cycle_id)</Label>
              <Input
                id="cycle"
                type="number"
                value={cycleInput}
                onChange={(e) => setCycleInput(e.target.value)}
                placeholder="ex.: 1"
                className="w-40"
              />
            </div>
            <Button type="submit">Carregar</Button>
          </form>
        </CardContent>
      </Card>

      {cycleId !== null && (
        <>
          {/* Plano x Realizado */}
          <Card>
            <CardHeader>
              <CardTitle>Plano x Realizado</CardTitle>
            </CardHeader>
            <CardContent>
              {pvaQuery.isLoading ? (
                <LoadingBlock label="Calculando…" />
              ) : pvaQuery.isError ? (
                <ErrorBlock error={pvaQuery.error} />
              ) : pva ? (
                <div className="space-y-4">
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <Stat
                      label="Realizado"
                      value={formatBRL(pva.actual_total_cost)}
                    />
                    <Stat
                      label="Planejado"
                      value={formatBRL(pva.planned_total_cost)}
                    />
                    <Stat
                      label="Falta investir"
                      value={formatBRL(pva.remaining_budget)}
                    />
                    <Stat
                      label="Aplicações"
                      value={`${pva.actual_applications} / ${pva.planned_applications}`}
                    />
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {pva.planned_total_cost > 0 && (
                      <Badge variant={pva.over_budget ? "danger" : "success"}>
                        {pva.over_budget ? "Acima do orçamento" : "Dentro do orçamento"}
                      </Badge>
                    )}
                    {pva.pct_budget_spent !== null && (
                      <Badge variant="secondary">
                        {formatNumber(pva.pct_budget_spent)}% gasto
                      </Badge>
                    )}
                    {pva.expected_profit !== null && (
                      <Badge variant="outline">
                        Lucro esperado {formatBRL(pva.expected_profit)}
                      </Badge>
                    )}
                  </div>
                  <p className="rounded-lg bg-brand-50 px-4 py-3 text-sm text-brand-900">
                    {pva.interpretation}
                  </p>
                </div>
              ) : null}
            </CardContent>
          </Card>

          {/* Agenda */}
          <Card>
            <CardHeader>
              <CardTitle>Agenda</CardTitle>
            </CardHeader>
            <CardContent>
              {agendaQuery.isLoading ? (
                <LoadingBlock label="Carregando…" />
              ) : agendaQuery.isError ? (
                <ErrorBlock error={agendaQuery.error} />
              ) : !agendaQuery.data || agendaQuery.data.items.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Nenhuma operação planejada. Adicione abaixo para montar a agenda.
                </p>
              ) : (
                <ul className="space-y-2">
                  {agendaQuery.data.items.map((i, idx) => (
                    <li
                      key={idx}
                      className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm"
                    >
                      <span>
                        <span className="font-medium">{typeLabel(i.event_type)}</span>{" "}
                        <span className="text-muted-foreground">· {i.planned_date}</span>
                        {i.expected_cost !== null && (
                          <span className="text-muted-foreground">
                            {" "}
                            · {formatBRL(i.expected_cost)}
                          </span>
                        )}
                      </span>
                      <Badge variant={statusVariant(i.status)}>{i.status}</Badge>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          {/* Ações: registrar operação + planejar */}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Registrar operação (rápido)</CardTitle>
              </CardHeader>
              <CardContent>
                <form
                  className="space-y-3"
                  onSubmit={(e) => {
                    e.preventDefault();
                    quickLog.mutate();
                  }}
                >
                  <div className="space-y-2">
                    <Label>Tipo</Label>
                    <Select
                      value={logType}
                      onChange={(e) => setLogType(e.target.value as EventType)}
                    >
                      {EVENT_TYPES.map((t) => (
                        <option key={t} value={t}>
                          {typeLabel(t)}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Data</Label>
                    <Input
                      type="date"
                      value={logDate}
                      onChange={(e) => setLogDate(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Custo (R$)</Label>
                    <Input
                      type="number"
                      value={logCost}
                      onChange={(e) => setLogCost(e.target.value)}
                      placeholder="opcional"
                    />
                  </div>
                  <Button type="submit" disabled={quickLog.isPending}>
                    {quickLog.isPending ? "Registrando…" : "Registrar"}
                  </Button>
                  {quickLog.isError && (
                    <p className="text-sm text-red-700">
                      {quickLog.error instanceof ApiError
                        ? quickLog.error.message
                        : "Erro ao registrar."}
                    </p>
                  )}
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Planejar operação</CardTitle>
              </CardHeader>
              <CardContent>
                <form
                  className="space-y-3"
                  onSubmit={(e) => {
                    e.preventDefault();
                    addPlanned.mutate();
                  }}
                >
                  <div className="space-y-2">
                    <Label>Tipo</Label>
                    <Select
                      value={planType}
                      onChange={(e) => setPlanType(e.target.value as EventType)}
                    >
                      {EVENT_TYPES.map((t) => (
                        <option key={t} value={t}>
                          {typeLabel(t)}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Data planejada</Label>
                    <Input
                      type="date"
                      value={planDate}
                      onChange={(e) => setPlanDate(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Custo esperado (R$)</Label>
                    <Input
                      type="number"
                      value={planCost}
                      onChange={(e) => setPlanCost(e.target.value)}
                      placeholder="opcional"
                    />
                  </div>
                  <Button type="submit" disabled={addPlanned.isPending}>
                    {addPlanned.isPending ? "Salvando…" : "Adicionar ao plano"}
                  </Button>
                  {addPlanned.isError && (
                    <p className="text-sm text-red-700">
                      {addPlanned.error instanceof ApiError
                        ? addPlanned.error.message
                        : "Erro ao planejar."}
                    </p>
                  )}
                </form>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
