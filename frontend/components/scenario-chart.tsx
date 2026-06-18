"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Scenario } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

const COLORS: Record<string, string> = {
  pessimista: "#dc2626",
  normal: "#2563eb",
  otimista: "#16a34a",
};

function colorFor(name: string): string {
  return COLORS[name.toLowerCase()] ?? "#16a34a";
}

export function ScenarioChart({ scenarios }: { scenarios: Scenario[] }) {
  const data = scenarios.map((s) => ({
    name: s.name.charAt(0).toUpperCase() + s.name.slice(1),
    raw: s.name,
    yield: Number(s.yield_sc_ha.toFixed(1)),
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis
            dataKey="name"
            tickLine={false}
            axisLine={false}
            fontSize={12}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            fontSize={12}
            width={48}
            unit=" sc"
          />
          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
            formatter={(value: number) => [
              `${formatNumber(value)} sc/ha`,
              "Produtividade",
            ]}
          />
          <Bar dataKey="yield" radius={[6, 6, 0, 0]} maxBarSize={90}>
            {data.map((entry) => (
              <Cell key={entry.raw} fill={colorFor(entry.raw)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
