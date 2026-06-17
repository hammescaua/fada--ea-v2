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
import type { CostBreakdown, FinancialScenario } from "@/lib/api";
import { costCategoryLabel } from "@/lib/events";
import { formatBRL } from "@/lib/utils";

export function CostByCategoryChart({
  breakdown,
}: {
  breakdown: CostBreakdown;
}) {
  const data = Object.entries(breakdown.cost_by_category).map(([k, v]) => ({
    name: costCategoryLabel(k),
    value: Number(v.toFixed(2)),
  }));

  if (data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Nenhum custo por categoria.
      </p>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 8, right: 16, left: 8, bottom: 0 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            horizontal={false}
            stroke="#e5e7eb"
          />
          <XAxis
            type="number"
            tickLine={false}
            axisLine={false}
            fontSize={12}
            tickFormatter={(v: number) => formatBRL(v, 0)}
          />
          <YAxis
            type="category"
            dataKey="name"
            tickLine={false}
            axisLine={false}
            fontSize={12}
            width={120}
          />
          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
            formatter={(value: number) => [formatBRL(value), "Custo"]}
          />
          <Bar
            dataKey="value"
            radius={[0, 6, 6, 0]}
            maxBarSize={28}
            fill="#16a34a"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ProfitScenarioChart({
  scenarios,
}: {
  scenarios: FinancialScenario[];
}) {
  const data = scenarios.map((s) => ({
    name: s.name,
    profit: Number(s.profit.toFixed(2)),
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={12} />
          <YAxis
            tickLine={false}
            axisLine={false}
            fontSize={12}
            width={72}
            tickFormatter={(v: number) => formatBRL(v, 0)}
          />
          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
            formatter={(value: number) => [formatBRL(value), "Lucro"]}
          />
          <Bar dataKey="profit" radius={[6, 6, 0, 0]} maxBarSize={90}>
            {data.map((entry) => (
              <Cell
                key={entry.name}
                fill={entry.profit >= 0 ? "#16a34a" : "#dc2626"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
