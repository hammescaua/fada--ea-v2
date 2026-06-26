"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  api,
  type AgronomicEstimate,
  type AgronomicFactor,
  type Farm,
  type Field,
  type FieldLearnedEstimate,
  type ManejoHistory,
  type SoilAnalysisResult,
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

  // Aprendizado: perfil (a priori) + colheitas do talhão (a posteriori).
  const learned = useQuery<FieldLearnedEstimate>({
    queryKey: ["field-learned", fieldId, season],
    queryFn: () => api.getFieldLearnedEstimate(fieldId as number, season),
    enabled: fieldId !== null,
    retry: false,
  });

  // Histórico de manejo × resultado por safra.
  const manejoHistory = useQuery<ManejoHistory>({
    queryKey: ["manejo-history", fieldId],
    queryFn: () => api.getManejoHistory(fieldId as number),
    enabled: fieldId !== null,
    retry: false,
  });
  const saveManejo = useMutation({
    mutationFn: (cycleId: number) =>
      api.saveCycleManejo(
        cycleId,
        Object.fromEntries(Object.entries(profile).filter(([, v]) => v !== ""))
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["manejo-history", fieldId] });
      qc.invalidateQueries({ queryKey: ["field-learned", fieldId, season] });
    },
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

  const [quickMode, setQuickMode] = React.useState(true);

  // Pré-preenchimento por análise de solo (CQFS) → mescla fatores no perfil.
  const [soil, setSoil] = React.useState<Record<string, string>>({});
  const [soilNotes, setSoilNotes] = React.useState<SoilAnalysisResult | null>(null);
  const soilFields: { key: string; label: string }[] = [
    { key: "p_mehlich", label: "P (mg/dm³)" },
    { key: "k_mehlich", label: "K (mg/dm³)" },
    { key: "clay_pct", label: "Argila (%)" },
    { key: "ctc", label: "CTC (cmolc/dm³)" },
    { key: "ph_water", label: "pH (água)" },
    { key: "al_saturation_pct", label: "Sat. Al — m (%)" },
    { key: "organic_matter_pct", label: "MO (%)" },
  ];
  // Sugestão de solo pela localização (EMBRAPA) — só no modo talhão.
  const [soilSugNote, setSoilSugNote] = React.useState<string | null>(null);
  const soilSuggest = useMutation({
    mutationFn: () => api.getFieldSoilSuggestion(fieldId as number),
    onSuccess: (res) => {
      setProfile((s) => ({ ...s, ...res.profile_fragment }));
      setSoilSugNote(
        `Solo dominante: ${res.ordem_dominante} (confiança ${res.confidence}). ` +
          `${res.note ?? ""} Fonte: ${res.source ?? ""}.`
      );
    },
  });

  const soilMutation = useMutation<SoilAnalysisResult, Error>({
    mutationFn: () => {
      const body = Object.fromEntries(
        Object.entries(soil)
          .filter(([, v]) => v !== "" && !Number.isNaN(Number(v)))
          .map(([k, v]) => [k, Number(v)])
      );
      return api.classifySoilAnalysis(body);
    },
    onSuccess: (res) => {
      setSoilNotes(res);
      setProfile((s) => ({ ...s, ...res.profile_fragment }));
    },
  });

  // Data de plantio → janela ZARC (preenche janela_plantio).
  const [plantingDate, setPlantingDate] = React.useState("");
  const [zarcBasis, setZarcBasis] = React.useState<string | null>(null);
  const zarcMutation = useMutation({
    mutationFn: () =>
      api.classifyPlantingWindow({
        plantingDate,
        fieldId: fieldId ?? undefined,
        municipality: fieldId === null ? municipality : undefined,
      }),
    onSuccess: (res) => {
      setZarcBasis(res.basis);
      setProfile((s) => ({ ...s, ...res.profile_fragment }));
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

  // Completude dos fatores essenciais (qualidade da previsão) — ao vivo.
  const essentialKeys = (factors.data ?? []).filter((f) => f.essential).map((f) => f.key);
  const essentialFilled = essentialKeys.filter((k) => (profile[k] ?? "") !== "");
  const essentialMissing = (factors.data ?? []).filter(
    (f) => f.essential && (profile[f.key] ?? "") === ""
  );
  const completenessPct =
    essentialKeys.length > 0
      ? Math.round((100 * essentialFilled.length) / essentialKeys.length)
      : 0;

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

      {/* PRÉ-PREENCHER PELA ANÁLISE DE SOLO (CQFS) */}
      <Card>
        <CardHeader>
          <CardTitle>Tem o laudo de análise de solo? Preencha automático</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-muted-foreground">
            Digite os valores do laudo — o FADA classifica fertilidade e acidez pelas
            faixas CQFS-RS/SC e preenche os fatores correspondentes (você pode ajustar).
          </p>
          {fieldMode && (
            <div className="flex flex-wrap items-center gap-3">
              <Button
                variant="outline"
                onClick={() => soilSuggest.mutate()}
                disabled={soilSuggest.isPending}
              >
                {soilSuggest.isPending && <Spinner />}
                Sugerir solo pela localização (EMBRAPA)
              </Button>
              {soilSugNote && (
                <span className="text-xs text-muted-foreground">{soilSugNote}</span>
              )}
            </div>
          )}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
            {soilFields.map((f) => (
              <div key={f.key} className="space-y-1">
                <Label htmlFor={f.key} className="text-xs">{f.label}</Label>
                <Input
                  id={f.key}
                  type="number"
                  step="0.1"
                  value={soil[f.key] ?? ""}
                  onChange={(ev) => setSoil((s) => ({ ...s, [f.key]: ev.target.value }))}
                />
              </div>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="outline" onClick={() => soilMutation.mutate()} disabled={soilMutation.isPending}>
              {soilMutation.isPending && <Spinner />}
              Classificar e preencher
            </Button>
            {soilNotes && (
              <span className="text-sm text-green-700">
                {soilNotes.notes.length} fator(es) preenchido(s) ✓
              </span>
            )}
          </div>
          {soilNotes && soilNotes.notes.length > 0 && (
            <ul className="space-y-0.5 text-xs text-muted-foreground">
              {soilNotes.notes.map((n) => (
                <li key={n.factor}>
                  <span className="font-medium">{n.factor} = {n.value}</span> — {n.basis}
                </li>
              ))}
            </ul>
          )}
          {soilNotes && (
            <p className="text-xs italic text-muted-foreground">{soilNotes.disclaimer}</p>
          )}
        </CardContent>
      </Card>

      {/* DATA DE PLANTIO → JANELA ZARC */}
      <Card>
        <CardHeader>
          <CardTitle>Data de plantio pretendida → janela ZARC oficial</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1">
              <Label htmlFor="planting-date" className="text-xs">Data de plantio</Label>
              <Input
                id="planting-date"
                type="date"
                value={plantingDate}
                onChange={(ev) => setPlantingDate(ev.target.value)}
                className="w-44"
              />
            </div>
            <Button
              variant="outline"
              onClick={() => plantingDate && zarcMutation.mutate()}
              disabled={!plantingDate || (fieldId === null && !municipality) || zarcMutation.isPending}
            >
              {zarcMutation.isPending && <Spinner />}
              Verificar ZARC e preencher
            </Button>
          </div>
          {zarcMutation.isError && <ErrorBlock error={zarcMutation.error} />}
          {zarcBasis && <p className="text-xs text-muted-foreground">{zarcBasis}</p>}
        </CardContent>
      </Card>

      {/* QUESTIONÁRIO PADRONIZADO */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>Perfil agronômico</CardTitle>
          <div className="flex rounded-md border border-border text-xs">
            <button
              type="button"
              onClick={() => setQuickMode(true)}
              className={"rounded-l-md px-3 py-1 " + (quickMode ? "bg-brand-600 text-white" : "text-muted-foreground")}
            >
              Rápido
            </button>
            <button
              type="button"
              onClick={() => setQuickMode(false)}
              className={"rounded-r-md px-3 py-1 " + (!quickMode ? "bg-brand-600 text-white" : "text-muted-foreground")}
            >
              Completo
            </button>
          </div>
        </CardHeader>
        <CardContent>
          {essentialKeys.length > 0 && (
            <div className="mb-4 space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium">
                  Perfil essencial · {essentialFilled.length}/{essentialKeys.length}
                </span>
                <span className="text-muted-foreground tabular-nums">
                  {completenessPct}%
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className={
                    "h-full rounded-full transition-all " +
                    (completenessPct >= 75
                      ? "bg-emerald-500"
                      : completenessPct >= 40
                        ? "bg-amber-500"
                        : "bg-red-400")
                  }
                  style={{ width: `${completenessPct}%` }}
                />
              </div>
              {essentialMissing.length > 0 ? (
                <p className="text-xs text-muted-foreground">
                  Quanto mais completo, mais confiável a previsão. Falta:{" "}
                  {essentialMissing.slice(0, 3).map((f) => f.question).join("; ")}
                  {essentialMissing.length > 3 ? "…" : "."}
                </p>
              ) : (
                <p className="text-xs text-emerald-700">
                  Perfil essencial completo — previsão no maior grau de confiança.
                </p>
              )}
            </div>
          )}
          {quickMode && (
            <p className="mb-3 text-xs text-muted-foreground">
              Modo rápido: responda só o essencial (o que mais pesa). O resto assume o
              nível típico — depois você pode abrir o modo completo.
            </p>
          )}
          {factors.isLoading && <LoadingBlock label="Carregando fatores…" />}
          {factors.isError && <ErrorBlock error={factors.error} />}
          {factors.data && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {factors.data
                .filter((f) => !quickMode || f.essential)
                .map((f) => (
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
                  {f.explanation && (
                    <details className="text-xs">
                      <summary className="cursor-pointer text-brand-700">
                        Por quê (fonte)
                      </summary>
                      <p className="mt-1 text-muted-foreground">{f.explanation}</p>
                      {f.sources && f.sources.length > 0 && (
                        <p className="mt-1 text-[11px] italic text-muted-foreground">
                          Fonte: {f.sources.join("; ")}
                        </p>
                      )}
                    </details>
                  )}
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

      {/* APRENDIZADO: perfil (a priori) + colheitas do talhão (a posteriori) */}
      {fieldMode && learned.data && (
        <Card className="border-brand-200">
          <CardHeader>
            <CardTitle>O que o FADA aprendeu da sua lavoura</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <div className="text-xs uppercase text-muted-foreground">Ponto de partida (perfil)</div>
                <div className="mt-1 text-lg font-semibold tabular-nums">
                  {learned.data.a_priori_profile_pct > 0 ? "+" : ""}
                  {formatNumber(learned.data.a_priori_profile_pct)}%
                </div>
                <div className="text-xs text-muted-foreground">vs. média regional</div>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <div className="text-xs uppercase text-muted-foreground">
                  Suas colheitas ({learned.data.n_harvests})
                </div>
                <div className="mt-1 text-lg font-semibold tabular-nums">
                  {learned.data.n_harvests > 0
                    ? `${learned.data.observed_from_harvests_pct > 0 ? "+" : ""}${formatNumber(learned.data.observed_from_harvests_pct)}%`
                    : "—"}
                </div>
                <div className="text-xs text-muted-foreground">
                  confiança {Math.round(learned.data.confidence_score * 100)}% · {learned.data.adaptation_level}
                </div>
              </div>
              <div className="rounded-lg border-2 border-brand-300 bg-brand-50/50 p-4">
                <div className="text-xs uppercase text-brand-700">Previsão aprendida</div>
                <div className="mt-1 text-2xl font-semibold tabular-nums text-brand-800">
                  {formatNumber(learned.data.learned.point_sc_ha)} sc/ha
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatNumber(learned.data.learned.interval_sc_ha[0])}–
                  {formatNumber(learned.data.learned.interval_sc_ha[1])}
                </div>
              </div>
            </div>
            {learned.data.residual_history.length > 0 && (
              <div className="text-xs text-muted-foreground">
                Histórico:{" "}
                {learned.data.residual_history
                  .map((h) => `${h.harvest_year}: ${formatNumber(h.actual_sc_ha)} sc/ha`)
                  .join(" · ")}
              </div>
            )}
            <p className="text-xs italic text-muted-foreground">{learned.data.explanation}</p>
          </CardContent>
        </Card>
      )}

      {/* HISTÓRICO DE MANEJO × RESULTADO */}
      {fieldMode && manejoHistory.data && manejoHistory.data.n_seasons > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Histórico de manejo × resultado</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Safra</th>
                    <th className="px-3 py-2 font-medium">Manejo</th>
                    <th className="px-3 py-2 font-medium">Previsto</th>
                    <th className="px-3 py-2 font-medium">Real</th>
                    <th className="px-3 py-2 font-medium">vs previsto</th>
                    <th className="px-3 py-2 font-medium">Registrar manejo</th>
                  </tr>
                </thead>
                <tbody>
                  {manejoHistory.data.history.map((h) => (
                    <tr key={h.crop_cycle_id} className="border-t border-border">
                      <td className="px-3 py-2 font-medium">{h.season}</td>
                      <td className="px-3 py-2 text-xs text-muted-foreground">
                        {h.manejo_effect_pct > 0 ? "+" : ""}
                        {formatNumber(h.manejo_effect_pct)}% · {h.manejo_source}
                      </td>
                      <td className="px-3 py-2 tabular-nums">
                        {h.predicted_sc_ha != null ? `${formatNumber(h.predicted_sc_ha)}` : "—"}
                      </td>
                      <td className="px-3 py-2 tabular-nums font-medium">
                        {h.actual_sc_ha != null ? `${formatNumber(h.actual_sc_ha)}` : "—"}
                      </td>
                      <td
                        className={
                          "px-3 py-2 tabular-nums " +
                          (h.delta_vs_predicted_pct == null
                            ? ""
                            : h.delta_vs_predicted_pct >= 0
                              ? "text-green-700"
                              : "text-red-700")
                        }
                      >
                        {h.delta_vs_predicted_pct != null
                          ? `${h.delta_vs_predicted_pct > 0 ? "+" : ""}${formatNumber(h.delta_vs_predicted_pct)}%`
                          : "—"}
                      </td>
                      <td className="px-3 py-2">
                        <button
                          className="text-xs text-brand-700 underline disabled:opacity-50"
                          onClick={() => saveManejo.mutate(h.crop_cycle_id)}
                          disabled={saveManejo.isPending}
                        >
                          salvar perfil atual aqui
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-muted-foreground">{manejoHistory.data.note}</p>
          </CardContent>
        </Card>
      )}

      {/* RESULTADO */}
      {e && (
        <Card className="border-brand-200">
          <CardHeader>
            <CardTitle>Sua previsão vs a média regional</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {e.narrative && (
              <p className="rounded-md bg-brand-50/60 px-3 py-2 text-sm leading-relaxed text-foreground">
                {e.narrative}
              </p>
            )}
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

            {/* Cenários personalizados (divergem por clima) + nota de sensibilidade */}
            <div className="space-y-2">
              <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
                {e.personalized.scenarios.map((s) => (
                  <span key={s.name}>
                    <span className="capitalize text-muted-foreground">{s.name}: </span>
                    <span className="font-medium tabular-nums">{formatNumber(s.yield_sc_ha)} sc/ha</span>
                  </span>
                ))}
              </div>
              {e.water_sensitivity_note && (
                <p className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800">
                  {e.water_sensitivity_note}
                </p>
              )}
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

      {/* RECOMENDAÇÕES ACIONÁVEIS */}
      {e && e.recommendations.length > 0 && (
        <Card className="border-green-200">
          <CardHeader>
            <CardTitle>O que mais vale corrigir neste talhão</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-xs text-muted-foreground">
              Ações que dependem de manejo (não estruturais), ordenadas pelo ganho de
              produtividade ao corrigir. Estimativa agronômica — confira com seu agrônomo.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Ganho</th>
                    <th className="px-3 py-2 font-medium">Ação</th>
                    <th className="px-3 py-2 font-medium">De → para</th>
                  </tr>
                </thead>
                <tbody>
                  {e.recommendations.map((r) => (
                    <tr key={r.key} className="border-t border-border">
                      <td className="px-3 py-2 font-medium tabular-nums text-green-700">
                        +{formatNumber(r.gain_sc_ha)} sc/ha
                        <span className="ml-1 text-xs text-muted-foreground">
                          (+{formatNumber(r.gain_pct)}%)
                        </span>
                      </td>
                      <td className="px-3 py-2">{r.question}</td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {r.current_label} → <span className="font-medium text-foreground">{r.target_label}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
