"use client";
import { CheckCircle, Circle, Loader2 } from "lucide-react";

const STEPS = [
  "Ingesting source records",
  "Normalizing jobs & pay rates",
  "Normalizing candidates",
  "Mapping pipeline stages",
  "Reconciling duplicate candidates",
  "Detecting anomalies",
  "Calculating metrics",
  "Generating manager report",
  "Preparing export",
];

interface Props {
  progress: number;  // 0–1
  visible: boolean;
}

export default function JobProgress({ progress, visible }: Props) {
  if (!visible) return null;

  const stepCount = STEPS.length;
  const currentStep = Math.floor(progress * stepCount);

  return (
    <div className="fixed bottom-5 right-5 z-50 w-72 bg-white border border-slate-200 rounded-xl shadow-xl overflow-hidden">
      {/* Header */}
      <div className="bg-slate-900 px-4 py-3 flex items-center gap-2">
        <Loader2 className="w-4 h-4 text-blue-400 animate-spin flex-shrink-0" />
        <span className="text-white text-sm font-semibold">Pipeline Refresh Running</span>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-slate-100">
        <div
          className="h-full bg-blue-500 transition-all duration-500"
          style={{ width: `${Math.round(progress * 100)}%` }}
        />
      </div>

      {/* Steps */}
      <div className="p-3 space-y-1.5 max-h-64 overflow-y-auto">
        {STEPS.map((step, i) => {
          const done    = i < currentStep;
          const active  = i === currentStep;
          const pending = i > currentStep;
          return (
            <div key={step} className={`flex items-center gap-2 ${pending ? "opacity-30" : ""}`}>
              {done    && <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />}
              {active  && <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin flex-shrink-0" />}
              {pending && <Circle className="w-3.5 h-3.5 text-slate-300 flex-shrink-0" />}
              <span className={`text-xs ${done ? "text-slate-500 line-through" : active ? "text-slate-800 font-medium" : "text-slate-400"}`}>
                {step}
              </span>
            </div>
          );
        })}
      </div>

      <div className="px-4 py-2.5 border-t border-slate-100 bg-slate-50">
        <div className="flex justify-between text-[11px] text-slate-400">
          <span>Step {Math.min(currentStep + 1, stepCount)} of {stepCount}</span>
          <span>{Math.round(progress * 100)}% complete</span>
        </div>
      </div>
    </div>
  );
}
