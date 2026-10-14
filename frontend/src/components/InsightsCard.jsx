import {
  CalendarClock,
  Lightbulb,
  ShoppingBag,
  Store,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import { Card, CardTitle, ErrorMessage } from "./ui";

const ICONS = {
  spike: TrendingUp,
  drop: TrendingDown,
  large_purchase: ShoppingBag,
  new_merchants: Store,
  price_increase: TrendingUp,
  forecast: CalendarClock,
};

const TONES = {
  warning: "bg-amber-50 text-amber-700",
  positive: "bg-emerald-50 text-emerald-700",
  info: "bg-sky-50 text-sky-700",
};

export function InsightList({ insights }) {
  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {insights.map((insight) => {
        const Icon = ICONS[insight.kind] ?? Lightbulb;
        return (
          <li
            key={`${insight.kind}-${insight.title}`}
            className="flex gap-3 rounded-lg p-3 ring-1 ring-slate-200"
          >
            <span className={`h-fit shrink-0 rounded-lg p-2 ${TONES[insight.tone]}`}>
              <Icon className="size-4" aria-hidden />
            </span>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-900">{insight.title}</p>
              <p className="mt-0.5 text-sm text-slate-600">{insight.detail}</p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

// Plain-English observations comparing the month with the user's own history.
export default function InsightsCard({ month }) {
  const insights = useApi("/insights", { month });
  if (insights.error) return <ErrorMessage error={insights.error} onRetry={insights.reload} />;
  if (!insights.data?.length) return null;
  return (
    <Card>
      <CardTitle>
        <span className="inline-flex items-center gap-2">
          <Lightbulb className="size-4 text-amber-500" aria-hidden />
          Insights
        </span>
      </CardTitle>
      <InsightList insights={insights.data} />
    </Card>
  );
}
