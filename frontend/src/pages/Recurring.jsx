import { ArrowUpRight, CalendarClock, Repeat } from "lucide-react";
import { CategoryBadge } from "../components/ExpenseList";
import {
  Card,
  CardTitle,
  EmptyState,
  ErrorMessage,
  LoadingState,
  PageHeader,
} from "../components/ui";
import { useApi } from "../hooks/useApi";
import { formatDate, formatMoney } from "../lib/format";

const CADENCE_LABELS = {
  weekly: "Weekly",
  fortnightly: "Every 2 weeks",
  monthly: "Monthly",
  quarterly: "Quarterly",
  yearly: "Yearly",
};

export function ChargeRow({ charge }) {
  const priceChange = charge.previous_amount != null ? charge.amount - charge.previous_amount : 0;
  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-2 py-3">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-slate-900">{charge.merchant}</p>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
          <CategoryBadge category={charge.category} />
          <span className="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-700">
            {CADENCE_LABELS[charge.cadence]}
          </span>
          <span>
            {charge.occurrences} charges since {formatDate(charge.first_date)}
          </span>
          {priceChange > 0 && (
            <span className="inline-flex items-center gap-0.5 rounded-full bg-red-50 px-2 py-0.5 font-medium text-red-700">
              <ArrowUpRight className="size-3" aria-hidden />
              Up from {formatMoney(charge.previous_amount)} since{" "}
              {formatDate(charge.price_changed_on)}
            </span>
          )}
          {priceChange < 0 && (
            <span className="rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-700">
              Down from {formatMoney(charge.previous_amount)} since{" "}
              {formatDate(charge.price_changed_on)}
            </span>
          )}
        </div>
      </div>
      <div className="text-right text-sm">
        <p className="font-semibold text-slate-900 tabular-nums">{formatMoney(charge.amount)}</p>
        <p className="text-xs text-slate-500">
          {charge.active
            ? `Next around ${formatDate(charge.next_date)}`
            : `Last charged ${formatDate(charge.last_date)}`}
        </p>
      </div>
    </li>
  );
}

export default function Recurring() {
  const recurring = useApi("/insights/recurring");
  const charges = recurring.data?.charges ?? [];
  const active = charges.filter((c) => c.active);
  const inactive = charges.filter((c) => !c.active);

  return (
    <>
      <PageHeader
        title="Recurring charges"
        description="Subscriptions, rent and memberships detected from your spending history."
      />
      <ErrorMessage error={recurring.error} onRetry={recurring.reload} />

      {recurring.loading ? (
        !recurring.error && <LoadingState label="Looking for recurring charges…" />
      ) : charges.length === 0 ? (
        recurring.data && (
          <Card>
            <EmptyState icon={Repeat} title="No recurring charges found yet">
              Charges from the same merchant at a regular interval (weekly to yearly) with a similar
              amount show up here. Import a few months of statements to get started.
            </EmptyState>
          </Card>
        )
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <p className="text-sm text-slate-500">Recurring per month</p>
              <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 tabular-nums">
                {formatMoney(recurring.data.monthly_total)}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                {active.length} active charge{active.length === 1 ? "" : "s"}
              </p>
            </Card>
            <Card>
              <p className="text-sm text-slate-500">Per year</p>
              <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 tabular-nums">
                {formatMoney(recurring.data.monthly_total * 12)}
              </p>
              <p className="mt-1 text-sm text-slate-500">At current prices</p>
            </Card>
          </div>

          {active.length > 0 && (
            <Card>
              <CardTitle>Active</CardTitle>
              <ul className="divide-y divide-slate-100">
                {active.map((c) => (
                  <ChargeRow key={`${c.merchant}-${c.first_date}`} charge={c} />
                ))}
              </ul>
            </Card>
          )}

          {inactive.length > 0 && (
            <Card>
              <CardTitle>
                <span className="inline-flex items-center gap-2">
                  <CalendarClock className="size-4 text-slate-400" aria-hidden />
                  Possibly cancelled
                </span>
              </CardTitle>
              <p className="-mt-2 mb-2 text-sm text-slate-500">
                These used to repeat but are overdue. If you cancelled them, nice saving.
              </p>
              <ul className="divide-y divide-slate-100 opacity-75">
                {inactive.map((c) => (
                  <ChargeRow key={`${c.merchant}-${c.first_date}`} charge={c} />
                ))}
              </ul>
            </Card>
          )}
        </div>
      )}
    </>
  );
}
