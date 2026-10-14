import { AlertTriangle, ChevronDown } from "lucide-react";
import { useState } from "react";
import api from "../../api/api";
import { useCategories } from "../../context/CategoriesContext";
import { formatDate, formatMoney } from "../../lib/format";
import { Button, ErrorMessage, inputClass } from "../ui";

const SOURCE_LABELS = {
  rule: { label: "Your rule", className: "bg-emerald-50 text-emerald-700" },
  history: { label: "Your past choice", className: "bg-violet-50 text-violet-700" },
  model: { label: "Learned", className: "bg-violet-50 text-violet-700" },
  default: { label: "Common merchant", className: "bg-sky-50 text-sky-700" },
  file: { label: "From file", className: "bg-slate-100 text-slate-700" },
  none: { label: "Needs a category", className: "bg-amber-50 text-amber-700" },
  manual: { label: "Edited", className: "bg-slate-100 text-slate-700" },
};

export function SourceBadge({ source, confidence }) {
  const { label, className } = SOURCE_LABELS[source] ?? SOURCE_LABELS.none;
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap ${className}`}>
      {label}
      {source === "model" && confidence != null && ` · ${Math.round(confidence * 100)}%`}
    </span>
  );
}

function toRows(transactions) {
  return transactions.map((t) => ({ ...t, include: !t.duplicate, suggested: t.category }));
}

// A category the user typed or changed is a "manual" label the classifier can learn from.
const sourceOf = (row) => (row.category.trim() !== row.suggested ? "manual" : row.category_source);

export default function ReviewStep({ preview, onImported, onBack }) {
  const { categories } = useCategories();
  const [rows, setRows] = useState(() => toRows(preview.transactions));
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const update = (index, changes) =>
    setRows((rs) => rs.map((r, i) => (i === index ? { ...r, ...changes } : r)));
  const setAll = (include) => setRows((rs) => rs.map((r) => ({ ...r, include })));

  const selected = rows.filter((r) => r.include);
  const duplicates = rows.filter((r) => r.duplicate).length;
  const uncategorized = selected.filter((r) => sourceOf(r) === "none").length;
  const total = selected.reduce((sum, r) => sum + r.amount, 0);

  const handleImport = async () => {
    setError(null);
    setSaving(true);
    try {
      const transactions = selected.map((r) => ({
        date: r.date,
        amount: r.amount,
        description: r.description || null,
        category: r.category,
        category_source: sourceOf(r),
      }));
      const response = await api.post("/imports/commit", { transactions });
      onImported(response.data.imported);
    } catch (err) {
      setError(err);
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <ErrorMessage error={error} />

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-slate-600">
        <span>
          <span className="font-semibold text-slate-900">{rows.length}</span> expenses found
        </span>
        {duplicates > 0 && (
          <span className="inline-flex items-center gap-1 text-amber-700">
            <AlertTriangle className="size-4" aria-hidden />
            {duplicates} already recorded (unticked)
          </span>
        )}
        {uncategorized > 0 && <span>{uncategorized} need a category</span>}
        <span className="ml-auto flex gap-2">
          <button
            type="button"
            className="font-medium text-emerald-700 hover:underline"
            onClick={() => setAll(true)}
          >
            Select all
          </button>
          <button
            type="button"
            className="font-medium text-emerald-700 hover:underline"
            onClick={() => setAll(false)}
          >
            Select none
          </button>
        </span>
      </div>

      {rows.length > 0 ? (
        <ul
          className="divide-y divide-slate-100 rounded-lg ring-1 ring-slate-200"
          aria-label="Transactions to import"
        >
          {rows.map((row, i) => (
            <li
              key={row.row}
              className={`grid grid-cols-[auto_1fr_auto] items-start gap-3 p-3 sm:grid-cols-[auto_1fr_14rem_auto] sm:items-center ${
                row.include ? "" : "bg-slate-50 opacity-60"
              }`}
            >
              <input
                type="checkbox"
                checked={row.include}
                onChange={(e) => update(i, { include: e.target.checked })}
                aria-label={`Import ${row.description || "row " + row.row}`}
                className="mt-1 size-4 sm:mt-0"
              />
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-900">
                  {row.description || "—"}
                </p>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <time dateTime={row.date}>{formatDate(row.date)}</time>
                  {row.duplicate && (
                    <span className="rounded-full bg-amber-50 px-2 py-0.5 font-medium text-amber-700">
                      Possible duplicate
                    </span>
                  )}
                  <SourceBadge source={sourceOf(row)} confidence={row.confidence} />
                </div>
              </div>
              <p className="text-right text-sm font-semibold text-slate-900 tabular-nums sm:order-last sm:w-24">
                {formatMoney(row.amount)}
              </p>
              <div className="col-span-3 sm:col-span-1">
                <label htmlFor={`row-${row.row}-category`} className="sr-only">
                  Category for {row.description}
                </label>
                <input
                  id={`row-${row.row}-category`}
                  list="import-categories"
                  value={row.category}
                  maxLength={50}
                  onChange={(e) => update(i, { category: e.target.value })}
                  className={inputClass}
                />
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
          No expenses found with this mapping. Check the amount column and sign on the previous
          step.
        </p>
      )}
      <datalist id="import-categories">
        {categories.map((c) => (
          <option key={c} value={c} />
        ))}
      </datalist>

      {preview.skipped.length > 0 && (
        <details className="group rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
          <summary className="flex cursor-pointer list-none items-center gap-1 font-medium">
            <ChevronDown className="size-4 transition group-open:rotate-180" aria-hidden />
            {preview.skipped.length} rows skipped
          </summary>
          <ul className="mt-2 space-y-1 pl-5">
            {preview.skipped.map((s) => (
              <li key={s.row}>
                Row {s.row}: {s.reason}
              </li>
            ))}
          </ul>
        </details>
      )}

      <div className="flex flex-col-reverse justify-between gap-2 sm:flex-row sm:items-center">
        <Button variant="secondary" onClick={onBack}>
          Back to columns
        </Button>
        <Button
          onClick={handleImport}
          loading={saving}
          disabled={selected.length === 0 || selected.some((r) => !r.category.trim())}
        >
          Import {selected.length} expense{selected.length === 1 ? "" : "s"} · {formatMoney(total)}
        </Button>
      </div>
    </div>
  );
}
