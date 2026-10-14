import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { useCategories } from "../context/CategoriesContext";
import { OTHER_COLOR } from "../lib/colors";
import { formatMoney } from "../lib/format";

const MAX_SLICES = 7;

// Keep the biggest categories and fold the long tail into a single "Other" slice.
function slices(categories) {
  if (categories.length <= MAX_SLICES + 1) return categories;
  const rest = categories.slice(MAX_SLICES);
  return [
    ...categories.slice(0, MAX_SLICES),
    {
      category: `Other (${rest.length})`,
      total: rest.reduce((sum, c) => sum + c.total, 0),
      isOther: true,
    },
  ];
}

export default function CategoryBreakdown({ categories, total }) {
  const { colorOf } = useCategories();
  const data = slices(categories);
  const color = (slice) => (slice.isOther ? OTHER_COLOR : colorOf(slice.category));

  return (
    <div className="@container">
      <div className="grid items-center gap-6 @lg:grid-cols-[10rem_1fr]">
        <div className="mx-auto size-40">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="total"
                nameKey="category"
                innerRadius="62%"
                outerRadius="100%"
                stroke="#ffffff"
                strokeWidth={2}
                isAnimationActive={false}
              >
                {data.map((slice) => (
                  <Cell key={slice.category} fill={color(slice)} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatMoney(value)} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <ul className="min-w-0 space-y-2" aria-label="Spending by category">
          {data.map((slice) => (
            <li key={slice.category} className="flex items-center gap-2 text-sm">
              <span
                className="size-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: color(slice) }}
                aria-hidden
              />
              <span className="min-w-0 flex-1 truncate text-slate-700">{slice.category}</span>
              <span className="text-slate-500 tabular-nums">
                {Math.round((slice.total / total) * 100)}%
              </span>
              <span className="text-right font-medium whitespace-nowrap text-slate-900 tabular-nums">
                {formatMoney(slice.total)}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
