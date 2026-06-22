"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useFarmContext } from "@/lib/context";
import { PageHeader } from "@/components/page-header";
import { ErrorBlock, LoadingBlock } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";

const STEPS = ["Fazenda", "Talhão", "Safra", "Pronto"];

function StepBadge({ n, current }: { n: number; current: number }) {
  const done = current > n;
  const active = current === n;
  return (
    <div className="flex items-center gap-2">
      <div
        className={
          "flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold " +
          (done
            ? "bg-brand-600 text-white"
            : active
              ? "bg-brand-100 text-brand-700 ring-2 ring-brand-600"
              : "bg-muted text-muted-foreground")
        }
      >
        {done ? "✓" : n}
      </div>
      <span className={active ? "text-sm font-medium" : "text-sm text-muted-foreground"}>
        {STEPS[n - 1]}
      </span>
    </div>
  );
}

export default function OnboardingPage() {
  const ctx = useFarmContext();
  const router = useRouter();
  const qc = useQueryClient();
  const [step, setStep] = React.useState(1);

  // Passo 1 — fazenda
  const munis = useQuery({ queryKey: ["municipalities"], queryFn: api.getMunicipalities });
  const [farmName, setFarmName] = React.useState("");
  const [muniCode, setMuniCode] = React.useState<number | "">("");

  const createFarm = useMutation({
    mutationFn: () =>
      api.createFarm({ name: farmName, municipality_code: Number(muniCode) }),
    onSuccess: (farm) => {
      ctx.setFarm(farm);
      qc.invalidateQueries({ queryKey: ["farms"] });
      setStep(2);
    },
  });

  // Passo 2 — talhão
  const [fieldName, setFieldName] = React.useState("");
  const [area, setArea] = React.useState("");
  const [fieldId, setFieldId] = React.useState<number | null>(null);

  const createField = useMutation({
    mutationFn: () =>
      api.createField(ctx.farmId as number, {
        name: fieldName,
        area_ha: Number(area),
      }),
    onSuccess: (field) => {
      setFieldId(field.id);
      setStep(3);
    },
  });

  // Passo 3 — safra
  const [season, setSeason] = React.useState("2026/27");
  const [target, setTarget] = React.useState("");
  const [price, setPrice] = React.useState("");

  const createCycle = useMutation({
    mutationFn: () =>
      api.createCropCycle(fieldId as number, {
        crop: "soja",
        season,
        planting_date: undefined,
      }),
    onSuccess: (cycle) => {
      // popula o contexto global para o app já abrir com a safra selecionada
      ctx.setCropCycle({
        id: cycle.id,
        field_id: cycle.field_id,
        field_name: fieldName,
        crop: cycle.crop,
        season: cycle.season,
        harvest_year: cycle.harvest_year,
        area_ha: Number(area),
        target_yield_sc_ha: target ? Number(target) : null,
        has_actual_yield: false,
      });
      // grava meta/preço se informados
      if (target || price) {
        api
          .updateCropCycle(cycle.id, {
            target_yield_sc_ha: target ? Number(target) : undefined,
            expected_price_per_bag: price ? Number(price) : undefined,
          })
          .catch(() => undefined);
      }
      qc.invalidateQueries({ queryKey: ["farm-cycles"] });
      setStep(4);
    },
  });

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <PageHeader
        title="Primeiros passos"
        description="Vamos criar sua fazenda em poucos passos. Sem códigos nem termos técnicos."
      />

      <div className="flex flex-wrap items-center gap-4">
        {[1, 2, 3, 4].map((n) => (
          <StepBadge key={n} n={n} current={step} />
        ))}
      </div>

      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>1. Sua fazenda</CardTitle>
          </CardHeader>
          <CardContent>
            {munis.isLoading ? (
              <LoadingBlock label="Carregando municípios…" />
            ) : munis.isError ? (
              <ErrorBlock error={munis.error} />
            ) : (
              <form
                className="space-y-4"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!farmName || muniCode === "") return;
                  createFarm.mutate();
                }}
              >
                <div className="space-y-2">
                  <Label htmlFor="fn">Nome da fazenda</Label>
                  <Input
                    id="fn"
                    value={farmName}
                    onChange={(e) => setFarmName(e.target.value)}
                    placeholder="Ex.: Fazenda Boa Vista"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="mc">Município</Label>
                  <Select
                    id="mc"
                    value={muniCode}
                    onChange={(e) =>
                      setMuniCode(e.target.value ? Number(e.target.value) : "")
                    }
                  >
                    <option value="">Selecione…</option>
                    {munis.data?.map((m) => (
                      <option key={m.code} value={m.code}>
                        {m.name}
                      </option>
                    ))}
                  </Select>
                </div>
                <Button
                  type="submit"
                  disabled={!farmName || muniCode === "" || createFarm.isPending}
                >
                  {createFarm.isPending ? "Criando…" : "Continuar"}
                </Button>
                {createFarm.isError && (
                  <ErrorBlock error={createFarm.error} />
                )}
              </form>
            )}
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>2. Seu primeiro talhão</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                if (!fieldName || !area) return;
                createField.mutate();
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="tn">Nome do talhão</Label>
                <Input
                  id="tn"
                  value={fieldName}
                  onChange={(e) => setFieldName(e.target.value)}
                  placeholder="Ex.: Talhão Norte"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ta">Área (hectares)</Label>
                <Input
                  id="ta"
                  type="number"
                  min="0"
                  value={area}
                  onChange={(e) => setArea(e.target.value)}
                  placeholder="Ex.: 100"
                />
              </div>
              <Button type="submit" disabled={!fieldName || !area || createField.isPending}>
                {createField.isPending ? "Salvando…" : "Continuar"}
              </Button>
              {createField.isError && <ErrorBlock error={createField.error} />}
            </form>
          </CardContent>
        </Card>
      )}

      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>3. Abrir a safra</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                if (!season) return;
                createCycle.mutate();
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="se">Safra</Label>
                <Input
                  id="se"
                  value={season}
                  onChange={(e) => setSeason(e.target.value)}
                  placeholder="2026/27"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="tg">Meta de produtividade (sc/ha)</Label>
                  <Input
                    id="tg"
                    type="number"
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                    placeholder="opcional"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="pr">Preço esperado (R$/sc)</Label>
                  <Input
                    id="pr"
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    placeholder="opcional"
                  />
                </div>
              </div>
              <Button type="submit" disabled={!season || createCycle.isPending}>
                {createCycle.isPending ? "Abrindo…" : "Concluir"}
              </Button>
              {createCycle.isError && <ErrorBlock error={createCycle.error} />}
            </form>
          </CardContent>
        </Card>
      )}

      {step === 4 && (
        <Card>
          <CardHeader>
            <CardTitle>Tudo pronto! 🎉</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Sua fazenda, talhão e safra estão criados e já selecionados no topo da
              página. A partir daqui você pode registrar operações, acompanhar custos e
              ver a estimativa da região.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button onClick={() => router.push("/home")}>Ir para o Início</Button>
              <Button variant="outline" onClick={() => router.push("/safra")}>
                Minha Lavoura
              </Button>
              <Button variant="outline" onClick={() => router.push("/")}>
                Estimativa da Região
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
