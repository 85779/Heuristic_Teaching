// DimensionRatioChart: R/M dimension ratio visualization
import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

interface DimensionRatioChartProps {
  ratio: number; // 0-1, where 1 = full Resource
  trend?: "rising" | "falling" | "stable";
  confidence?: number;
  size?: number;
}

export const DimensionRatioChart: React.FC<DimensionRatioChartProps> = ({
  ratio,
  trend,
  confidence,
  size = 160,
}) => {
  const resourcePercent = Math.round(ratio * 100);
  const metacogPercent = 100 - resourcePercent;

  const data = [
    { name: "Resource", value: resourcePercent, color: "#8B5CF6" }, // purple
    { name: "Metacognitive", value: metacogPercent, color: "#06B6D4" }, // cyan
  ];

  const trendIcon = trend === "rising" ? "↗" : trend === "falling" ? "↘" : "→";
  const trendColor =
    trend === "rising"
      ? "text-emerald-500"
      : trend === "falling"
        ? "text-red-500"
        : "text-slate-400";

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              startAngle={180}
              endAngle={0}
              innerRadius="60%"
              outerRadius="85%"
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0].payload as { name: string; value: number };
                return (
                  <div className="bg-white px-3 py-2 rounded-lg border border-slate-200 shadow-lg">
                    <p className="text-slate-800 font-medium">{p.name}</p>
                    <p className="text-slate-500">{p.value}%</p>
                  </div>
                );
              }}
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-slate-800">
            {resourcePercent}%
          </span>
          <span className="text-xs text-slate-500">R维度</span>
        </div>
      </div>

      {/* Legend & trend */}
      <div className="flex items-center gap-4 mt-2">
        <div className="flex items-center gap-2 text-xs text-slate-600">
          <span className="w-2 h-2 rounded-full bg-purple-500" />
          <span>Resource</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-600">
          <span className="w-2 h-2 rounded-full bg-cyan-500" />
          <span>Metacog</span>
        </div>
      </div>

      {trend && (
        <div className={`flex items-center gap-1 mt-2 text-sm ${trendColor}`}>
          <span>{trendIcon}</span>
          <span>
            趋势 {confidence && `(${Math.round(confidence * 100)}%置信)`}
          </span>
        </div>
      )}
    </div>
  );
};
