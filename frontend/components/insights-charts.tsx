"use client";

import {
  Bar,
  BarChart,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { FieldSummary } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

/** Bias de cada talhão vs. expectativa regional (verde = acima, vermelho = abaixo). */
export function FieldBiasChart({ fields }: { fields: FieldSummary[] }) {
  const data = fields.map((f) => ({
    name: f.field_name,
    bias: f.bias_vs_region_pct,
    fill: f.bias_vs_region_pct >= 0 ? "#16a34a" : "#dc2626",
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(140, data.length * 48)}>
      <BarChart data={data} layout="vertical" margin={{ left: 16, right: 24 }}>
        <XAxis
          type="number"
          tickFormatter={(v) => `${formatNumber(Number(v))}%`}
          fontSize={12}
          stroke="#9ca3af"
        />
        <YAxis
          type="category"
          dataKey="name"
          width={110}
          fontSize={12}
          stroke="#6b7280"
        />
        <ReferenceLine x={0} stroke="#6b7280" strokeWidth={1} />
        <Tooltip
          cursor={{ fill: "rgba(0,0,0,0.04)" }}
          formatter={(value) => [
            `${formatNumber(Number(value))}%`,
            "Bias vs. região",
          ]}
        />
        <Bar dataKey="bias" radius={[0, 6, 6, 0]} maxBarSize={32}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
