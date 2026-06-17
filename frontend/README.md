# FADA — Frontend

Web app for the **Farm AI Decision Agent (FADA)** — agricultural intelligence
for soybean (`soja`) in Rio Grande do Sul (`RS`).

Built with Next.js 14 (App Router) + TypeScript, Tailwind CSS,
TanStack React Query v5 and Recharts.

## Pages

- `/` — **Inteligência Regional**: expected yield, scenarios, climatic risks and planting window.
- `/planting/simulate` — **Simular Data de Plantio**: yield/risk for a specific planting date.
- `/planting/optimize` — **Otimizar Janela**: ranked top planting dates.
- `/farms` — **Captura de Dados**: guided ground-truth capture (farm → field → crop cycle → yield).
- `/assistant` — **Assistente**: natural-language chat.

## Requirements

- Node.js 18.18+ (tested on Node 22)
- The FADA backend running and reachable (default `http://localhost:8000`).

## Setup

```bash
npm install
```

Configure the API base URL (optional — defaults to `http://localhost:8000`):

```bash
cp .env.local.example .env.local
# edit NEXT_PUBLIC_API_URL if your backend runs elsewhere
```

The client calls endpoints under `${NEXT_PUBLIC_API_URL}/api/v1`.

## Run

```bash
npm run dev      # development server at http://localhost:3000
npm run build    # production build
npm start        # serve the production build
npm run typecheck  # tsc --noEmit
```

## Environment variables

| Variable              | Default                 | Description                          |
| --------------------- | ----------------------- | ------------------------------------ |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL (no trailing slash) |
