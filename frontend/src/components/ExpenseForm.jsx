import { useState } from "react";
import api from "../api/api";
import { today } from "../lib/format";
import { Button, ErrorMessage, Field, inputClass } from "./ui";

const EMPTY = { amount: "", category: "", date: "", description: "" };

export default function ExpenseForm({ expense, categories = [], onSaved, onCancel }) {
  const [values, setValues] = useState(() =>
    expense
      ? { ...expense, amount: String(expense.amount), description: expense.description ?? "" }
      : { ...EMPTY, date: today() },
  );
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const update = (field) => (event) => setValues((v) => ({ ...v, [field]: event.target.value }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    const payload = {
      amount: values.amount,
      category: values.category,
      date: values.date,
      description: values.description || null,
    };
    try {
      const response = expense
        ? await api.put(`/expenses/${expense.id}`, payload)
        : await api.post("/expenses", payload);
      onSaved(response.data);
    } catch (err) {
      setError(err);
      setSaving(false);
    }
  };

  const idPrefix = expense ? `edit-${expense.id}` : "new";

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4"
      aria-label={expense ? "Edit expense" : "Add expense"}
    >
      <ErrorMessage error={error} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Amount" htmlFor={`${idPrefix}-amount`}>
          <input
            id={`${idPrefix}-amount`}
            type="number"
            inputMode="decimal"
            min="0.01"
            step="0.01"
            required
            value={values.amount}
            onChange={update("amount")}
            className={inputClass}
          />
        </Field>
        <Field label="Date" htmlFor={`${idPrefix}-date`}>
          <input
            id={`${idPrefix}-date`}
            type="date"
            required
            value={values.date}
            onChange={update("date")}
            className={inputClass}
          />
        </Field>
        <Field label="Category" htmlFor={`${idPrefix}-category`}>
          <input
            id={`${idPrefix}-category`}
            list={`${idPrefix}-categories`}
            required
            maxLength={50}
            placeholder="e.g. Groceries"
            value={values.category}
            onChange={update("category")}
            className={inputClass}
          />
          <datalist id={`${idPrefix}-categories`}>
            {categories.map((c) => (
              <option key={c} value={c} />
            ))}
          </datalist>
        </Field>
        <Field label="Description (optional)" htmlFor={`${idPrefix}-description`}>
          <input
            id={`${idPrefix}-description`}
            maxLength={255}
            placeholder="e.g. Weekly shop"
            value={values.description}
            onChange={update("description")}
            className={inputClass}
          />
        </Field>
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={saving}>
          {expense ? "Save changes" : "Add expense"}
        </Button>
      </div>
    </form>
  );
}
