import { ArrowDownRight, ArrowUpRight, PieChart, Plus } from "lucide-react";
import { Link } from "react-router-dom";
import BudgetAlerts from "../components/BudgetAlerts";
import BudgetProgress from "../components/BudgetProgress";
import CategoryBreakdown from "../components/CategoryBreakdown";
import DailySpendingChart from "../components/DailySpendingChart";
import ExpenseList from "../components/ExpenseList";
import MonthPicker from "../components/MonthPicker";
import {
  Card,
  CardTitle,
  EmptyState,
  ErrorMessage,
  LoadingState,
  PageHeader,
} from "../components/ui";
import { useApi } from "../hooks/useApi";
import { useMonthParam } from "../hooks/useMonthParam";
import { formatMoney, formatMonth, monthRange } from "../lib/format";

function StatCard({ label, value, children }) {
  return (
    <Card>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 tabular-nums">
        {value}
      </p>
      {children && <div className="mt-1 text-sm">{children}</div>}
    </Card>
  );
}

function MonthOverMonth({ current, previous }) {
  if (!previous) return <span className="text-slate-500">No spending last month</span>;
  const change = ((current - previous) / previous) * 100;
  const up = change > 0;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  return (
    <span className={`inline-flex items-center gap-1 ${up ? "text-red-600" : "text-emerald-600"}`}>
      <Icon className="size-4" aria-hidden />
      {Math.abs(change).toFixed(0)}% {up ? "more" : "less"} than last month
    </span>
  );
}

export default function Dashboard() {
  const [month, setMonth] = useMonthParam();
  const summary = useApi("/dashboard/summary", { month });
  const expenses = useApi("/expenses", monthRange(month));
  const budgets = useApi("/budgets/status", { month });

  const error = summary.error || expenses.error || budgets.error;
  const retry = () => {
    summary.reload();
    expenses.reload();
    budgets.reload();
  };

  return (
    <>
      <PageHeader
        title="Dashboard"
        description={`Your spending in ${formatMonth(month)}.`}
        actions={<MonthPicker month={month} onChange={setMonth} />}
      />
      <ErrorMessage error={error} onRetry={retry} />

      {summary.loading || expenses.loading || budgets.loading ? (
        !error && <LoadingState />
      ) : summary.data && expenses.data && budgets.data ? (
        <div className="space-y-6">
          <BudgetAlerts budgets={budgets.data} month={month} />
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard label="Spent this month" value={formatMoney(summary.data.total_spent)}>
              <MonthOverMonth
                current={summary.data.total_spent}
                previous={summary.data.previous_month_total}
              />
            </StatCard>
            <StatCard label="Transactions" value={summary.data.transaction_count} />
            <StatCard label="Top category" value={summary.data.by_category[0]?.category ?? "—"}>
              {summary.data.by_category[0] && (
                <span className="text-slate-500">
                  {formatMoney(summary.data.by_category[0].total)}
                </span>
              )}
            </StatCard>
          </div>

          {summary.data.transaction_count === 0 ? (
            <Card>
              <EmptyState
                icon={PieChart}
                title={`No spending recorded for ${formatMonth(month)}`}
                action={
                  <Link
                    to="/expenses"
                    className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                  >
                    <Plus className="size-4" aria-hidden />
                    Add an expense
                  </Link>
                }
              >
                Add expenses to see where your money goes.
              </EmptyState>
            </Card>
          ) : (
            <>
              <div className="grid gap-6 lg:grid-cols-2">
                <Card>
                  <CardTitle>By category</CardTitle>
                  <CategoryBreakdown
                    categories={summary.data.by_category}
                    total={summary.data.total_spent}
                  />
                </Card>
                <Card>
                  <CardTitle>Daily spending</CardTitle>
                  <DailySpendingChart expenses={expenses.data} month={month} />
                </Card>
              </div>
              {budgets.data.length > 0 && (
                <Card>
                  <CardTitle
                    action={
                      <Link
                        to={`/budgets?month=${month}`}
                        className="text-sm font-medium text-emerald-700 hover:underline"
                      >
                        Manage
                      </Link>
                    }
                  >
                    Budgets
                  </CardTitle>
                  <ul className="divide-y divide-slate-100">
                    {budgets.data.slice(0, 4).map((budget) => (
                      <li key={budget.id}>
                        <BudgetProgress budget={budget} />
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
              <Card>
                <CardTitle
                  action={
                    <Link
                      to={`/expenses?month=${month}`}
                      className="text-sm font-medium text-emerald-700 hover:underline"
                    >
                      View all
                    </Link>
                  }
                >
                  Recent expenses
                </CardTitle>
                <ExpenseList expenses={expenses.data.slice(0, 5)} />
              </Card>
            </>
          )}
        </div>
      ) : null}
    </>
  );
}
