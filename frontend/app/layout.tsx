import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Nav } from "@/components/nav";

export const metadata: Metadata = {
  title: "FADA — Farm AI Decision Agent",
  description:
    "Inteligência agrícola para soja no Rio Grande do Sul: produtividade esperada, janela de plantio e captura de dados de campo.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>
        <Providers>
          <div className="flex min-h-screen flex-col md:flex-row">
            <Nav />
            <main className="flex-1 overflow-x-hidden px-5 py-8 md:px-10 md:py-10">
              <div className="mx-auto w-full max-w-5xl">{children}</div>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
