import { CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import MappingStep from "../components/import/MappingStep";
import ReviewStep from "../components/import/ReviewStep";
import UploadStep from "../components/import/UploadStep";
import { Button, Card, PageHeader } from "../components/ui";
import { useCategories } from "../context/CategoriesContext";

const STEPS = ["Upload", "Match columns", "Review", "Done"];

function Steps({ current }) {
  return (
    <ol className="mb-6 flex flex-wrap gap-x-6 gap-y-2 text-sm" aria-label="Import progress">
      {STEPS.map((label, i) => (
        <li
          key={label}
          aria-current={i === current ? "step" : undefined}
          className={`flex items-center gap-2 ${i <= current ? "font-medium text-slate-900" : "text-slate-400"}`}
        >
          <span
            className={`flex size-6 items-center justify-center rounded-full text-xs ${
              i < current
                ? "bg-emerald-600 text-white"
                : i === current
                  ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600"
                  : "bg-slate-100"
            }`}
          >
            {i + 1}
          </span>
          {label}
        </li>
      ))}
    </ol>
  );
}

export default function Import() {
  const { reload: reloadCategories } = useCategories();
  const [parsed, setParsed] = useState(null);
  const [preview, setPreview] = useState(null);
  const [imported, setImported] = useState(null);

  const step = imported !== null ? 3 : preview ? 2 : parsed ? 1 : 0;

  const restart = () => {
    setParsed(null);
    setPreview(null);
    setImported(null);
  };

  return (
    <>
      <PageHeader
        title="Import a statement"
        description="Upload a CSV from your bank or card. We'll match the columns, skip duplicates and suggest categories."
      />
      <Steps current={step} />
      <Card>
        {step === 0 && <UploadStep onParsed={setParsed} />}
        {step === 1 && <MappingStep parsed={parsed} onPreviewed={setPreview} onBack={restart} />}
        {step === 2 && (
          <ReviewStep
            preview={preview}
            onBack={() => setPreview(null)}
            onImported={(count) => {
              setImported(count);
              reloadCategories();
            }}
          />
        )}
        {step === 3 && (
          <div className="flex flex-col items-center py-8 text-center">
            <CheckCircle2 className="mb-3 size-10 text-emerald-600" aria-hidden />
            <h2 className="text-lg font-semibold text-slate-900">
              Imported {imported} expense{imported === 1 ? "" : "s"}
            </h2>
            <p className="mt-1 max-w-md text-sm text-slate-500">
              Categories you changed during review teach the categoriser for next time.
            </p>
            <div className="mt-6 flex gap-2">
              <Button variant="secondary" onClick={restart}>
                Import another file
              </Button>
              <Link
                to="/expenses"
                className="inline-flex items-center rounded-lg bg-emerald-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-emerald-700"
              >
                View expenses
              </Link>
            </div>
          </div>
        )}
      </Card>
    </>
  );
}
