import { Wallet } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import DemoButton from "./DemoButton";
import { Button, ErrorMessage, Field, inputClass } from "./ui";

export default function AuthForm({
  title,
  subtitle,
  submitLabel,
  onSubmit,
  footer,
  passwordHint,
  children,
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit({ email, password });
    } catch (err) {
      setError(err);
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-sm">
        <Link
          to="/"
          className="mb-8 flex items-center justify-center gap-2 font-semibold text-slate-900"
        >
          <span className="rounded-lg bg-emerald-600 p-1.5 text-white">
            <Wallet className="size-5" aria-hidden />
          </span>
          Finance Tracker
        </Link>
        <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
          <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <ErrorMessage error={error} />
            <Field label="Email" htmlFor="email">
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="Password" htmlFor="password" hint={passwordHint}>
              <input
                id="password"
                type="password"
                autoComplete={passwordHint ? "new-password" : "current-password"}
                required
                minLength={passwordHint ? 8 : undefined}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputClass}
              />
            </Field>
            <Button type="submit" loading={submitting} className="w-full">
              {submitLabel}
            </Button>
          </form>
          {children}
          <div className="my-6 flex items-center gap-3 text-xs text-slate-400">
            <span className="h-px flex-1 bg-slate-200" />
            or
            <span className="h-px flex-1 bg-slate-200" />
          </div>
          <DemoButton />
        </div>
        <p className="mt-6 text-center text-sm text-slate-500">{footer}</p>
      </div>
    </div>
  );
}
