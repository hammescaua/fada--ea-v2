"use client";

import { useQuery } from "@tanstack/react-query";
import { api, type DataSourceHealth, type SystemStatus } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { ErrorBlock, LoadingBlock } from "@/components/states";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Stat } from "@/components/stat";

function statusVariant(status: string): BadgeProps["variant"] {
  if (status === "ok") return "success";
  if (status === "degraded") return "warning";
  return "danger";
}

function sourceVariant(status: string): BadgeProps["variant"] {
  if (status === "atual" || status === "ok") return "success";
  if (status === "desatualizado") return "warning";
  return "secondary";
}

function ageLabel(d: DataSourceHealth): string {
  if (d.status === "ausente") return "ausente";
  if (d.age_days === null) return d.fetched_at ?? "—";
  if (d.age_days === 0) return "hoje";
  return `há ${d.age_days} dia${d.age_days === 1 ? "" : "s"}`;
}

const COUNT_LABELS: Record<string, string> = {
  farms: "Fazendas",
  fields: "Talhões",
  crop_cycles: "Safras",
  events: "Operações",
};

export default function SystemPage() {
  const query = useQuery<SystemStatus>({
    queryKey: ["system-status"],
    queryFn: api.getSystemStatus,
    refetchInterval: 30_000,
    retry: false,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Sistema"
        description="Status da plataforma: backend, banco, modelo e registros."
      />

      {query.isLoading ? (
        <LoadingBlock label="Consultando status…" />
      ) : query.isError ? (
        <ErrorBlock error={query.error} />
      ) : query.data ? (
        <>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle>Estado geral</CardTitle>
              <Badge variant={statusVariant(query.data.status)}>
                {query.data.status}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Versão</span>
                <span className="font-medium tabular-nums">{query.data.version}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">
                  Banco de dados ({query.data.database.url_scheme})
                </span>
                <Badge variant={statusVariant(query.data.database.status)}>
                  {query.data.database.status}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">
                  Modelo ({query.data.model.path})
                </span>
                <Badge variant={statusVariant(query.data.model.status)}>
                  {query.data.model.status}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Relatório de calibração</span>
                <Badge
                  variant={
                    query.data.calibration_report.present ? "success" : "secondary"
                  }
                >
                  {query.data.calibration_report.present ? "presente" : "ausente"}
                </Badge>
              </div>
              {query.data.llm && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Explicação (LLM)</span>
                  <Badge variant={query.data.llm.active ? "success" : "secondary"}>
                    {query.data.llm.label}
                  </Badge>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {Object.entries(query.data.counts).map(([key, value]) => (
              <Stat key={key} label={COUNT_LABELS[key] ?? key} value={`${value}`} />
            ))}
          </div>

          {query.data.data_sources && query.data.data_sources.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Fontes públicas — frescor dos dados</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                {query.data.data_sources.map((d) => (
                  <div
                    key={d.label}
                    className="flex flex-col gap-1 border-b border-border pb-2 last:border-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <span className="font-medium">{d.label}</span>
                      {d.source && (
                        <span className="text-muted-foreground"> · {d.source}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground tabular-nums">
                        {ageLabel(d)}
                      </span>
                      <Badge variant={sourceVariant(d.status)}>{d.status}</Badge>
                    </div>
                  </div>
                ))}
                <p className="text-xs text-muted-foreground">
                  Todos os números do FADA são datados. &quot;Desatualizado&quot; não
                  significa errado — apenas que vale revisar a fonte antes de decidir.
                </p>
              </CardContent>
            </Card>
          )}
        </>
      ) : null}
    </div>
  );
}
