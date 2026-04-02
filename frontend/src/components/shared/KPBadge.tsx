// KPBadge: Knowledge Point badge component
import React from "react";

interface KPBadgeProps {
  kpId: string;
  name?: string;
  type?: "knowledge" | "method";
  size?: "sm" | "md";
}

export const KPBadge: React.FC<KPBadgeProps> = ({
  kpId,
  name,
  type,
  size = "sm",
}) => {
  const isMethod = type === "method";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded font-mono ${
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm"
      }       ${
        isMethod
          ? "bg-purple-100 text-purple-700 border border-purple-200"
          : "bg-blue-100 text-blue-700 border border-blue-200"
      }`}
    >
      <span>{isMethod ? "🔧" : "📚"}</span>
      <span>{name || kpId}</span>
    </span>
  );
};
