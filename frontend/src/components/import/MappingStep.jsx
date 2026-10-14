import { useState } from "react";
import api from "../../api/api";
import { Button, ErrorMessage, Field, inputClass } from "../ui";

const DATE_FORMAT_LABELS = {
  "%Y-%m-%d": "2026-01-31",
  "%d/%m/%Y": "31/01/2026 (day first)",
  "%m/%d/%Y": "01/31/2026 (month first)",
  "%d.%m.%Y": "31.01.2026",
  "%d-%m-%Y": "31-01-2026 (day first)",
  "%m-%d-%Y": "01-31-2026 (month first)",
  "%Y/%m/%d": "2026/01/31",
  "%d/%m/%y": "31/01/26 (day first)",
  "%m/%d/%y": "01/31/26 (month first)",
  "%d %b %Y": "31 Jan 2026",
  "%b %d, %Y": "Jan 31, 2026",
  "%Y%m%d": "20260131",
};

function initialMapping(suggested) {
  const { date_format_options: _options, ...mapping } = suggested;
  return { ...mapping, date_format: mapping.date_format ?? "%Y-%m-%d" };
}

function ColumnSelect({ id, label, value, headers, onChange, optional = false }) {
  return (
    <Field label={label} htmlFor={id}>
      <select
        id={id}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
        className={inputClass}
        required={!optional}
      >
        <option value="">{optional ? "None" : "Choose a column"}</option>
        {headers.map((header, i) => (
          <option key={i} value={i}>
            {header || `Column ${i + 1}`}
          </option>
        ))}
      </select>
    </Field>
  );
}

export default function MappingStep({ parsed, onPreviewed, onBack }) {
  const [mapping, setMapping] = useState(() => initialMapping(parsed.suggested_mapping));
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const set = (field) => (value) => setMapping((m) => ({ ...m, [field]: value }));

  const detected = parsed.suggested_mapping.date_format_options;
  const dateFormats = detected.length ? detected : Object.keys(DATE_FORMAT_LABELS);
  const ambiguousDates = detected.length > 1;

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const response = await api.post("/imports/preview", { mapping, rows: parsed.rows });
      onPreviewed(response.data, mapping);
    } catch (err) {
      setError(err);
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <ErrorMessage error={error} />

      <div>
        <h3 className="mb-2 text-sm font-medium text-slate-700">
          First rows of {parsed.filename} ({parsed.rows.length} rows)
        </h3>
        <div className="overflow-x-auto rounded-lg ring-1 ring-slate-200">
          <table className="min-w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                {parsed.headers.map((h, i) => (
                  <th key={i} className="px-3 py-2 font-medium whitespace-nowrap">
                    {h || `Column ${i + 1}`}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {parsed.rows.slice(0, 4).map((row, r) => (
                <tr key={r}>
                  {row.map((cell, c) => (
                    <td key={c} className="max-w-48 truncate px-3 py-2 whitespace-nowrap">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <ColumnSelect
          id="map-date"
          label="Date column"
          value={mapping.date_column}
          headers={parsed.headers}
          onChange={set("date_column")}
        />
        <Field
          label="Date format"
          htmlFor="map-date-format"
          hint={
            ambiguousDates
              ? "Your dates could be day-first or month-first. Please check."
              : undefined
          }
        >
          <select
            id="map-date-format"
            value={mapping.date_format}
            onChange={(e) => set("date_format")(e.target.value)}
            className={inputClass}
          >
            {dateFormats.map((f) => (
              <option key={f} value={f}>
                {DATE_FORMAT_LABELS[f] ?? f}
              </option>
            ))}
          </select>
        </Field>
        <ColumnSelect
          id="map-description"
          label="Description column"
          value={mapping.description_column}
          headers={parsed.headers}
          onChange={set("description_column")}
        />
        <ColumnSelect
          id="map-category"
          label="Category column"
          value={mapping.category_column}
          headers={parsed.headers}
          onChange={set("category_column")}
          optional
        />
      </div>

      <fieldset className="space-y-4">
        <legend className="mb-2 text-sm font-medium text-slate-700">Amounts</legend>
        <div className="flex flex-wrap gap-4 text-sm text-slate-700">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="amount-mode"
              checked={mapping.amount_mode === "single"}
              onChange={() => set("amount_mode")("single")}
            />
            One amount column
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="amount-mode"
              checked={mapping.amount_mode === "split"}
              onChange={() => set("amount_mode")("split")}
            />
            Separate money in / money out columns
          </label>
        </div>
        {mapping.amount_mode === "single" ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <ColumnSelect
              id="map-amount"
              label="Amount column"
              value={mapping.amount_column}
              headers={parsed.headers}
              onChange={set("amount_column")}
            />
            <Field label="Expenses are shown as" htmlFor="map-sign">
              <select
                id="map-sign"
                value={mapping.expense_sign}
                onChange={(e) => set("expense_sign")(e.target.value)}
                className={inputClass}
              >
                <option value="negative">Negative numbers (most bank accounts)</option>
                <option value="positive">Positive numbers (most credit cards)</option>
              </select>
            </Field>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            <ColumnSelect
              id="map-debit"
              label="Money out (debit) column"
              value={mapping.debit_column}
              headers={parsed.headers}
              onChange={set("debit_column")}
            />
            <ColumnSelect
              id="map-credit"
              label="Money in (credit) column"
              value={mapping.credit_column}
              headers={parsed.headers}
              onChange={set("credit_column")}
              optional
            />
          </div>
        )}
      </fieldset>

      <div className="flex justify-between gap-2">
        <Button variant="secondary" onClick={onBack}>
          Choose another file
        </Button>
        <Button type="submit" loading={loading}>
          Preview transactions
        </Button>
      </div>
    </form>
  );
}
