"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ResidualPoint } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

/**
 * Bar chart of relative residual (%) per harvest year, with a zero reference
 * line. Positive residuals (farm above the regional fit) are green; negative
 * are red.
 */
export function ResidualPctChart({ history }: { history: ResidualPoint[] }) {
  const data = history.map((p) => ({
    year: p.harvest_year,
    residual_pct: Number(p.residual_pct.toFixed(1)),
  }));

  if (data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Sem histórico de resíduos disponível.
      </p>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis
            dataKey="year"
            tickLine={false}
            axisLine={false}
            fontSize={12}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            fontSize={12}
            width={48}
            tickFormatter={(v: number) => `${v}%`}
          />
          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
            formatter={(value: number) => [
              `${formatNumber(value)}%`,
              "Desvio relativo",
            ]}
            labelFormatter={(label) => `Safra ${label}`}
          />
          <ReferenceLine y={0} stroke="#6b7280" strokeWidth={1.5} />
          <Bar dataKey="residual_pct" radius={[4, 4, 0, 0]} maxBarSize={56}>
            {data.map((entry) => (
              <Cell
                key={entry.year}
                fill={entry.residual_pct >= 0 ? "#16a34a" : "#dc2626"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Line chart comparing observed yield (actual_sc_ha) against the regional
 * fitted yield (regional_fitted_sc_ha) per harvest year.
 */
export function ActualVsFittedChart({ history }: { history: ResidualPoint[] }) {
  const data = history.map((p) => ({
    year: p.harvest_year,
    actual: Number(p.actual_sc_ha.toFixed(1)),
    regional: Number(p.regional_fitted_sc_ha.toFixed(1)),
  }));

  if (data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Sem histórico disponível.
      </p>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis
            dataKey="year"
            tickLine={false}
            axisLine={false}
            fontSize={12}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            fontSize={12}
            width={48}
            tickFormatter={(v: number) => formatNumber(v, 0)}
          />
          <Tooltip
            formatter={(value: number, name) => [
              `${formatNumber(value)} sc/ha`,
              name === "actual" ? "Fazenda (real)" : "Regional (ajustado)",
            ]}
            labelFormatter={(label) => `Safra ${label}`}
          />
          <Legend
            formatter={(value) =>
              value === "actual" ? "Fazenda (real)" : "Regional (ajustado)"
            }
          />
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#16a34a"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
          <Line
            type="monotone"
            dataKey="regional"
            stroke="#2563eb"
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
