"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import {
  api,
  type AssistantRequest,
  type AssistantResponse,
} from "@/lib/api";
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
    mutation.mutate({
      message: trimmed,
      municipality: municipality || null,
    });
    setMessage("");
  };

  return (
    <div>
      <PageHeader
        title="Assistente FADA"
        description="Faça perguntas em linguagem natural sobre produtividade, plantio e riscos da soja no RS."
      />

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
            <div className="flex h-full items-center justify-center text-center text-sm text-muted-foreground">
              Comece perguntando, por exemplo:
              <br />
              &ldquo;Qual a melhor data de plantio em Santa Rosa?&rdquo;
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
