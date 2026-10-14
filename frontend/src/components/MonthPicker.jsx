import { ChevronLeft, ChevronRight } from "lucide-react";
import { currentMonth, formatMonth, shiftMonth } from "../lib/format";

export default function MonthPicker({ month, onChange }) {
  const isCurrent = month >= currentMonth();
  const buttonClass =
    "rounded-md p-1.5 text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40";
  return (
    <div className="inline-flex items-center gap-1 rounded-lg bg-white p-1 ring-1 ring-slate-200">
      <button
        type="button"
        className={buttonClass}
        onClick={() => onChange(shiftMonth(month, -1))}
        aria-label="Previous month"
      >
        <ChevronLeft className="size-4" aria-hidden />
      </button>
      <span className="min-w-32 text-center text-sm font-medium text-slate-900" aria-live="polite">
        {formatMonth(month)}
      </span>
      <button
        type="button"
        className={buttonClass}
        onClick={() => onChange(shiftMonth(month, 1))}
        disabled={isCurrent}
        aria-label="Next month"
      >
        <ChevronRight className="size-4" aria-hidden />
      </button>
    </div>
  );
}
