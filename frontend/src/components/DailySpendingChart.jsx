import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCompactMoney, formatDate, formatMoney, monthRange } from "../lib/format";

function dailyTotals(expenses, month) {
  const lastDay = Number(monthRange(month).end.slice(8));
  const totals = Array.from({ length: lastDay }, (_, i) => ({
    date: `${month}-${String(i + 1).padStart(2, "0")}`,
    day: i + 1,
    total: 0,
  }));
  for (const e of expenses) totals[Number(e.date.slice(8)) - 1].total += e.amount;
  return totals;
}

export default function DailySpendingChart({ expenses, month }) {
  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={dailyTotals(expenses, month)}
          margin={{ top: 4, right: 4, bottom: 0, left: 0 }}
        >
          <CartesianGrid vertical={false} stroke="#e2e8f0" />
          <XAxis
            dataKey="day"
            tickLine={false}
            axisLine={false}
            fontSize={12}
            interval="preserveStartEnd"
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
            labelFormatter={(_, payload) =>
              payload?.[0] ? formatDate(payload[0].payload.date) : ""
            }
            formatter={(value) => [formatMoney(value), "Spent"]}
          />
          <Bar dataKey="total" fill="#059669" radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
