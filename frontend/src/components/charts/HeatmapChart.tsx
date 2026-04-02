// HeatmapChart: Knowledge mastery heatmap for student profile
import React, { useState } from "react";

interface HeatmapCell {
  kpId: string;
  name: string;
  chapter: number;
  mastery: number;
  attempts: number;
}

interface HeatmapChartProps {
  data: HeatmapCell[];
  title?: string;
}

// Color scale based on mastery
const getMasteryColor = (mastery: number): string => {
  if (mastery >= 0.8) return "#10B981";
  if (mastery >= 0.6) return "#34D399";
  if (mastery >= 0.4) return "#FBBF24";
  if (mastery >= 0.2) return "#F97316";
  return "#EF4444";
};

export const HeatmapChart: React.FC<HeatmapChartProps> = ({ data, title }) => {
  const [hoveredCell, setHoveredCell] = useState<HeatmapCell | null>(null);

  // Group by chapter
  const chapters = Array.from(new Set(data.map((d) => d.chapter))).sort(
    (a, b) => a - b,
  );

  return (
    <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
      {title && (
        <h3 className="text-sm font-medium text-slate-700 mb-3">{title}</h3>
      )}

      <div className="space-y-2">
        {chapters.map((chapter) => {
          const chapterData = data.filter((d) => d.chapter === chapter);
          return (
            <div key={chapter} className="flex items-center gap-2">
              <span className="text-xs text-slate-400 w-6">Ch{chapter}</span>
              <div className="flex-1 flex gap-1">
                {chapterData.map((cell) => (
                  <div
                    key={cell.kpId}
                    className="flex-1 h-8 rounded cursor-pointer transition-transform hover:scale-110 relative"
                    style={{ backgroundColor: getMasteryColor(cell.mastery) }}
                    onMouseEnter={() => setHoveredCell(cell)}
                    onMouseLeave={() => setHoveredCell(null)}
                  >
                    {hoveredCell?.kpId === cell.kpId && (
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 whitespace-nowrap bg-white px-3 py-2 rounded-lg border border-slate-200 shadow-lg">
                        <p className="font-medium text-slate-800 text-sm">
                          {cell.name}
                        </p>
                        <p className="text-xs text-slate-500">
                          {cell.kpId} · 掌握度 {(cell.mastery * 100).toFixed(0)}
                          %
                        </p>
                        <p className="text-xs text-slate-400">
                          尝试 {cell.attempts} 次
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-end gap-2 mt-3 text-xs text-slate-500">
        <span>低</span>
        <div className="flex gap-0.5">
          <div
            className="w-4 h-2 rounded-sm"
            style={{ backgroundColor: "#EF4444" }}
          />
          <div
            className="w-4 h-2 rounded-sm"
            style={{ backgroundColor: "#F97316" }}
          />
          <div
            className="w-4 h-2 rounded-sm"
            style={{ backgroundColor: "#FBBF24" }}
          />
          <div
            className="w-4 h-2 rounded-sm"
            style={{ backgroundColor: "#34D399" }}
          />
          <div
            className="w-4 h-2 rounded-sm"
            style={{ backgroundColor: "#10B981" }}
          />
        </div>
        <span>高</span>
      </div>
    </div>
  );
};
