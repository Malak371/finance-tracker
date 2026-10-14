import { PiggyBank, Plus } from "lucide-react";
import { useState } from "react";
import api, { errorMessage } from "../api/api";
import { CategoryBadge } from "../components/ExpenseList";
import {
  Button,
  Card,
  EmptyState,
  ErrorMessage,
  Field,
  LoadingState,
  PageHeader,
  inputClass,
} from "../components/ui";
import { useCategories } from "../context/CategoriesContext";
import { useApi } from "../hooks/useApi";
import { formatMoney } from "../lib/format";

function BudgetForm({ budget, categories, onSaved, onCancel }) {
  const [category, setCategory] = useState(budget?.category ?? "");
  const [amount, setAmount] = useState(budget ? String(budget.amount) : "");
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = { category, amount };
      if (budget) await api.put(`/budgets/${budget.id}`, payload);
      else await api.post("/budgets", payload);
      onSaved();
    } catch (err) {
      setError(err);
      setSaving(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4"
      aria-label={budget ? "Edit budget" : "Add budget"}
    >
      <ErrorMessage error={error} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Category" htmlFor="budget-category">
          <input
            id="budget-category"
            list="budget-categories"
            required
            maxLength={50}
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className={inputClass}
          />
          <datalist id="budget-categories">
            {categories.map((c) => (
              <option key={c} value={c} />
            ))}
          </datalist>
        </Field>
        <Field label="Monthly limit" htmlFor="budget-amount">
          <input
            id="budget-amount"
            type="number"
            inputMode="decimal"
            min="0.01"
            step="0.01"
            required
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className={inputClass}
          />
        </Field>
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={saving}>
          {budget ? "Save changes" : "Add budget"}
        </Button>
      </div>
    </form>
  );
}

export default function Budgets() {
  const budgets = useApi("/budgets");
  const categories = useCategories();
  const [editing, setEditing] = useState(null);
  const [actionError, setActionError] = useState(null);

  const handleSaved = () => {
    setEditing(null);
    budgets.reload();
    categories.reload();
  };

  const handleDelete = async (budget) => {
    if (!window.confirm(`Delete the ${budget.category} budget?`)) return;
    setActionError(null);
    try {
      await api.delete(`/budgets/${budget.id}`);
      budgets.reload();
    } catch (err) {
      setActionError(errorMessage(err));
    }
  };

  return (
    <>
      <PageHeader
        title="Budgets"
        description="Set a monthly limit for each category."
        actions={
          <Button onClick={() => setEditing("new")}>
            <Plus className="size-4" aria-hidden />
            Add budget
          </Button>
        }
      />

      {editing && (
        <Card className="mb-6">
          <h2 className="mb-4 text-base font-semibold text-slate-900">
            {editing === "new" ? "New budget" : `Edit ${editing.category} budget`}
          </h2>
          <BudgetForm
            key={editing === "new" ? "new" : editing.id}
            budget={editing === "new" ? null : editing}
            categories={categories.categories}
            onSaved={handleSaved}
            onCancel={() => setEditing(null)}
          />
        </Card>
      )}

      <div className="mb-4 space-y-3">
        <ErrorMessage error={actionError} />
        <ErrorMessage error={budgets.error} onRetry={budgets.reload} />
      </div>

      {budgets.loading ? (
        !budgets.error && <LoadingState label="Loading budgets…" />
      ) : budgets.data?.length ? (
        <Card>
          <ul className="divide-y divide-slate-100">
            {budgets.data.map((budget) => (
              <li key={budget.id} className="flex items-center gap-3 py-3">
                <div className="flex-1">
                  <CategoryBadge category={budget.category} />
                </div>
                <span className="text-sm font-semibold text-slate-900 tabular-nums">
                  {formatMoney(budget.amount)} / month
                </span>
                <Button variant="ghost" onClick={() => setEditing(budget)}>
                  Edit
                </Button>
                <Button variant="danger" onClick={() => handleDelete(budget)}>
                  Delete
                </Button>
              </li>
            ))}
          </ul>
        </Card>
      ) : (
        budgets.data && (
          <Card>
            <EmptyState
              icon={PiggyBank}
              title="No budgets yet"
              action={<Button onClick={() => setEditing("new")}>Add your first budget</Button>}
            >
              Set a monthly limit for a category to keep spending in check.
            </EmptyState>
          </Card>
        )
      )}
    </>
  );
}
