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
import type { CalibrationReport, ReliabilityPoint } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

const REGIONAL_COLOR = "#2563eb";
const PERSONALIZED_COLOR = "#16a34a";
const DIAGONAL_COLOR = "#6b7280";

/**
 * Reliability diagram: observed coverage (y) vs nominal coverage (x) for the
 * regional curve, plus the personalized curve and the identity diagonal y = x
 * (perfect calibration). Points above the diagonal = conservative
 * (underconfident); below = overconfident. Values are fractions 0..1 and are
 * rendered as percentages.
 */
export function ReliabilityChart({
  regional,
  personalized,
  showPersonalized,
}: {
  regional: ReliabilityPoint[];
  personalized: ReliabilityPoint[];
  showPersonalized: boolean;
}) {
  // Index the personalized curve by nominal so we can merge both series on a
  // single x axis (the nominal levels are shared between reports).
  const persByNominal = new Map<number, ReliabilityPoint>();
  for (const p of personalized) persByNominal.set(p.nominal, p);

  const data = regional.map((p) => {
    const pers = persByNominal.get(p.nominal);
    return {
      nominal: Number((p.nominal * 100).toFixed(1)),
      identity: Number((p.nominal * 100).toFixed(1)),
      regional: Number((p.observed * 100).toFixed(1)),
      regional_low: Number((p.wilson_low * 100).toFixed(1)),
      regional_high: Number((p.wilson_high * 100).toFixed(1)),
      personalized:
        pers != null ? Number((pers.observed * 100).toFixed(1)) : null,
    };
  });

  if (data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Sem curva de confiabilidade disponível.
      </p>
    );
  }

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="nominal"
            type="number"
            domain={[0, 100]}
            tickLine={false}
            axisLine={false}
            fontSize={12}
            tickFormatter={(v: number) => `${v}%`}
            label={{
              value: "Cobertura nominal",
              position: "insideBottom",
              offset: -2,
              fontSize: 12,
              fill: "#6b7280",
            }}
          />
          <YAxis
            type="number"
            domain={[0, 100]}
            tickLine={false}
            axisLine={false}
            fontSize={12}
            width={48}
            tickFormatter={(v: number) => `${v}%`}
            label={{
              value: "Cobertura observada",
              angle: -90,
              position: "insideLeft",
              fontSize: 12,
              fill: "#6b7280",
            }}
          />
          <Tooltip
            formatter={(value, name) => {
              if (value == null) return ["—", String(name)];
              const labels: Record<string, string> = {
                identity: "Calibração perfeita",
                regional: "Regional (observada)",
                personalized: "Personalizada (observada)",
                regional_low: "Wilson inf. (regional)",
                regional_high: "Wilson sup. (regional)",
              };
              return [`${formatNumber(Number(value))}%`, labels[String(name)] ?? String(name)];
            }}
            labelFormatter={(label) => `Nominal ${label}%`}
          />
          <Legend
            formatter={(value) => {
              const labels: Record<string, string> = {
                identity: "Calibração perfeita (y = x)",
                regional: "Regional",
                personalized: "Personalizada",
                regional_low: "Banda de Wilson",
                regional_high: "Banda de Wilson",
              };
              return labels[value] ?? value;
            }}
            payload={[
              { value: "identity", type: "line", color: DIAGONAL_COLOR, id: "identity" },
              { value: "regional", type: "line", color: REGIONAL_COLOR, id: "regional" },
              ...(showPersonalized
                ? [
                    {
                      value: "personalized",
                      type: "line" as const,
                      color: PERSONALIZED_COLOR,
                      id: "personalized",
                    },
                  ]
                : []),
              {
                value: "regional_low",
                type: "line" as const,
                color: "#9ca3af",
                id: "regional_low",
              },
            ]}
          />
          {/* Identity diagonal = perfect calibration */}
          <Line
            type="linear"
            dataKey="identity"
            stroke={DIAGONAL_COLOR}
            strokeWidth={1.5}
            strokeDasharray="6 4"
            dot={false}
            activeDot={false}
            isAnimationActive={false}
          />
          {/* Wilson confidence band for the regional curve */}
          <Line
            type="monotone"
            dataKey="regional_low"
            stroke="#9ca3af"
            strokeWidth={1}
            strokeDasharray="2 3"
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="regional_high"
            stroke="#9ca3af"
            strokeWidth={1}
            strokeDasharray="2 3"
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="regional"
            stroke={REGIONAL_COLOR}
            strokeWidth={2.5}
            dot={{ r: 3 }}
            isAnimationActive={false}
          />
          {showPersonalized && (
            <Line
              type="monotone"
              dataKey="personalized"
              stroke={PERSONALIZED_COLOR}
              strokeWidth={2.5}
              dot={{ r: 3 }}
              connectNulls
              isAnimationActive={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Bar chart comparing the mean interval width (sc/ha) of the regional and
 * personalized predictors. Personalizing does NOT narrow the interval.
 */
export function IntervalWidthChart({
  regional,
  personalized,
}: {
  regional: CalibrationReport;
  personalized: CalibrationReport;
}) {
  const data = [
    {
      name: "Regional",
      width: Number(regional.mean_width.toFixed(1)),
      fill: REGIONAL_COLOR,
    },
    {
      name: "Personalizada",
      width: Number(personalized.mean_width.toFixed(1)),
      fill: PERSONALIZED_COLOR,
    },
  ];

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={12} />
          <YAxis
            tickLine={false}
            axisLine={false}
            fontSize={12}
            width={56}
            tickFormatter={(v: number) => formatNumber(v, 0)}
          />
          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
            formatter={(value) => [
              `${formatNumber(Number(value))} sc/ha`,
              "Largura média do intervalo",
            ]}
          />
          <Bar dataKey="width" radius={[6, 6, 0, 0]} maxBarSize={90}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Grouped bar chart comparing accuracy metrics (MAE, RMSE, pinball mean)
 * between the regional and personalized predictors. Lower is better.
 */
export function AccuracyComparisonChart({
  regional,
  personalized,
}: {
  regional: CalibrationReport;
  personalized: CalibrationReport;
}) {
  const data = [
    {
      metric: "MAE",
      regional: Number(regional.mae.toFixed(2)),
      personalized: Number(personalized.mae.toFixed(2)),
    },
    {
      metric: "RMSE",
      regional: Number(regional.rmse.toFixed(2)),
      personalized: Number(personalized.rmse.toFixed(2)),
    },
    {
      metric: "Pinball (média)",
      regional: Number((regional.pinball.mean ?? 0).toFixed(2)),
      personalized: Number((personalized.pinball.mean ?? 0).toFixed(2)),
    },
  ];

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis dataKey="metric" tickLine={false} axisLine={false} fontSize={12} />
          <YAxis
            tickLine={false}
            axisLine={false}
            fontSize={12}
            width={48}
            tickFormatter={(v: number) => formatNumber(v, 0)}
          />
          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
            formatter={(value, name) => [
              `${formatNumber(Number(value), 2)} sc/ha`,
              name === "regional" ? "Regional" : "Personalizada",
            ]}
          />
          <Legend
            formatter={(value) =>
              value === "regional" ? "Regional" : "Personalizada"
            }
          />
          <ReferenceLine y={0} stroke="#6b7280" strokeWidth={1} />
          <Bar
            dataKey="regional"
            fill={REGIONAL_COLOR}
            radius={[4, 4, 0, 0]}
            maxBarSize={48}
          />
          <Bar
            dataKey="personalized"
            fill={PERSONALIZED_COLOR}
            radius={[4, 4, 0, 0]}
            maxBarSize={48}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
