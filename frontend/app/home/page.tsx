"use client";

import * as React from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type EventType, type FarmDashboard } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { ConfidenceBadge } from "@/components/confidence-badge";
import { ErrorBlock, LoadingBlock } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Stat } from "@/components/stat";
import { useFarmContext } from "@/lib/context";
import { EVENT_TYPES, EVENT_TYPE_LABELS } from "@/lib/events";
import { formatBRL, formatNumber } from "@/lib/utils";

function levelVariant(level: string): BadgeProps["variant"] {
  if (level === "alta") return "danger";
  if (level === "média") return "warning";
  return "success";
}

const MORE_TOOLS = [
  { href: "/", label: "Inteligência Regional" },
  { href: "/planting/optimize", label: "Otimizar Plantio" },
  { href: "/financeiro", label: "Financeiro" },
  { href: "/adaptive", label: "Inteligência Adaptativa" },
  { href: "/calibration", label: "Calibração" },
  { href: "/system", label: "Sistema" },
];

export default function HomePage() {
  const ctx = useFarmContext();
  const farmId = ctx.farmId; // fazenda vem do contexto global (header)
  const queryClient = useQueryClient();
  const farmsQuery = useQuery({ queryKey: ["farms"], queryFn: api.getFarms });

  const seedDemo = useMutation({
    mutationFn: api.seedDemo,
    onSuccess: () => {
      // a barra de contexto seleciona a fazenda recém-criada automaticamente
      queryClient.invalidateQueries({ queryKey: ["farms"] });
    },
  });

  const dash = useQuery<FarmDashboard>({
    queryKey: ["dashboard", farmId],
    queryFn: () => api.getDashboard(farmId as number),
    enabled: farmId !== null,
  });

  const hasFarms = !!farmsQuery.data && farmsQuery.data.length > 0;

  // Registro rápido (Fase 5.1) + presets (Fase 5.2)
  const [qType, setQType] = React.useState<EventType>("FUNGICIDE");
  const [qDate, setQDate] = React.useState("");
  const [qCost, setQCost] = React.useState("");
  const [presetId, setPresetId] = React.useState<number | null>(null);
  const presetsQuery = useQuery({
    queryKey: ["event-presets"],
    queryFn: api.getEventPresets,
  });
  const quickLog = useMutation({
    mutationFn: () =>
      api.quickLog({
        crop_cycle_ids: [ctx.cropCycleId as number],
        event_date: qDate,
        event_type: qType,
        cost: qCost ? Number(qCost) : undefined,
        preset_id: presetId ?? undefined,
      }),
    onSuccess: () => {
      setQCost("");
      queryClient.invalidateQueries({ queryKey: ["dashboard", farmId] });
    },
  });

  // Criar preset (operação favorita)
  const [newPreset, setNewPreset] = React.useState({
    name: "",
    event_type: "FUNGICIDE" as EventType,
    product_name: "",
    default_cost: "",
    cost_is_per_hectare: false,
  });
  const createPreset = useMutation({
    mutationFn: () =>
      api.createEventPreset({
        name: newPreset.name,
        event_type: newPreset.event_type,
        product_name: newPreset.product_name || undefined,
        default_cost: newPreset.default_cost ? Number(newPreset.default_cost) : undefined,
        cost_is_per_hectare: newPreset.cost_is_per_hectare,
      }),
    onSuccess: () => {
      setNewPreset({
        name: "",
        event_type: "FUNGICIDE",
        product_name: "",
        default_cost: "",
        cost_is_per_hectare: false,
      });
      queryClient.invalidateQueries({ queryKey: ["event-presets"] });
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Início"
        description="O essencial da sua safra hoje — atenção, próxima operação, orçamento e alertas."
      />

      <ConfidenceBadge />

      {/* Registro rápido — flywheel (Fase 5.1) */}
      {hasFarms && ctx.cropCycleId !== null && (
        <Card>
          <CardHeader>
            <CardTitle>Registro rápido</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="flex flex-wrap items-end gap-3"
              onSubmit={(e) => {
                e.preventDefault();
                if (!qDate) return;
                quickLog.mutate();
              }}
            >
              {presetsQuery.data && presetsQuery.data.length > 0 && (
                <div className="space-y-1">
                  <Label htmlFor="qpreset">Preset</Label>
                  <Select
                    id="qpreset"
                    value={presetId ?? ""}
                    onChange={(e) => {
                      const id = e.target.value ? Number(e.target.value) : null;
                      setPresetId(id);
                      const p = presetsQuery.data?.find((x) => x.id === id);
                      if (p) setQType(p.event_type);
                    }}
                  >
                    <option value="">— sem preset —</option>
                    {presetsQuery.data.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </Select>
                </div>
              )}
              <div className="space-y-1">
                <Label htmlFor="qtype">Operação</Label>
                <Select
                  id="qtype"
                  value={qType}
                  onChange={(e) => setQType(e.target.value as EventType)}
                >
                  {EVENT_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {EVENT_TYPE_LABELS[t]}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="space-y-1">
                <Label htmlFor="qdate">Data</Label>
                <Input
                  id="qdate"
                  type="date"
                  value={qDate}
                  onChange={(e) => setQDate(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="qcost">Custo (R$)</Label>
                <Input
                  id="qcost"
                  type="number"
                  value={qCost}
                  onChange={(e) => setQCost(e.target.value)}
                  placeholder="opcional"
                  className="w-32"
                />
              </div>
              <Button type="submit" disabled={quickLog.isPending}>
                {quickLog.isPending ? "Registrando…" : "Registrar"}
              </Button>
            </form>
            <p className="mt-2 text-xs text-muted-foreground">
              Registrado na safra{" "}
              <span className="font-medium">{ctx.cropCycleLabel ?? ""}</span>.
            </p>

            <details className="mt-3">
              <summary className="cursor-pointer text-xs text-brand-700">
                Criar preset (operação favorita)
              </summary>
              <form
                className="mt-2 flex flex-wrap items-end gap-3"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!newPreset.name) return;
                  createPreset.mutate();
                }}
              >
                <div className="space-y-1">
                  <Label htmlFor="pname">Nome</Label>
                  <Input
                    id="pname"
                    value={newPreset.name}
                    onChange={(e) => setNewPreset((s) => ({ ...s, name: e.target.value }))}
                    placeholder="Ex.: Fungicida padrão"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="ptype">Operação</Label>
                  <Select
                    id="ptype"
                    value={newPreset.event_type}
                    onChange={(e) =>
                      setNewPreset((s) => ({ ...s, event_type: e.target.value as EventType }))
                    }
                  >
                    {EVENT_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {EVENT_TYPE_LABELS[t]}
                      </option>
                    ))}
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="pcost">Custo padrão (R$)</Label>
                  <Input
                    id="pcost"
                    type="number"
                    value={newPreset.default_cost}
                    onChange={(e) =>
                      setNewPreset((s) => ({ ...s, default_cost: e.target.value }))
                    }
                    placeholder="opcional"
                    className="w-32"
                  />
                </div>
                <label className="flex items-center gap-2 text-xs text-muted-foreground">
                  <input
                    type="checkbox"
                    checked={newPreset.cost_is_per_hectare}
                    onChange={(e) =>
                      setNewPreset((s) => ({ ...s, cost_is_per_hectare: e.target.checked }))
                    }
                  />
                  por hectare
                </label>
                <Button type="submit" variant="outline" disabled={createPreset.isPending}>
                  {createPreset.isPending ? "Salvando…" : "Salvar preset"}
                </Button>
              </form>
            </details>
          </CardContent>
        </Card>
      )}

      {/* Empty state / onboarding */}
      {farmsQuery.isLoading ? (
        <LoadingBlock label="Carregando…" />
      ) : farmsQuery.isError ? (
        <ErrorBlock error={farmsQuery.error} />
      ) : !hasFarms ? (
        <Card>
          <CardHeader>
            <CardTitle>Bem-vindo ao FADA</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Para começar, cadastre sua fazenda e talhões — ou explore com uma fazenda
              de demonstração já populada (histórico, plano, custos e insights).
            </p>
            <div className="flex flex-wrap gap-3">
              <Button onClick={() => seedDemo.mutate()} disabled={seedDemo.isPending}>
                {seedDemo.isPending
                  ? "Criando demonstração…"
                  : "Explorar com fazenda de demonstração"}
              </Button>
              <Link href="/onboarding">
                <Button variant="outline">Criar minha fazenda</Button>
              </Link>
            </div>
            {seedDemo.isError && (
              <p className="text-sm text-red-700">
                Não foi possível criar a demonstração. Verifique se o backend está ativo
                (página Sistema).
              </p>
            )}
          </CardContent>
        </Card>
      ) : null}

      {/* Dashboard */}
      {farmId !== null && hasFarms && (
        <>
          {dash.isLoading ? (
            <LoadingBlock label="Montando o painel…" />
          ) : dash.isError ? (
            <ErrorBlock error={dash.error} />
          ) : dash.data ? (
            <>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <Stat
                  label="Já gastei"
                  value={formatBRL(dash.data.budget.actual_total)}
                />
                <Stat
                  label="Falta investir"
                  value={formatBRL(dash.data.budget.remaining)}
                />
                <Stat
                  label="Talhões em alerta"
                  value={`${
                    dash.data.attention.levels["alta"] +
                    dash.data.attention.levels["média"]
                  } / ${dash.data.n_fields}`}
                />
                <Stat
                  label="Operações atrasadas"
                  value={`${dash.data.agenda.overdue}`}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                {/* Atenção */}
                <Card>
                  <CardHeader>
                    <CardTitle>O que merece atenção</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {dash.data.attention.top ? (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={levelVariant(
                              dash.data.attention.top.attention_level
                            )}
                          >
                            {dash.data.attention.top.attention_level}
                          </Badge>
                          <span className="font-medium">
                            {dash.data.attention.top.field_name}
                          </span>
                        </div>
                        <ul className="list-inside list-disc text-sm text-muted-foreground">
                          {dash.data.attention.top.flags.map((fl, i) => (
                            <li key={i}>{fl.title}</li>
                          ))}
                        </ul>
                        <Link
                          href="/decisoes"
                          className="text-sm text-brand-700 underline"
                        >
                          Ver todos os talhões →
                        </Link>
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        Nenhum talhão em alerta com os dados atuais.
                      </p>
                    )}
                  </CardContent>
                </Card>

                {/* Próxima operação + orçamento */}
                <Card>
                  <CardHeader>
                    <CardTitle>Safra & próxima operação</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    <div>
                      <span className="text-muted-foreground">Próxima operação: </span>
                      {dash.data.agenda.next_operation ? (
                        <span className="font-medium">
                          {dash.data.agenda.next_operation.event_type} ·{" "}
                          {dash.data.agenda.next_operation.planned_date}
                        </span>
                      ) : (
                        <span>nenhuma planejada</span>
                      )}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Orçamento: </span>
                      <span className="font-medium">
                        {formatBRL(dash.data.budget.actual_total)} de{" "}
                        {formatBRL(dash.data.budget.planned_total)}
                      </span>
                      {dash.data.budget.pct_consumed !== null && (
                        <span className="text-muted-foreground">
                          {" "}
                          ({formatNumber(dash.data.budget.pct_consumed)}%)
                        </span>
                      )}
                    </div>
                    <Link
                      href="/planejamento"
                      className="inline-block text-brand-700 underline"
                    >
                      Plano & orçamento →
                    </Link>
                  </CardContent>
                </Card>
              </div>

              {/* Insights */}
              {dash.data.insights.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Destaques</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2 text-sm">
                      {dash.data.insights.map((i, idx) => (
                        <li key={idx}>
                          <span className="font-medium">{i.title}</span>
                          <span className="text-muted-foreground"> — {i.detail}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </>
          ) : null}
        </>
      )}

      {/* Mais ferramentas (acesso no mobile) */}
      <Card>
        <CardHeader>
          <CardTitle>Mais ferramentas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {MORE_TOOLS.map((t) => (
              <Link
                key={t.href}
                href={t.href}
                className="rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                {t.label}
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
