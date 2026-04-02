// ScatterPlot: Class overview scatter plot (students by R ratio vs mastery)
import React from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface StudentPoint {
  id: string;
  name: string;
  dimensionRatio: number; // X-axis: R dimension ratio
  mastery: number; // Y-axis: average mastery
  status: "normal" | "warning" | "attention";
}

interface ScatterPlotProps {
  data: StudentPoint[];
  title?: string;
}

export const ScatterPlot: React.FC<ScatterPlotProps> = ({ data, title }) => {
  return (
    <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
      {title && (
        <h3 className="text-sm font-medium text-slate-700 mb-3">{title}</h3>
      )}

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />

            <XAxis
              type="number"
              dataKey="dimensionRatio"
              domain={[0, 1]}
              tickFormatter={(v) => `${Math.round(v * 100)}%`}
              tick={{ fill: "#64748B", fontSize: 12 }}
              tickLine={{ stroke: "#CBD5E1" }}
              label={{
                value: "R维度比例",
                position: "bottom",
                offset: 0,
                fill: "#64748B",
              }}
            />

            <YAxis
              type="number"
              dataKey="mastery"
              domain={[0, 1]}
              tickFormatter={(v) => `${Math.round(v * 100)}%`}
              tick={{ fill: "#64748B", fontSize: 12 }}
              tickLine={{ stroke: "#CBD5E1" }}
              label={{
                value: "平均掌握度",
                angle: -90,
                position: "left",
                fill: "#64748B",
              }}
            />

            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0].payload as StudentPoint;
                return (
                  <div className="bg-white px-4 py-3 rounded-lg border border-slate-200 shadow-lg">
                    <p className="font-medium text-slate-800">{p.name}</p>
                    <p className="text-xs text-slate-500">
                      R维度: {(p.dimensionRatio * 100).toFixed(0)}% · 掌握度:{" "}
                      {(p.mastery * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs text-slate-400">{p.id}</p>
                  </div>
                );
              }}
            />

            {/* Reference lines */}
            <ReferenceLine x={0.5} stroke="#CBD5E1" strokeDasharray="3 3" />
            <ReferenceLine y={0.5} stroke="#CBD5E1" strokeDasharray="3 3" />

            <Scatter data={data} fill="#8884D8" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-3 text-xs">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-emerald-500" />
          <span className="text-slate-500">正常</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-amber-500" />
          <span className="text-slate-500">预警</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-slate-500">需关注</span>
        </div>
      </div>
    </div>
  );
};
