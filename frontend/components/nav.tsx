"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

// Destinos primários — os 5 trabalhos do agricultor (aparecem no menu inferior do
// celular). As joias do produto (previsão do talhão e plano de safra) vêm na frente.
const primary = [
  { href: "/home", label: "Início" },
  { href: "/perfil-talhao", label: "Meu Talhão" },
  { href: "/projecao", label: "Projeção de Safras" },
  { href: "/planejar-safra", label: "Planejar Safra" },
  { href: "/safra", label: "Minha Lavoura" },
  { href: "/assistant", label: "Assistente" },
];

// Ferramentas — agrupadas e colapsadas (analítico/avançado, linguagem de produtor).
const advanced = [
  { href: "/decisoes", label: "Onde olhar primeiro" },
  { href: "/financeiro", label: "Financeiro" },
  { href: "/credito", label: "Crédito & 2ª safra" },
  { href: "/planejamento", label: "Orçamento da safra" },
  { href: "/guia", label: "Guia agronômico" },
  { href: "/", label: "Estimativa da região" },
  { href: "/planting/optimize", label: "Melhor janela de plantio" },
  { href: "/planting/simulate", label: "Simular data de plantio" },
  { href: "/insights", label: "Análise dos talhões" },
  { href: "/adaptive", label: "Personalização (histórico)" },
  { href: "/farms", label: "Cadastro de dados" },
];

// Rodapé discreto — "sobre o modelo".
const footer = [
  { href: "/calibration", label: "Sobre o Modelo" },
  { href: "/system", label: "Sistema" },
];

function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

function linkClass(active: boolean): string {
  return cn(
    "rounded-md px-3 py-2 text-sm font-medium transition-colors",
    active
      ? "bg-brand-50 text-brand-700"
      : "text-muted-foreground hover:bg-muted hover:text-foreground"
  );
}

/** Sidebar — desktop. */
export function Nav() {
  const pathname = usePathname();
  const advancedActive = advanced.some((l) => isActive(pathname, l.href));
  const [open, setOpen] = React.useState(advancedActive);

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-card md:flex md:h-screen">
      <div className="flex items-center gap-2 px-6 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-brand-600 text-white font-bold">
          F
        </div>
        <div className="leading-tight">
          <div className="text-base font-semibold">FADA</div>
          <div className="text-xs text-muted-foreground">Decisão na lavoura</div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto px-3 pb-4">
        {primary.map((link) => (
          <Link key={link.href} href={link.href} className={linkClass(isActive(pathname, link.href))}>
            {link.label}
          </Link>
        ))}

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="mt-3 flex items-center justify-between rounded-md px-3 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground hover:bg-muted"
        >
          Ferramentas
          <span aria-hidden>{open ? "▾" : "▸"}</span>
        </button>
        {open &&
          advanced.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn("ml-2", linkClass(isActive(pathname, link.href)))}
            >
              {link.label}
            </Link>
          ))}

        <div className="mt-auto flex flex-col gap-1 border-t border-border pt-3">
          {footer.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn("text-xs", linkClass(isActive(pathname, link.href)))}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </nav>
    </aside>
  );
}

/** Bottom nav — mobile (5 destinos primários). */
export function BottomNav() {
  const pathname = usePathname();
  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-5 border-t border-border bg-card md:hidden">
      {primary.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={cn(
            "flex flex-col items-center gap-0.5 py-2 text-[11px] font-medium",
            isActive(pathname, link.href) ? "text-brand-700" : "text-muted-foreground"
          )}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
