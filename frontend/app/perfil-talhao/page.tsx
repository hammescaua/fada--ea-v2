"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  api,
  type AgronomicEstimate,
  type AgronomicFactor,
  type Farm,
  type Field,
} from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { MunicipalitySelect } from "@/components/municipality-select";
import { ErrorBlock, LoadingBlock, Spinner } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { formatNumber } from "@/lib/utils";

export default function PerfilTalhaoPage() {
  const qc = useQueryClient();
  const [season, setSeason] = React.useState("2026/27");
  const [municipality, setMunicipality] = React.useState("");
  const [farmId, setFarmId] = React.useState<number | null>(null);
  const [fieldId, setFieldId] = React.useState<number | null>(null);
  const [profile, setProfile] = React.useState<Record<string, string>>({});

  const factors = useQuery<AgronomicFactor[]>({
    queryKey: ["agronomic-factors"],
    queryFn: api.getAgronomicFactors,
    staleTime: Infinity,
  });
  const farms = useQuery<Farm[]>({ queryKey: ["farms"], queryFn: api.getFarms });
  const fields = useQuery<Field[]>({
    queryKey: ["fields", farmId],
    queryFn: () => api.getFields(farmId as number),
    enabled: farmId !== null,
  });

  // Carrega o perfil salvo do talhão selecionado.
  const savedProfile = useQuery({
    queryKey: ["field-profile", fieldId],
    queryFn: () => api.getFieldProfile(fieldId as number),
    enabled: fieldId !== null,
  });
  React.useEffect(() => {
    if (savedProfile.data) setProfile(savedProfile.data.profile ?? {});
  }, [savedProfile.data]);

  const saveProfile = useMutation({
    mutationFn: () =>
      api.saveFieldProfile(
        fieldId as number,
        Object.fromEntries(Object.entries(profile).filter(([, v]) => v !== ""))
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["field-profile", fieldId] });
      estimate.mutate();
    },
  });

  const estimate = useMutation<AgronomicEstimate, Error>({
    mutationFn: () => {
      const clean = Object.fromEntries(
        Object.entries(profile).filter(([, v]) => v !== "")
      );
      return fieldId !== null
        ? api.getFieldEstimate(fieldId, season)
        : api.postAgronomicEstimate({ municipality, season, profile: clean });
    },
  });

  const e = estimate.data;
  const fieldMode = fieldId !== null;
  const canEstimate = fieldMode || municipality !== "";
  const answered = Object.values(profile).filter((v) => v !== "").length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Perfil do Talhão — previsão personalizada"
        description="Cada lavoura tem variáveis próprias que mexem na produtividade. Responda o perfil agronômico padronizado e veja sua previsão divergir da média regional, fator a fator — antes de plantar."
      />

      <Card>
        <CardContent className="space-y-4 pt-6">
          {/* Modo talhão: escolhe fazenda + talhão (perfil é salvo nele) */}
          {farms.data && farms.data.length > 0 && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="space-y-1">
                <Label htmlFor="farm">Fazenda</Label>
                <Select
                  id="farm"
                  value={farmId ?? ""}
                  onChange={(ev) => {
                    setFarmId(ev.target.value ? Number(ev.target.value) : null);
                    setFieldId(null);
                  }}
                >
                  <option value="">— sem talhão (avulso) —</option>
                  {farms.data.map((f) => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </Select>
              </div>
              <div className="space-y-1">
                <Label htmlFor="field">Talhão</Label>
                <Select
                  id="field"
                  value={fieldId ?? ""}
                  onChange={(ev) => setFieldId(ev.target.value ? Number(ev.target.value) : null)}
                  disabled={farmId === null}
                >
                  <option value="">— selecione —</option>
                  {(fields.data ?? []).map((f) => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </Select>
              </div>
              <div className="space-y-1">
                <Label htmlFor="season">Safra</Label>
                <Input id="season" value={season} onChange={(ev) => setSeason(ev.target.value)} />
              </div>
            </div>
          )}

          {/* Modo avulso: município (quando nenhum talhão selecionado) */}
          {!fieldMode && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <Label htmlFor="municipality">Município (sem talhão)</Label>
                <MunicipalitySelect
                  id="municipality"
                  value={municipality}
                  onChange={setMunicipality}
                />
              </div>
              <div className="flex items-end text-sm text-muted-foreground">
                {answered} fator(es) respondido(s); os demais assumem o nível típico.
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* QUESTIONÁRIO PADRONIZADO */}
      <Card>
        <CardHeader>
          <CardTitle>Perfil agronômico padronizado</CardTitle>
        </CardHeader>
        <CardContent>
          {factors.isLoading && <LoadingBlock label="Carregando fatores…" />}
          {factors.isError && <ErrorBlock error={factors.error} />}
          {factors.data && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {factors.data.map((f) => (
                <div key={f.key} className="space-y-1">
                  <Label htmlFor={f.key}>{f.question}</Label>
                  <Select
                    id={f.key}
                    value={profile[f.key] ?? ""}
                    onChange={(ev) => setProfile((s) => ({ ...s, [f.key]: ev.target.value }))}
                  >
                    <option value="">— típico —</option>
                    {f.options.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                        {o.effect_pct !== 0 ? ` (${o.effect_pct > 0 ? "+" : ""}${o.effect_pct}%)` : ""}
                      </option>
                    ))}
                  </Select>
                  <p className="text-xs text-muted-foreground">{f.rationale}</p>
                </div>
              ))}
            </div>
          )}
          <div className="mt-4 flex flex-wrap gap-3">
            <Button onClick={() => canEstimate && estimate.mutate()} disabled={!canEstimate || estimate.isPending}>
              {estimate.isPending && <Spinner />}
              Calcular previsão
            </Button>
            {fieldMode && (
              <Button variant="outline" onClick={() => saveProfile.mutate()} disabled={saveProfile.isPending}>
                {saveProfile.isPending && <Spinner />}
                Salvar perfil no talhão
              </Button>
            )}
            {saveProfile.isSuccess && (
              <span className="self-center text-sm text-green-700">Perfil salvo ✓</span>
            )}
          </div>
          {fieldMode && (
            <p className="mt-2 text-xs text-muted-foreground">
              Salvo no talhão, o perfil personaliza também o brief de “Planejar a Safra”.
            </p>
          )}
        </CardContent>
      </Card>

      {estimate.isError && <ErrorBlock error={estimate.error} />}

      {/* RESULTADO */}
      {e && (
        <Card className="border-brand-200">
          <CardHeader>
            <CardTitle>Sua previsão vs a média regional</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <div className="text-xs uppercase text-muted-foreground">Regional (média)</div>
                <div className="mt-1 text-2xl font-semibold tabular-nums">
                  {formatNumber(e.regional.point_sc_ha)} sc/ha
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatNumber(e.regional.interval_sc_ha[0])}–{formatNumber(e.regional.interval_sc_ha[1])}
                </div>
              </div>
              <div className="rounded-lg border-2 border-brand-300 bg-brand-50/50 p-4">
                <div className="text-xs uppercase text-brand-700">Seu talhão</div>
                <div className="mt-1 text-2xl font-semibold tabular-nums text-brand-800">
                  {formatNumber(e.personalized.point_sc_ha)} sc/ha
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatNumber(e.personalized.interval_sc_ha[0])}–{formatNumber(e.personalized.interval_sc_ha[1])}
                </div>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <div className="text-xs uppercase text-muted-foreground">Ajuste do perfil</div>
                <div
                  className={
                    "mt-1 text-2xl font-semibold tabular-nums " +
                    (e.adjustment.total_effect_pct >= 0 ? "text-green-700" : "text-red-700")
                  }
                >
                  {e.adjustment.total_effect_pct > 0 ? "+" : ""}
                  {formatNumber(e.adjustment.total_effect_pct)}%
                </div>
                <div className="text-xs text-muted-foreground">
                  {e.adjustment.n_factors} fatores{e.adjustment.clamped ? " · limitado" : ""}
                </div>
              </div>
            </div>

            {e.adjustment.factors.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2 font-medium">Efeito</th>
                      <th className="px-3 py-2 font-medium">Fator</th>
                      <th className="px-3 py-2 font-medium">Resposta</th>
                      <th className="px-3 py-2 font-medium">Por quê</th>
                    </tr>
                  </thead>
                  <tbody>
                    {e.adjustment.factors.map((f) => (
                      <tr key={f.key} className="border-t border-border">
                        <td
                          className={
                            "px-3 py-2 font-medium tabular-nums " +
                            (f.effect_pct >= 0 ? "text-green-700" : "text-red-700")
                          }
                        >
                          {f.effect_pct > 0 ? "+" : ""}
                          {f.effect_pct}%
                        </td>
                        <td className="px-3 py-2">{f.question}</td>
                        <td className="px-3 py-2 font-medium">{f.option_label}</td>
                        <td className="px-3 py-2 text-xs text-muted-foreground">{f.rationale}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <p className="text-xs italic text-muted-foreground">{e.disclaimer}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
