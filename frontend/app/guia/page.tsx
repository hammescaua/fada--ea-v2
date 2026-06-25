"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type KnowledgeEntry } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { ErrorBlock, LoadingBlock } from "@/components/states";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function GuiaPage() {
  const [q, setQ] = React.useState("");
  const knowledge = useQuery<KnowledgeEntry[]>({
    queryKey: ["agronomic-knowledge"],
    queryFn: api.getAgronomicKnowledge,
    staleTime: Infinity,
  });

  const term = q.trim().toLowerCase();
  const entries = (knowledge.data ?? []).filter(
    (e) =>
      !term ||
      e.title.toLowerCase().includes(term) ||
      e.explanation.toLowerCase().includes(term)
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Guia Agronômico"
        description="Por que cada variável pesa na produtividade e na rentabilidade — explicado com fonte. O FADA explica e cita; nunca inventa número."
      />

      <Input
        placeholder="Buscar (ex.: ferrugem, calagem, veranico)…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        className="max-w-md"
      />

      {knowledge.isLoading && <LoadingBlock label="Carregando guia…" />}
      {knowledge.isError && <ErrorBlock error={knowledge.error} />}

      <div className="grid gap-4 md:grid-cols-2">
        {entries.map((e) => (
          <Card key={e.key}>
            <CardHeader>
              <CardTitle className="text-base">{e.title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p className="text-muted-foreground">{e.explanation}</p>
              <p>
                <span className="font-medium">Na prática: </span>
                <span className="text-muted-foreground">{e.practical}</span>
              </p>
              <p className="text-xs italic text-muted-foreground">
                Fonte: {e.sources.join("; ")}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
