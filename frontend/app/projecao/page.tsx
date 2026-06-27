"use client";

import * as React from "react";
import Link from "next/link";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  api,
  type Field,
  type MultiSeasonProjection,
} from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { ErrorBlock, LoadingBlock } from "@/components/states";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Stat } from "@/components/stat";
import { useFarmContext } from "@/lib/context";
import { formatBRL, formatNumber } from "@/lib/utils";

function scenarioLabel(name: string): string {
  if (name === "pessimista") return "Ano seco";
  if (name === "otimista") return "Ano favorável";
  return "Ano normal";
}

export default function ProjecaoPage() {
  const ctx = useFarmContext();
  const farmId = ctx.farmId;
  const [fieldId, setFieldId] = React.useState<number | null>(null);
  const [n, setN] = React.useState("3");
  const [price, setPrice] = React.useState("");
  const [cost, setCost] = React.useState("");
  const [priceTrend, setPriceTrend] = React.useState("");
  const [costTrend, setCostTrend] = React.useState("");

  const fields = useQuery<Field[]>({
    queryKey: ["fields", farmId],
    queryFn: () => api.getFields(farmId as number),
    enabled: farmId !== null,
  });

  React.useEffect(() => {
    if (fieldId === null && fields.data && fields.data.length > 0) {
      setFieldId(fields.data[0].id);
    }
  }, [fields.data, fieldId]);

  const proj = useMutation<MultiSeasonProjection>({
    mutationFn: () =>
      api.getMultiSeason(fieldId as number, {
        n: Number(n),
        price_per_bag: price ? Number(price) : undefined,
        cost_per_ha: cost ? Number(cost) : undefined,
        price_trend_pct: priceTrend ? Number(priceTrend) : undefined,
        cost_trend_pct: costTrend ? Number(costTrend) : undefined,
      }),
  });

  const data = proj.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Projeção de safras (soja)"
        description="Veja produtividade e rentabilidade das próximas safras lado a lado, sob as suas suposições de preço e custo. A base climática é a safra típica da região."
      />

      {farmId === null ? (
        <Card>
          <CardContent className="py-6 text-sm text-muted-foreground">
            Selecione uma fazenda no topo da tela.{" "}
            <Link href="/home" className="text-brand-700 underline">
              Ir para o Início
            </Link>
            .
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Suposições</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="flex flex-wrap items-end gap-3"
              onSubmit={(e) => {
                e.preventDefault();
                if (fieldId !== null) proj.mutate();
              }}
            >
              <div className="space-y-1">
                <Label htmlFor="field">Talhão</Label>
                <Select
                  id="field"
                  value={fieldId ?? ""}
                  onChange={(e) => setFieldId(e.target.value ? Number(e.target.value) : null)}
                >
                  {(fields.data ?? []).map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name} ({f.area_ha} ha)
                    </option>
                  ))}
                </Select>
              </div>
              <div className="space-y-1">
                <Label htmlFor="n">Safras</Label>
                <Select id="n" value={n} onChange={(e) => setN(e.target.value)}>
                  {[2, 3, 4, 5, 6].map((v) => (
                    <option key={v} value={v}>
                      {v}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="space-y-1">
                <Label htmlFor="price">Preço (R$/sc)</Label>
                <Input
                  id="price"
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="CEPEA"
                  className="w-28"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="cost">Custo (R$/ha)</Label>
                <Input
                  id="cost"
                  type="number"
                  value={cost}
                  onChange={(e) => setCost(e.target.value)}
                  placeholder="CONAB"
                  className="w-28"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="pt">Preço +%/ano</Label>
                <Input
                  id="pt"
                  type="number"
                  value={priceTrend}
                  onChange={(e) => setPriceTrend(e.target.value)}
                  placeholder="0"
                  className="w-24"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="ct">Custo +%/ano</Label>
                <Input
                  id="ct"
                  type="number"
                  value={costTrend}
                  onChange={(e) => setCostTrend(e.target.value)}
                  placeholder="0"
                  className="w-24"
                />
              </div>
              <Button type="submit" disabled={proj.isPending || fieldId === null}>
                {proj.isPending ? "Projetando…" : "Projetar"}
              </Button>
            </form>
            <p className="mt-3 text-xs text-muted-foreground">
              Preencha preço/custo para usar seus números; em branco, o FADA usa as
              fontes públicas (CEPEA/CONAB). A produtividade vem do Perfil do Talhão —
              quanto mais completo, melhor.{" "}
              <Link href="/perfil-talhao" className="text-brand-700 underline">
                Editar perfil
              </Link>
              .
            </p>
          </CardContent>
        </Card>
      )}

      {proj.isError && <ErrorBlock error={proj.error} />}
      {proj.isPending && <LoadingBlock label="Projetando safras…" />}

      {data && (
        <>
          {data.narrative && (
            <Card className="border-brand-200 bg-brand-50/60">
              <CardContent className="py-4 text-sm">{data.narrative}</CardContent>
            </Card>
          )}

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Stat
              label="Produtividade típica"
              value={`${formatNumber(data.productivity.point_sc_ha)} sc/ha`}
              unit={`(${formatNumber(data.productivity.interval_sc_ha[0])}–${formatNumber(
                data.productivity.interval_sc_ha[1]
              )})`}
            />
            <Stat label="Preço base" value={formatBRL(data.assumptions.price_per_bag)} />
            <Stat label="Custo base/ha" value={formatBRL(data.assumptions.cost_per_ha)} />
            <Stat label="Área" value={`${data.area_ha} ha`} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Rentabilidade por safra (R$/ha)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="py-2 pr-3">Safra</th>
                      <th className="py-2 pr-3">Preço</th>
                      <th className="py-2 pr-3">Custo/ha</th>
                      <th className="py-2 pr-3">Ano seco</th>
                      <th className="py-2 pr-3">Ano normal</th>
                      <th className="py-2 pr-3">Ano favorável</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.seasons.map((s) => {
                      const by = (nm: string) =>
                        s.scenarios.find((x) => x.name === nm)?.profit_per_ha ?? 0;
                      const cell = (v: number) => (
                        <span className={v >= 0 ? "text-emerald-700" : "text-red-700"}>
                          {formatBRL(v)}
                        </span>
                      );
                      return (
                        <tr key={s.season} className="border-b border-border last:border-0">
                          <td className="py-2 pr-3 font-medium">{s.season}</td>
                          <td className="py-2 pr-3 tabular-nums">{formatBRL(s.price_per_bag)}</td>
                          <td className="py-2 pr-3 tabular-nums">{formatBRL(s.cost_per_ha)}</td>
                          <td className="py-2 pr-3 tabular-nums">{cell(by("pessimista"))}</td>
                          <td className="py-2 pr-3 tabular-nums font-medium">{cell(by("normal"))}</td>
                          <td className="py-2 pr-3 tabular-nums">{cell(by("otimista"))}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-muted-foreground">{data.productivity.note}</p>
              <p className="text-xs text-muted-foreground">{data.disclaimer}</p>
              {data.data_sources.length > 0 && (
                <p className="text-[11px] text-muted-foreground">
                  Fontes: {data.data_sources.join(" · ")}.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Produtividade por cenário (safra típica)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2 text-sm">
                {data.productivity.scenarios.map((s) => (
                  <div key={s.name} className="rounded-md border border-border px-3 py-1.5">
                    <span className="text-muted-foreground">{scenarioLabel(s.name)}: </span>
                    <span className="font-medium tabular-nums">
                      {formatNumber(s.yield_sc_ha)} sc/ha
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
