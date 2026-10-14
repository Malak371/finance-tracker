import { Download, Plus, ReceiptText } from "lucide-react";
import { useState } from "react";
import api, { errorMessage } from "../api/api";
import ExpenseForm from "../components/ExpenseForm";
import ExpenseList from "../components/ExpenseList";
import MonthPicker from "../components/MonthPicker";
import {
  Button,
  Card,
  EmptyState,
  ErrorMessage,
  LoadingState,
  PageHeader,
  inputClass,
} from "../components/ui";
import { useCategories } from "../context/CategoriesContext";
import { useApi } from "../hooks/useApi";
import { useMonthParam } from "../hooks/useMonthParam";
import { formatMoney, formatMonth, monthRange } from "../lib/format";

async function downloadCsv() {
  const response = await api.get("/expenses/export", { responseType: "blob" });
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = "expenses.csv";
  link.click();
  URL.revokeObjectURL(url);
}

export default function Expenses() {
  const [month, setMonth] = useMonthParam();
  const [category, setCategory] = useState("");
  // null: form closed, "new": adding, otherwise the expense being edited
  const [editing, setEditing] = useState(null);
  const [actionError, setActionError] = useState(null);

  const expenses = useApi("/expenses", { ...monthRange(month), ...(category && { category }) });
  const categories = useCategories();

  const refresh = () => {
    expenses.reload();
    categories.reload();
  };

  const handleSaved = () => {
    setEditing(null);
    refresh();
  };

  const handleDelete = async (expense) => {
    if (!window.confirm(`Delete "${expense.description || expense.category}"?`)) return;
    setActionError(null);
    try {
      await api.delete(`/expenses/${expense.id}`);
      refresh();
    } catch (err) {
      setActionError(errorMessage(err));
    }
  };

  const handleExport = async () => {
    setActionError(null);
    try {
      await downloadCsv();
    } catch (err) {
      setActionError(errorMessage(err, "Export failed. Please try again."));
    }
  };

  const total = (expenses.data ?? []).reduce((sum, e) => sum + e.amount, 0);

  return (
    <>
      <PageHeader
        title="Expenses"
        description="Everything you've spent, month by month."
        actions={
          <>
            <Button variant="secondary" onClick={handleExport}>
              <Download className="size-4" aria-hidden />
              Export CSV
            </Button>
            <Button onClick={() => setEditing("new")}>
              <Plus className="size-4" aria-hidden />
              Add expense
            </Button>
          </>
        }
      />

      {editing && (
        <Card className="mb-6">
          <h2 className="mb-4 text-base font-semibold text-slate-900">
            {editing === "new" ? "New expense" : "Edit expense"}
          </h2>
          <ExpenseForm
            key={editing === "new" ? "new" : editing.id}
            expense={editing === "new" ? null : editing}
            categories={categories.categories}
            onSaved={handleSaved}
            onCancel={() => setEditing(null)}
          />
        </Card>
      )}

      <Card>
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <MonthPicker month={month} onChange={setMonth} />
          <div className="flex items-center gap-3">
            <label htmlFor="category-filter" className="sr-only">
              Filter by category
            </label>
            <select
              id="category-filter"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className={`${inputClass} sm:w-48`}
            >
              <option value="">All categories</option>
              {categories.categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="space-y-3">
          <ErrorMessage error={actionError} />
          <ErrorMessage error={expenses.error} onRetry={expenses.reload} />
        </div>

        {expenses.loading ? (
          <LoadingState label="Loading expenses…" />
        ) : expenses.data?.length ? (
          <>
            <ExpenseList expenses={expenses.data} onEdit={setEditing} onDelete={handleDelete} />
            <p className="mt-4 border-t border-slate-100 pt-4 text-right text-sm text-slate-500">
              {expenses.data.length} expense{expenses.data.length === 1 ? "" : "s"} ·{" "}
              <span className="font-semibold text-slate-900">{formatMoney(total)}</span>
            </p>
          </>
        ) : (
          !expenses.error && (
            <EmptyState
              icon={ReceiptText}
              title={`No expenses in ${formatMonth(month)}`}
              action={
                // Hidden while the form is already open above.
                !editing && (
                  <Button onClick={() => setEditing("new")}>
                    <Plus className="size-4" aria-hidden />
                    Add expense
                  </Button>
                )
              }
            >
              {category ? `Nothing in ${category} this month.` : "Add one to start tracking."}
            </EmptyState>
          )
        )}
      </Card>
    </>
  );
}
