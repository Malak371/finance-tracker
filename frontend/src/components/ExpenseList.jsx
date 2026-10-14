import { Pencil, Trash2 } from "lucide-react";
import { useCategories } from "../context/CategoriesContext";
import { formatDate, formatMoney } from "../lib/format";

export function CategoryBadge({ category }) {
  const { colorOf } = useCategories();
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
      <span
        className="size-2 rounded-full"
        style={{ backgroundColor: colorOf(category) }}
        aria-hidden
      />
      {category}
    </span>
  );
}

export default function ExpenseList({ expenses, onEdit, onDelete }) {
  return (
    <ul className="divide-y divide-slate-100">
      {expenses.map((expense) => (
        <li key={expense.id} className="flex items-center gap-3 py-3">
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-900">
              {expense.description || expense.category}
            </p>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
              <time dateTime={expense.date}>{formatDate(expense.date)}</time>
              <CategoryBadge category={expense.category} />
            </div>
          </div>
          <p className="text-sm font-semibold whitespace-nowrap text-slate-900 tabular-nums">
            {formatMoney(expense.amount)}
          </p>
          {(onEdit || onDelete) && (
            <div className="flex shrink-0 gap-1">
              {onEdit && (
                <button
                  type="button"
                  onClick={() => onEdit(expense)}
                  className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                  aria-label={`Edit ${expense.description || expense.category}`}
                >
                  <Pencil className="size-4" aria-hidden />
                </button>
              )}
              {onDelete && (
                <button
                  type="button"
                  onClick={() => onDelete(expense)}
                  className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                  aria-label={`Delete ${expense.description || expense.category}`}
                >
                  <Trash2 className="size-4" aria-hidden />
                </button>
              )}
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
