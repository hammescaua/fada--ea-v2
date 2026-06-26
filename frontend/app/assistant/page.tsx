"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import {
  api,
  type AssistantRequest,
  type AssistantResponse,
} from "@/lib/api";
import { useFarmContext } from "@/lib/context";
import { PageHeader } from "@/components/page-header";
import { MunicipalitySelect } from "@/components/municipality-select";
import { ErrorBlock, Spinner } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  intent?: string;
}

export default function AssistantPage() {
  const ctx = useFarmContext();
  const [municipality, setMunicipality] = React.useState("");
  const [message, setMessage] = React.useState("");
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  const mutation = useMutation<AssistantResponse, Error, AssistantRequest>({
    mutationFn: api.assistant,
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.answer, intent: data.intent },
      ]);
    },
  });

  React.useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, mutation.isPending]);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || mutation.isPending) return;
    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    // Contexto global (fazenda/safra) habilita perguntas de custo/orçamento/
    // decisão/personalização. O backend já aceita estes campos.
    mutation.mutate({
      message: trimmed,
      municipality: municipality || null,
      farm_id: ctx.farmId,
      crop_cycle_id: ctx.cropCycleId,
    });
    setMessage("");
  };

  return (
    <div>
      <PageHeader
        title="Assistente FADA"
        description="Pergunte sobre números (produtividade, plantio, custos, risco) — respondidos pelo domínio — ou sobre o porquê agronômico — explicado com fonte citada. O FADA nunca inventa número."
      />

      {ctx.farmId !== null && (
        <p className="mb-4 text-sm text-muted-foreground">
          Respondendo sobre:{" "}
          <span className="font-medium text-foreground">{ctx.farmName}</span>
          {ctx.cropCycleLabel && (
            <>
              {" · "}
              <span className="font-medium text-foreground">{ctx.cropCycleLabel}</span>
            </>
          )}
          . Pergunte também sobre custos, orçamento e atenção dos talhões.
        </p>
      )}

      <div className="mb-4 max-w-xs space-y-2">
        <Label htmlFor="municipality">Município (contexto opcional)</Label>
        <MunicipalitySelect
          id="municipality"
          value={municipality}
          onChange={setMunicipality}
          includeEmpty
          emptyLabel="Nenhum"
        />
      </div>

      <div className="flex h-[60vh] flex-col rounded-lg border border-border bg-card">
        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 && !mutation.isPending && (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-sm text-muted-foreground">
              <span>Experimente perguntar:</span>
              <div className="flex flex-wrap justify-center gap-2">
                {[
                  "Qual a melhor data de plantio em Santa Rosa?",
                  "Por que aplicar fungicida na soja?",
                  "O que é veranico?",
                  "Vale a pena fazer inoculação?",
                ].map((ex) => (
                  <button
                    key={ex}
                    type="button"
                    onClick={() => setMessage(ex)}
                    className="rounded-full border border-border px-3 py-1 text-xs hover:bg-muted hover:text-foreground"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={
                m.role === "user" ? "flex justify-end" : "flex justify-start"
              }
            >
              <div
                className={
                  "max-w-[80%] rounded-lg px-4 py-2 text-sm " +
                  (m.role === "user"
                    ? "bg-brand-600 text-white"
                    : "border border-border bg-muted/40 text-foreground")
                }
              >
                {m.role === "assistant" && m.intent && (
                  <div className="mb-1">
                    <Badge variant="secondary">{m.intent}</Badge>
                  </div>
                )}
                <p className="whitespace-pre-line leading-relaxed">{m.text}</p>
              </div>
            </div>
          ))}
          {mutation.isPending && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/40 px-4 py-2 text-sm text-muted-foreground">
                <Spinner /> Pensando...
              </div>
            </div>
          )}
        </div>

        {mutation.isError && (
          <div className="border-t border-border p-3">
            <ErrorBlock error={mutation.error} />
          </div>
        )}

        <form
          onSubmit={onSubmit}
          className="flex items-center gap-2 border-t border-border p-3"
        >
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Escreva sua pergunta..."
            aria-label="Mensagem"
          />
          <Button type="submit" disabled={!message.trim() || mutation.isPending}>
            Enviar
          </Button>
        </form>
      </div>
    </div>
  );
}
