"use client";

import * as React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api, type Field } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

/**
 * Guia de próximo passo — resolve a confusão de "o que faço agora?".
 *
 * Lê o estado real do agricultor (fazenda → talhão → perfil → plano) e mostra
 * UM único próximo passo claro, com o atalho certo. À medida que o produtor
 * avança, o passo muda sozinho. Os 4 passos são a jornada V2 inteira numa frase.
 */

type Step = {
  n: number;
  title: string;
  detail: string;
  href: string;
  cta: string;
};

const STEPS_TOTAL = 4;

function pickStep(args: {
  hasFarms: boolean;
  fields: Field[] | undefined;
  profileFilled: boolean | undefined;
  hasPlan: boolean;
}): Step | null {
  const { hasFarms, fields, profileFilled, hasPlan } = args;

  if (!hasFarms) {
    return {
      n: 1,
      title: "Cadastre sua fazenda",
      detail: "Comece informando o município e o nome da fazenda. Leva 1 minuto.",
      href: "/onboarding",
      cta: "Criar minha fazenda",
    };
  }
  if (fields && fields.length === 0) {
    return {
      n: 1,
      title: "Adicione um talhão",
      detail: "Cadastre ao menos um talhão (nome e área) para começar a previsão.",
      href: "/farms",
      cta: "Adicionar talhão",
    };
  }
  if (fields === undefined) return null; // ainda carregando talhões
  if (profileFilled === false) {
    return {
      n: 2,
      title: "Complete o Perfil do Talhão",
      detail:
        "Informe solo, manejo e cultivar (ou use a sugestão pela localização). " +
        "É o que personaliza a previsão para a SUA lavoura, antes de plantar.",
      href: "/perfil-talhao",
      cta: "Preencher o Perfil do Talhão",
    };
  }
  if (profileFilled === undefined) return null; // ainda carregando perfil
  if (!hasPlan) {
    return {
      n: 3,
      title: "Planeje a safra",
      detail:
        "Veja margem esperada, melhor janela de plantio (ZARC) e o que mais " +
        "move sua produtividade e lucro neste talhão.",
      href: "/planejar-safra",
      cta: "Planejar a safra",
    };
  }
  return {
    n: 4,
    title: "Acompanhe a lavoura",
    detail:
      "Registre suas operações (pulverização, adubação) para o FADA aprender com " +
      "seus resultados e afinar as próximas previsões.",
    href: "/safra",
    cta: "Acompanhar minha lavoura",
  };
}

export function JourneyGuide({
  farmId,
  hasFarms,
}: {
  farmId: number | null;
  hasFarms: boolean;
}) {
  const fieldsQuery = useQuery({
    queryKey: ["fields", farmId],
    queryFn: () => api.getFields(farmId as number),
    enabled: farmId !== null && hasFarms,
  });

  const firstFieldId = fieldsQuery.data?.[0]?.id ?? null;
  const profileQuery = useQuery({
    queryKey: ["field-profile", firstFieldId],
    queryFn: () => api.getFieldProfile(firstFieldId as number),
    enabled: firstFieldId !== null,
  });

  const dashQuery = useQuery({
    queryKey: ["dashboard", farmId],
    queryFn: () => api.getDashboard(farmId as number),
    enabled: farmId !== null && hasFarms,
  });

  const fields = hasFarms ? fieldsQuery.data : [];
  // Perfil "pronto" para a jornada = ao menos metade dos fatores essenciais.
  const profileFilled =
    firstFieldId === null
      ? undefined
      : profileQuery.data
        ? (profileQuery.data.completeness?.pct ?? 0) >= 50
        : profileQuery.isLoading
          ? undefined
          : false;
  const hasPlan = !!dashQuery.data?.agenda.next_operation;

  const step = pickStep({ hasFarms, fields, profileFilled, hasPlan });
  if (step === null) return null;

  return (
    <Card className="border-brand-200 bg-brand-50/60">
      <CardContent className="flex flex-col gap-3 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white">
              {step.n}
            </span>
            <span className="text-xs font-semibold uppercase tracking-wide text-brand-700">
              Próximo passo · {step.n} de {STEPS_TOTAL}
            </span>
          </div>
          <div className="text-base font-semibold">{step.title}</div>
          <p className="max-w-xl text-sm text-muted-foreground">{step.detail}</p>
        </div>
        <Link href={step.href} className="shrink-0">
          <Button>{step.cta}</Button>
        </Link>
      </CardContent>
    </Card>
  );
}
