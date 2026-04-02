// AlertBadge: Status indicator badge
import React from "react";

type AlertStatus = "normal" | "warning" | "attention" | "success" | "error";

interface AlertBadgeProps {
  status: AlertStatus;
  label?: string;
  size?: "sm" | "md";
  pulse?: boolean;
}

const statusConfig = {
  normal: {
    bg: "bg-emerald-100",
    text: "text-emerald-700",
    border: "border-emerald-200",
    icon: "✓",
    label: "正常",
  },
  warning: {
    bg: "bg-amber-100",
    text: "text-amber-700",
    border: "border-amber-200",
    icon: "⚠",
    label: "预警",
  },
  attention: {
    bg: "bg-amber-100",
    text: "text-amber-700",
    border: "border-amber-200",
    icon: "!",
    label: "需关注",
  },
  success: {
    bg: "bg-emerald-100",
    text: "text-emerald-700",
    border: "border-emerald-200",
    icon: "✓",
    label: "成功",
  },
  error: {
    bg: "bg-red-100",
    text: "text-red-700",
    border: "border-red-200",
    icon: "✕",
    label: "错误",
  },
};

export const AlertBadge: React.FC<AlertBadgeProps> = ({
  status,
  label,
  size = "sm",
  pulse = false,
}) => {
  const config = statusConfig[status];

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border ${config.bg} ${config.text} ${config.border} ${
        size === "sm" ? "text-xs" : "text-sm"
      } ${pulse ? "animate-pulse" : ""}`}
    >
      <span>{config.icon}</span>
      <span className="font-medium">{label || config.label}</span>
    </span>
  );
};
