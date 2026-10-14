import { FileUp } from "lucide-react";
import { useRef, useState } from "react";
import api from "../../api/api";
import { ErrorMessage, LoadingState } from "../ui";

export default function UploadStep({ onParsed }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const upload = async (file) => {
    if (!file) return;
    setError(null);
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const response = await api.post("/imports/parse", form);
      onParsed({ ...response.data, filename: file.name });
    } catch (err) {
      setError(err);
      setUploading(false);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    upload(event.dataTransfer.files[0]);
  };

  if (uploading) return <LoadingState label="Reading your file…" />;

  return (
    <div className="space-y-4">
      <ErrorMessage error={error} />
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`flex flex-col items-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition ${
          dragging ? "border-emerald-500 bg-emerald-50" : "border-slate-300"
        }`}
      >
        <div className="mb-3 rounded-full bg-slate-100 p-3 text-slate-500">
          <FileUp className="size-6" aria-hidden />
        </div>
        <p className="text-sm font-medium text-slate-900">Drop a CSV statement here</p>
        <p className="mt-1 text-sm text-slate-500">
          or{" "}
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="font-medium text-emerald-700 hover:underline"
          >
            choose a file
          </button>
        </p>
        <p className="mt-3 text-xs text-slate-400">
          CSV exports from most banks and card providers · up to 2 MB
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="sr-only"
          aria-label="CSV file"
          onChange={(e) => upload(e.target.files[0])}
        />
      </div>
    </div>
  );
}
