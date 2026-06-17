"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Inteligência Regional" },
  { href: "/planting/simulate", label: "Simular Data de Plantio" },
  { href: "/planting/optimize", label: "Otimizar Janela" },
  { href: "/farms", label: "Captura de Dados" },
  { href: "/safra", label: "Safra" },
  { href: "/financeiro", label: "Financeiro" },
  { href: "/adaptive", label: "Inteligência Adaptativa" },
  { href: "/calibration", label: "Calibração" },
  { href: "/assistant", label: "Assistente" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-border bg-card md:h-screen md:w-64 md:border-b-0 md:border-r">
      <div className="flex items-center gap-2 px-6 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-brand-600 text-white font-bold">
          F
        </div>
        <div className="leading-tight">
          <div className="text-base font-semibold">FADA</div>
          <div className="text-xs text-muted-foreground">
            Farm AI Decision Agent
          </div>
        </div>
      </div>
      <nav className="flex flex-row flex-wrap gap-1 px-3 pb-4 md:flex-col md:flex-nowrap">
        {links.map((link) => {
          const active =
            link.href === "/"
              ? pathname === "/"
              : pathname.startsWith(link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-brand-50 text-brand-700"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto hidden px-6 py-4 text-xs text-muted-foreground md:block">
        Soja · Rio Grande do Sul
      </div>
    </aside>
  );
}
