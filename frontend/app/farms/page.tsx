"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  api,
  type Farm,
  type Field,
  type CropCycle,
  type YieldObservation,
} from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { useMunicipalities } from "@/components/municipality-select";
import { ErrorBlock, LoadingBlock, Spinner } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { formatNumber, formatDateBR } from "@/lib/utils";

function StepBadge({ n, done }: { n: number; done: boolean }) {
  return (
    <span
      className={
        "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-semibold " +
        (done
          ? "bg-brand-600 text-white"
          : "border border-border bg-muted text-muted-foreground")
      }
    >
      {n}
    </span>
  );
}

export default function FarmsPage() {
  const qc = useQueryClient();
  const municipalities = useMunicipalities();

  // ---- queries ----
  const farmsQuery = useQuery<Farm[]>({
    queryKey: ["farms"],
    queryFn: api.getFarms,
  });

  const [selectedFarmId, setSelectedFarmId] = React.useState<number | null>(
    null
  );
  const [selectedFieldId, setSelectedFieldId] = React.useState<number | null>(
    null
  );
  const [activeCycle, setActiveCycle] = React.useState<CropCycle | null>(null);

  const fieldsQuery = useQuery<Field[]>({
    queryKey: ["fields", selectedFarmId],
    queryFn: () => api.getFields(selectedFarmId as number),
    enabled: selectedFarmId !== null,
  });

  const observationsQuery = useQuery<YieldObservation[]>({
    queryKey: ["yield-observations"],
    queryFn: api.getYieldObservations,
  });

  // ---- farm form ----
  const [farmName, setFarmName] = React.useState("");
  const [farmMunicipalityCode, setFarmMunicipalityCode] = React.useState("");
  const createFarm = useMutation({
    mutationFn: api.createFarm,
    onSuccess: (farm) => {
      setFarmName("");
      setFarmMunicipalityCode("");
      setSelectedFarmId(farm.id);
      qc.invalidateQueries({ queryKey: ["farms"] });
    },
  });

  // ---- field form ----
  const [fieldName, setFieldName] = React.useState("");
  const [fieldArea, setFieldArea] = React.useState("");
  const createField = useMutation({
    mutationFn: (vars: { farmId: number }) =>
      api.createField(vars.farmId, {
        name: fieldName,
        area_ha: Number(fieldArea),
      }),
    onSuccess: (field) => {
      setFieldName("");
      setFieldArea("");
      setSelectedFieldId(field.id);
      qc.invalidateQueries({ queryKey: ["fields", selectedFarmId] });
    },
  });

  // ---- crop cycle form ----
  const [cycleSeason, setCycleSeason] = React.useState("2025/26");
  const [cyclePlantingDate, setCyclePlantingDate] = React.useState("");
  const createCycle = useMutation({
    mutationFn: (vars: { fieldId: number }) =>
      api.createCropCycle(vars.fieldId, {
        crop: "soja",
        season: cycleSeason,
        planting_date: cyclePlantingDate || undefined,
      }),
    onSuccess: (cycle) => {
      setActiveCycle(cycle);
    },
  });

  // ---- yield observation form ----
  const [actualYield, setActualYield] = React.useState("");
  const [obsArea, setObsArea] = React.useState("");
  const [obsPlanting, setObsPlanting] = React.useState("");
  const [obsHarvest, setObsHarvest] = React.useState("");
  const [cultivar, setCultivar] = React.useState("");
  const [notes, setNotes] = React.useState("");
  const createObs = useMutation({
    mutationFn: (vars: { cropCycleId: number }) =>
      api.createYieldObservation({
        crop_cycle_id: vars.cropCycleId,
        actual_yield_sc_ha: Number(actualYield),
        area_ha: Number(obsArea),
        actual_planting_date: obsPlanting || undefined,
        actual_harvest_date: obsHarvest || undefined,
        cultivar: cultivar || undefined,
        notes: notes || undefined,
      }),
    onSuccess: () => {
      setActualYield("");
      setObsArea("");
      setObsPlanting("");
      setObsHarvest("");
      setCultivar("");
      setNotes("");
      setActiveCycle(null);
      qc.invalidateQueries({ queryKey: ["yield-observations"] });
    },
  });

  const municipalityName = (code: number) =>
    municipalities.data?.find((m) => m.code === code)?.name ?? `#${code}`;

  const selectedFarm = farmsQuery.data?.find((f) => f.id === selectedFarmId);
  const selectedField = fieldsQuery.data?.find(
    (f) => f.id === selectedFieldId
  );

  return (
    <div>
      <PageHeader
        title="Captura de Dados de Campo"
        description="Registre safras reais para que a FADA aprenda e melhore suas previsões a cada temporada. Esta é a base do aprimoramento contínuo do modelo."
      />

      <div className="mb-8 rounded-lg border border-brand-100 bg-brand-50 p-4 text-sm text-brand-800">
        <span className="font-semibold">Por que isso importa: </span>
        cada produtividade real informada calibra os modelos da FADA, reduzindo
        a incerteza nas próximas safras. Quanto mais dados de campo, melhores as
        recomendações.
      </div>

      <div className="space-y-6">
        {/* STEP 1 — FARM */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <StepBadge n={1} done={selectedFarmId !== null} />
              <CardTitle>Fazenda</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!farmName || !farmMunicipalityCode) return;
                createFarm.mutate({
                  name: farmName,
                  municipality_code: Number(farmMunicipalityCode),
                });
              }}
              className="grid grid-cols-1 gap-4 md:grid-cols-3 md:items-end"
            >
              <div className="space-y-2">
                <Label htmlFor="farmName">Nome da fazenda</Label>
                <Input
                  id="farmName"
                  value={farmName}
                  onChange={(e) => setFarmName(e.target.value)}
                  placeholder="Ex.: Fazenda Santa Clara"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="farmMunicipality">Município</Label>
                <Select
                  id="farmMunicipality"
                  value={farmMunicipalityCode}
                  onChange={(e) => setFarmMunicipalityCode(e.target.value)}
                  disabled={municipalities.isLoading}
                >
                  <option value="">Selecione...</option>
                  {municipalities.data?.map((m) => (
                    <option key={m.code} value={m.code}>
                      {m.name}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <Button
                  type="submit"
                  disabled={
                    !farmName || !farmMunicipalityCode || createFarm.isPending
                  }
                >
                  {createFarm.isPending && <Spinner />}
                  Criar fazenda
                </Button>
              </div>
            </form>
            {createFarm.isError && <ErrorBlock error={createFarm.error} />}

            {farmsQuery.isLoading && <LoadingBlock label="Carregando fazendas..." />}
            {farmsQuery.isError && <ErrorBlock error={farmsQuery.error} />}
            {farmsQuery.data && farmsQuery.data.length > 0 && (
              <div className="space-y-2">
                <Label>Selecionar fazenda existente</Label>
                <Select
                  value={selectedFarmId === null ? "" : String(selectedFarmId)}
                  onChange={(e) => {
                    const v = e.target.value;
                    setSelectedFarmId(v ? Number(v) : null);
                    setSelectedFieldId(null);
                    setActiveCycle(null);
                  }}
                >
                  <option value="">Selecione...</option>
                  {farmsQuery.data.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name} — {municipalityName(f.municipality_code)}
                    </option>
                  ))}
                </Select>
              </div>
            )}
          </CardContent>
        </Card>

        {/* STEP 2 — FIELD */}
        <Card className={selectedFarmId === null ? "opacity-60" : ""}>
          <CardHeader>
            <div className="flex items-center gap-3">
              <StepBadge n={2} done={selectedFieldId !== null} />
              <CardTitle>Talhão</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedFarmId === null ? (
              <p className="text-sm text-muted-foreground">
                Selecione ou crie uma fazenda primeiro.
              </p>
            ) : (
              <>
                <p className="text-sm text-muted-foreground">
                  Fazenda selecionada:{" "}
                  <span className="font-medium text-foreground">
                    {selectedFarm?.name}
                  </span>
                </p>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!fieldName || !fieldArea) return;
                    createField.mutate({ farmId: selectedFarmId });
                  }}
                  className="grid grid-cols-1 gap-4 md:grid-cols-3 md:items-end"
                >
                  <div className="space-y-2">
                    <Label htmlFor="fieldName">Nome do talhão</Label>
                    <Input
                      id="fieldName"
                      value={fieldName}
                      onChange={(e) => setFieldName(e.target.value)}
                      placeholder="Ex.: Talhão 1"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="fieldArea">Área (ha)</Label>
                    <Input
                      id="fieldArea"
                      type="number"
                      min="0"
                      step="0.1"
                      value={fieldArea}
                      onChange={(e) => setFieldArea(e.target.value)}
                      placeholder="Ex.: 50"
                    />
                  </div>
                  <div>
                    <Button
                      type="submit"
                      disabled={!fieldName || !fieldArea || createField.isPending}
                    >
                      {createField.isPending && <Spinner />}
                      Criar talhão
                    </Button>
                  </div>
                </form>
                {createField.isError && <ErrorBlock error={createField.error} />}

                {fieldsQuery.isLoading && (
                  <LoadingBlock label="Carregando talhões..." />
                )}
                {fieldsQuery.data && fieldsQuery.data.length > 0 && (
                  <div className="space-y-2">
                    <Label>Selecionar talhão</Label>
                    <Select
                      value={
                        selectedFieldId === null ? "" : String(selectedFieldId)
                      }
                      onChange={(e) => {
                        const v = e.target.value;
                        setSelectedFieldId(v ? Number(v) : null);
                        setActiveCycle(null);
                      }}
                    >
                      <option value="">Selecione...</option>
                      {fieldsQuery.data.map((f) => (
                        <option key={f.id} value={f.id}>
                          {f.name} — {formatNumber(f.area_ha)} ha
                        </option>
                      ))}
                    </Select>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* STEP 3 — CROP CYCLE */}
        <Card className={selectedFieldId === null ? "opacity-60" : ""}>
          <CardHeader>
            <div className="flex items-center gap-3">
              <StepBadge n={3} done={activeCycle !== null} />
              <CardTitle>Ciclo de cultivo</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedFieldId === null ? (
              <p className="text-sm text-muted-foreground">
                Selecione ou crie um talhão primeiro.
              </p>
            ) : (
              <>
                <p className="text-sm text-muted-foreground">
                  Talhão selecionado:{" "}
                  <span className="font-medium text-foreground">
                    {selectedField?.name}
                  </span>
                </p>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    createCycle.mutate({ fieldId: selectedFieldId });
                  }}
                  className="grid grid-cols-1 gap-4 md:grid-cols-4 md:items-end"
                >
                  <div className="space-y-2">
                    <Label htmlFor="cycleCrop">Cultura</Label>
                    <Input id="cycleCrop" value="soja" disabled readOnly />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cycleSeason">Safra</Label>
                    <Input
                      id="cycleSeason"
                      value={cycleSeason}
                      onChange={(e) => setCycleSeason(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cyclePlanting">Data de plantio</Label>
                    <Input
                      id="cyclePlanting"
                      type="date"
                      value={cyclePlantingDate}
                      onChange={(e) => setCyclePlantingDate(e.target.value)}
                    />
                  </div>
                  <div>
                    <Button type="submit" disabled={createCycle.isPending}>
                      {createCycle.isPending && <Spinner />}
                      Criar ciclo
                    </Button>
                  </div>
                </form>
                {createCycle.isError && <ErrorBlock error={createCycle.error} />}
                {activeCycle && (
                  <p className="rounded-md bg-brand-50 px-3 py-2 text-sm text-brand-800">
                    Ciclo criado: soja · {activeCycle.season} · colheita{" "}
                    {activeCycle.harvest_year}. Registre a produtividade abaixo.
                  </p>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* STEP 4 — YIELD OBSERVATION */}
        <Card className={activeCycle === null ? "opacity-60" : ""}>
          <CardHeader>
            <div className="flex items-center gap-3">
              <StepBadge n={4} done={false} />
              <CardTitle>Produtividade observada</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {activeCycle === null ? (
              <p className="text-sm text-muted-foreground">
                Crie um ciclo de cultivo primeiro.
              </p>
            ) : (
              <>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!actualYield || !obsArea) return;
                    createObs.mutate({ cropCycleId: activeCycle.id });
                  }}
                  className="grid grid-cols-1 gap-4 md:grid-cols-2"
                >
                  <div className="space-y-2">
                    <Label htmlFor="actualYield">
                      Produtividade real (sc/ha)
                    </Label>
                    <Input
                      id="actualYield"
                      type="number"
                      min="0"
                      step="0.1"
                      value={actualYield}
                      onChange={(e) => setActualYield(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="obsArea">Área colhida (ha)</Label>
                    <Input
                      id="obsArea"
                      type="number"
                      min="0"
                      step="0.1"
                      value={obsArea}
                      onChange={(e) => setObsArea(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="obsPlanting">Data de plantio real</Label>
                    <Input
                      id="obsPlanting"
                      type="date"
                      value={obsPlanting}
                      onChange={(e) => setObsPlanting(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="obsHarvest">Data de colheita real</Label>
                    <Input
                      id="obsHarvest"
                      type="date"
                      value={obsHarvest}
                      onChange={(e) => setObsHarvest(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cultivar">Cultivar</Label>
                    <Input
                      id="cultivar"
                      value={cultivar}
                      onChange={(e) => setCultivar(e.target.value)}
                      placeholder="Opcional"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="notes">Observações</Label>
                    <Input
                      id="notes"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Opcional"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Button
                      type="submit"
                      disabled={!actualYield || !obsArea || createObs.isPending}
                    >
                      {createObs.isPending && <Spinner />}
                      Registrar produtividade
                    </Button>
                  </div>
                </form>
                {createObs.isError && <ErrorBlock error={createObs.error} />}
              </>
            )}
          </CardContent>
        </Card>

        {/* OBSERVATIONS TABLE */}
        <Card>
          <CardHeader>
            <CardTitle>Produtividades registradas</CardTitle>
          </CardHeader>
          <CardContent>
            {observationsQuery.isLoading && (
              <LoadingBlock label="Carregando registros..." />
            )}
            {observationsQuery.isError && (
              <ErrorBlock error={observationsQuery.error} />
            )}
            {observationsQuery.data && observationsQuery.data.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Nenhuma produtividade registrada ainda.
              </p>
            )}
            {observationsQuery.data && observationsQuery.data.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2 font-medium">Ciclo</th>
                      <th className="px-3 py-2 font-medium">Prod. (sc/ha)</th>
                      <th className="px-3 py-2 font-medium">Área (ha)</th>
                      <th className="px-3 py-2 font-medium">Plantio</th>
                      <th className="px-3 py-2 font-medium">Colheita</th>
                      <th className="px-3 py-2 font-medium">Cultivar</th>
                      <th className="px-3 py-2 font-medium">Notas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {observationsQuery.data.map((o) => (
                      <tr key={o.id} className="border-t border-border">
                        <td className="px-3 py-2 tabular-nums">
                          #{o.crop_cycle_id}
                        </td>
                        <td className="px-3 py-2 font-medium tabular-nums text-brand-700">
                          {formatNumber(o.actual_yield_sc_ha)}
                        </td>
                        <td className="px-3 py-2 tabular-nums">
                          {formatNumber(o.area_ha)}
                        </td>
                        <td className="px-3 py-2">
                          {formatDateBR(o.actual_planting_date)}
                        </td>
                        <td className="px-3 py-2">
                          {formatDateBR(o.actual_harvest_date)}
                        </td>
                        <td className="px-3 py-2">{o.cultivar ?? "—"}</td>
                        <td className="px-3 py-2 text-muted-foreground">
                          {o.notes ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
