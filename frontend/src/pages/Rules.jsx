import { ArrowRight, ChevronDown, Tags, Trash2 } from "lucide-react";
import { useState } from "react";
import api, { errorMessage } from "../api/api";
import { CategoryBadge } from "../components/ExpenseList";
import {
  Button,
  Card,
  CardTitle,
  EmptyState,
  ErrorMessage,
  Field,
  LoadingState,
  PageHeader,
  inputClass,
} from "../components/ui";
import { useCategories } from "../context/CategoriesContext";
import { useApi } from "../hooks/useApi";

function RuleForm({ onCreated }) {
  const { categories } = useCategories();
  const [keyword, setKeyword] = useState("");
  const [category, setCategory] = useState("");
  const [applyToExisting, setApplyToExisting] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const response = await api.post("/rules", {
        keyword,
        category,
        apply_to_existing: applyToExisting,
      });
      setKeyword("");
      setCategory("");
      onCreated(response.data);
    } catch (err) {
      setError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" aria-label="Add rule">
      <ErrorMessage error={error} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field
          label="When the description contains"
          htmlFor="rule-keyword"
          hint="Whole words, any case."
        >
          <input
            id="rule-keyword"
            required
            maxLength={100}
            placeholder="e.g. tesco"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className={inputClass}
          />
        </Field>
        <Field label="Categorise as" htmlFor="rule-category">
          <input
            id="rule-category"
            list="rule-categories"
            required
            maxLength={50}
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className={inputClass}
          />
          <datalist id="rule-categories">
            {categories.map((c) => (
              <option key={c} value={c} />
            ))}
          </datalist>
        </Field>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={applyToExisting}
            onChange={(e) => setApplyToExisting(e.target.checked)}
          />
          Also apply to existing auto-categorised expenses
        </label>
        <Button type="submit" loading={saving}>
          Add rule
        </Button>
      </div>
    </form>
  );
}

export default function Rules() {
  const rules = useApi("/rules");
  const defaults = useApi("/rules/defaults");
  const { reload: reloadCategories } = useCategories();
  const [notice, setNotice] = useState(null);
  const [actionError, setActionError] = useState(null);

  const handleCreated = (rule) => {
    setNotice(
      rule.applied
        ? `Rule added and ${rule.applied} existing expense${rule.applied === 1 ? "" : "s"} re-categorised.`
        : "Rule added.",
    );
    rules.reload();
    reloadCategories();
  };

  const handleDelete = async (rule) => {
    setActionError(null);
    setNotice(null);
    try {
      await api.delete(`/rules/${rule.id}`);
      rules.reload();
    } catch (err) {
      setActionError(errorMessage(err));
    }
  };

  return (
    <>
      <PageHeader
        title="Categorisation rules"
        description="How imported transactions get their category."
      />

      <Card className="mb-6">
        <h2 className="text-base font-semibold text-slate-900">How it works</h2>
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-600">
          <li>Your rules below are checked first.</li>
          <li>Then merchants you&apos;ve categorised before get the same category again.</li>
          <li>
            Then a classifier that learns from <em>your</em> choices: every category you type or
            correct teaches it. It only suggests when it&apos;s at least 70% sure.
          </li>
          <li>Then built-in keywords for common merchants.</li>
          <li>Anything left is marked Uncategorized for you to review.</li>
        </ol>
      </Card>

      <Card className="mb-6">
        <CardTitle>Add a rule</CardTitle>
        {notice && (
          <p role="status" className="mb-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">
            {notice}
          </p>
        )}
        <RuleForm onCreated={handleCreated} />
      </Card>

      <Card className="mb-6">
        <CardTitle>Your rules</CardTitle>
        <div className="space-y-3">
          <ErrorMessage error={actionError} />
          <ErrorMessage error={rules.error} onRetry={rules.reload} />
        </div>
        {rules.loading ? (
          !rules.error && <LoadingState label="Loading rules…" />
        ) : rules.data?.length ? (
          <ul className="divide-y divide-slate-100">
            {rules.data.map((rule) => (
              <li key={rule.id} className="flex items-center gap-3 py-3 text-sm">
                <code className="rounded bg-slate-100 px-2 py-0.5 text-slate-800">
                  {rule.keyword}
                </code>
                <ArrowRight className="size-4 shrink-0 text-slate-400" aria-hidden />
                <div className="flex-1">
                  <CategoryBadge category={rule.category} />
                </div>
                <button
                  type="button"
                  onClick={() => handleDelete(rule)}
                  className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                  aria-label={`Delete rule ${rule.keyword}`}
                >
                  <Trash2 className="size-4" aria-hidden />
                </button>
              </li>
            ))}
          </ul>
        ) : (
          rules.data && (
            <EmptyState icon={Tags} title="No rules yet">
              Add one above, e.g. &ldquo;tesco&rdquo; → Groceries.
            </EmptyState>
          )
        )}
      </Card>

      {defaults.data && (
        <details className="group rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200 sm:p-6">
          <summary className="flex cursor-pointer list-none items-center gap-2 text-base font-semibold text-slate-900">
            <ChevronDown className="size-4 transition group-open:rotate-180" aria-hidden />
            Built-in merchant keywords ({defaults.data.length})
          </summary>
          <div className="mt-4 flex flex-wrap gap-2">
            {defaults.data.map((d) => (
              <span
                key={d.keyword}
                className="rounded-md bg-slate-50 px-2 py-1 text-xs text-slate-600"
              >
                {d.keyword} → {d.category}
              </span>
            ))}
          </div>
        </details>
      )}
    </>
  );
}
