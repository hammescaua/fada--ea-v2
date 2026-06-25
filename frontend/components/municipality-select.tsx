"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type Municipality } from "@/lib/api";
import { Select } from "@/components/ui/select";

export function useMunicipalities() {
  return useQuery<Municipality[]>({
    queryKey: ["municipalities"],
    queryFn: api.getMunicipalities,
  });
}

interface MunicipalitySelectProps {
  value: string;
  onChange: (name: string) => void;
  includeEmpty?: boolean;
  emptyLabel?: string;
  id?: string;
  disabled?: boolean;
}

export function MunicipalitySelect({
  value,
  onChange,
  includeEmpty = false,
  emptyLabel = "Selecione...",
  id,
  disabled = false,
}: MunicipalitySelectProps) {
  const { data, isLoading, isError } = useMunicipalities();

  return (
    <Select
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled || isLoading || isError}
    >
      {isLoading && <option value="">Carregando municípios...</option>}
      {isError && <option value="">Erro ao carregar municípios</option>}
      {!isLoading && !isError && (
        <>
          {(includeEmpty || !value) && <option value="">{emptyLabel}</option>}
          {data?.map((m) => (
            <option key={m.code} value={m.name}>
              {m.name}
            </option>
          ))}
        </>
      )}
    </Select>
  );
}
