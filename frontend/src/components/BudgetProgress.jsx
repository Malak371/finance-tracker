import { AlertOctagon, AlertTriangle, CheckCircle2, TrendingUp } from "lucide-react";
import { formatMoney } from "../lib/format";
import { CategoryBadge } from "./ExpenseList";
import { ProgressBar } from "./ui";

const STATUS = {
  ok: { label: "On track", icon: CheckCircle2, className: "text-emerald-700" },
  warning: { label: "Nearing limit", icon: AlertTriangle, className: "text-amber-700" },
  over: { label: "Over budget", icon: AlertOctagon, className: "text-red-700" },
};

export function StatusLabel({ status }) {
  const { label, icon: Icon, className } = STATUS[status];
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium ${className}`}>
      <Icon className="size-3.5" aria-hidden />
      {label}
    </span>
  );
}

function willExceed(budget) {
  return budget.status === "ok" && budget.projected != null && budget.projected > budget.amount;
}

export default function BudgetProgress({ budget, actions }) {
  return (
    <div className="py-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <CategoryBadge category={budget.category} />
          <StatusLabel status={budget.status} />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-600 tabular-nums">
            <span className="font-semibold text-slate-900">{formatMoney(budget.spent)}</span> of{" "}
            {formatMoney(budget.amount)}
          </span>
          {actions}
        </div>
      </div>
      <ProgressBar
        percent={budget.percent}
        tone={budget.status}
        label={`${budget.category}: ${Math.round(budget.percent)}% of budget used`}
      />
      <div className="mt-1.5 flex flex-wrap justify-between gap-2 text-xs text-slate-500">
        <span>
          {budget.remaining >= 0
            ? `${formatMoney(budget.remaining)} left`
            : `${formatMoney(-budget.remaining)} over`}
        </span>
        {willExceed(budget) && (
          <span className="inline-flex items-center gap-1 text-amber-700">
            <TrendingUp className="size-3.5" aria-hidden />
            On pace for {formatMoney(budget.projected)} this month
          </span>
        )}
      </div>
    </div>
  );
}
