// StepIndicator: Shows step progress in a process
import React from "react";

interface Step {
  label: string;
  description?: string;
}

interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
  orientation?: "horizontal" | "vertical";
}

export const StepIndicator: React.FC<StepIndicatorProps> = ({
  steps,
  currentStep,
  orientation = "horizontal",
}) => {
  return (
    <div
      className={`flex ${orientation === "vertical" ? "flex-col gap-4" : "flex-row items-center gap-2"}`}
    >
      {steps.map((step, index) => {
        const isCompleted = index < currentStep;
        const isCurrent = index === currentStep;
        const isPending = index > currentStep;

        return (
          <React.Fragment key={index}>
            <div
              className={`flex ${orientation === "vertical" ? "flex-row items-start" : "flex-col items-center"} gap-2`}
            >
              {/* Step circle */}
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm transition-all ${
                  isCompleted
                    ? "bg-emerald-500 text-white"
                    : isCurrent
                      ? "bg-blue-500 text-white ring-4 ring-blue-200"
                      : "bg-slate-200 text-slate-500"
                }`}
              >
                {isCompleted ? "✓" : index + 1}
              </div>

              {/* Step label */}
              <div
                className={`${orientation === "vertical" ? "text-left" : "text-center"}`}
              >
                <p
                  className={`text-sm font-medium ${isCurrent ? "text-slate-900" : isPending ? "text-slate-400" : "text-slate-700"}`}
                >
                  {step.label}
                </p>
                {step.description && (
                  <p
                    className={`text-xs ${orientation === "vertical" ? "" : "max-w-20"} ${isPending ? "text-slate-400" : "text-slate-500"}`}
                  >
                    {step.description}
                  </p>
                )}
              </div>
            </div>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div
                className={`flex-1 h-0.5 ${
                  orientation === "vertical" ? "w-0.5 h-8 ml-4" : "h-0.5"
                } ${index < currentStep ? "bg-emerald-500" : "bg-slate-200"}`}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
