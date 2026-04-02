// ProgressBar: Reusable progress bar component
import React from "react";

interface ProgressBarProps {
  value: number; // 0-100
  size?: "sm" | "md" | "lg";
  color?: "blue" | "green" | "yellow" | "red" | "purple";
  showLabel?: boolean;
  label?: string;
}

const colorMap = {
  blue: { bg: "bg-blue-500", glow: "" },
  green: { bg: "bg-emerald-500", glow: "" },
  yellow: { bg: "bg-amber-500", glow: "" },
  red: { bg: "bg-red-500", glow: "" },
  purple: { bg: "bg-purple-500", glow: "" },
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  size = "md",
  color = "blue",
  showLabel = false,
  label,
}) => {
  const clampedValue = Math.max(0, Math.min(100, value));
  const colors = colorMap[color];

  const heightMap = {
    sm: "h-1.5",
    md: "h-2.5",
    lg: "h-4",
  };

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex justify-between mb-1 text-sm">
          <span className="text-slate-600">{label || "进度"}</span>
          <span className="text-slate-700 font-medium">
            {clampedValue.toFixed(0)}%
          </span>
        </div>
      )}
      <div
        className={`w-full bg-slate-200 rounded-full overflow-hidden ${heightMap[size]}`}
      >
        <div
          className={`${colors.bg} rounded-full transition-all duration-500`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
};
