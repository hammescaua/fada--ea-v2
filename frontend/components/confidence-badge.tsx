"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

/**
 * Selo de confiança — traduz a Calibração técnica num sinal simples e honesto.
 * Mostra a cobertura observada do intervalo de 80% no backtest. Some se ausente.
 */
export function ConfidenceBadge() {
  const { data } = useQuery({
    queryKey: ["calibration"],
    queryFn: api.getCalibration,
    retry: false,
    staleTime: 5 * 60_000,
  });

  if (!data) return null;
  const pct = formatNumber(data.regional.coverage_80 * 100, 0);

  return (
    <div className="rounded-lg border border-brand-100 bg-brand-50 px-4 py-3 text-sm text-brand-800">
      Selo de confiança: nosso intervalo de 80% conteve a produtividade real em{" "}
      <span className="font-semibold">~{pct}%</span> das safras no histórico (backtest).{" "}
      <Link href="/calibration" className="underline">
        Sobre o modelo
      </Link>
    </div>
  );
}
