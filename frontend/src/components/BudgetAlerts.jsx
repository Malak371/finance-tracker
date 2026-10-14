import { AlertOctagon, AlertTriangle } from "lucide-react";
import { Link } from "react-router-dom";
import { formatMoney } from "../lib/format";

// A banner listing budgets that are over or close to their limit for the month.
export default function BudgetAlerts({ budgets, month }) {
  const over = budgets.filter((b) => b.status === "over");
  const warning = budgets.filter((b) => b.status === "warning");
  if (!over.length && !warning.length) return null;

  const severe = over.length > 0;
  const Icon = severe ? AlertOctagon : AlertTriangle;
  return (
    <div
      role="alert"
      className={`flex gap-3 rounded-xl p-4 ring-1 ${
        severe ? "bg-red-50 text-red-800 ring-red-200" : "bg-amber-50 text-amber-800 ring-amber-200"
      }`}
    >
      <Icon className="mt-0.5 size-5 shrink-0" aria-hidden />
      <div className="flex-1 text-sm">
        <p className="font-semibold">
          Budget alert:{" "}
          {[
            over.length && `${over.length} over the limit`,
            warning.length && `${warning.length} nearly used up`,
          ]
            .filter(Boolean)
            .join(", ")}
        </p>
        <ul className="mt-1 space-y-0.5">
          {[...over, ...warning].map((b) => (
            <li key={b.id}>
              {b.category}: {formatMoney(b.spent)} of {formatMoney(b.amount)} (
              {Math.round(b.percent)}%)
            </li>
          ))}
        </ul>
      </div>
      <Link to={`/app/budgets?month=${month}`} className="self-start text-sm font-medium underline">
        Review
      </Link>
    </div>
  );
}
