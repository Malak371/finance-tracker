import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useCategories } from "../context/CategoriesContext";
import { useApi } from "../hooks/useApi";
import { formatCompactMoney, formatMoney, formatMonth } from "../lib/format";
import { CardTitle, ErrorMessage, LoadingState, inputClass } from "./ui";

const SELECTED = "#047857";
const OTHER = "#6ee7b7";

export default function MonthlyTrendChart({ month, category, onCategoryChange, onSelectMonth }) {
  const { categories } = useCategories();
  const trends = useApi("/dashboard/trends", { month, months: 12, ...(category && { category }) });
  const data = trends.data ?? [];
  const active = data.filter((m) => m.total > 0);
  const average = active.length ? active.reduce((sum, m) => sum + m.total, 0) / active.length : 0;

  return (
    <>
      <CardTitle
        action={
          <div className="w-40 sm:w-48">
            <label htmlFor="trend-category" className="sr-only">
              Category for monthly trend
            </label>
            <select
              id="trend-category"
              value={category}
              onChange={(e) => onCategoryChange(e.target.value)}
              className={`${inputClass} py-1.5`}
            >
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        }
      >
        Last 12 months
      </CardTitle>
      <ErrorMessage error={trends.error} onRetry={trends.reload} />
      {trends.loading ? (
        !trends.error && <LoadingState />
      ) : (
        <>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                <CartesianGrid vertical={false} stroke="#e2e8f0" />
                <XAxis
                  dataKey="month"
                  tickFormatter={(m) => formatMonth(m, "short").split(" ")[0]}
                  tickLine={false}
                  axisLine={false}
                  fontSize={12}
                />
                <YAxis
                  tickFormatter={formatCompactMoney}
                  tickLine={false}
                  axisLine={false}
                  fontSize={12}
                  width={56}
                />
                <Tooltip
                  cursor={{ fill: "#f1f5f9" }}
                  labelFormatter={(m) => formatMonth(m)}
                  formatter={(value) => [formatMoney(value), category || "Spent"]}
                />
                {average > 0 && (
                  <ReferenceLine
                    y={average}
                    stroke="#64748b"
                    strokeDasharray="4 4"
                    ifOverflow="extendDomain"
                  />
                )}
                <Bar
                  dataKey="total"
                  radius={[4, 4, 0, 0]}
                  isAnimationActive={false}
                  cursor="pointer"
                  onClick={(entry) => onSelectMonth(entry.month)}
                >
                  {data.map((m) => (
                    <Cell key={m.month} fill={m.month === month ? SELECTED : OTHER} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 flex items-center gap-2 text-xs text-slate-500">
            <span
              className="inline-block w-5 border-t-2 border-dashed border-slate-500"
              aria-hidden
            />
            Monthly average {formatMoney(average)} · click a bar to open that month
          </p>
        </>
      )}
    </>
  );
}
