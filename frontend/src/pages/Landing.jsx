import {
  ArrowRight,
  CodeXml,
  FileUp,
  Lightbulb,
  LineChart,
  PiggyBank,
  Repeat,
  ShieldCheck,
  Sparkles,
  Tags,
  Wallet,
} from "lucide-react";
import { Link } from "react-router-dom";
import BudgetProgress from "../components/BudgetProgress";
import CategoryBreakdown from "../components/CategoryBreakdown";
import DemoButton from "../components/DemoButton";
import { CategoryBadge } from "../components/ExpenseList";
import { InsightList } from "../components/InsightsCard";
import { SourceBadge } from "../components/import/ReviewStep";
import { useAuth } from "../context/AuthContext";
import { StaticCategoriesProvider } from "../context/CategoriesContext";
import {
  SAMPLE_BUDGETS,
  SAMPLE_BY_CATEGORY,
  SAMPLE_CATEGORIES,
  SAMPLE_IMPORT_ROWS,
  SAMPLE_INSIGHTS,
  SAMPLE_RECURRING,
  SAMPLE_TOTAL,
} from "../landing/sampleData";
import { formatMoney } from "../lib/format";
import { ChargeRow } from "./Recurring";

const REPO_URL = "https://github.com/Malak371/finance-tracker";

function PrimaryCta({ variant = "primary" }) {
  const { token } = useAuth();
  if (token) {
    return (
      <Link
        to="/app"
        className={`inline-flex items-center justify-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold ${
          variant === "light"
            ? "bg-white text-emerald-800 hover:bg-emerald-50"
            : "bg-emerald-600 text-white hover:bg-emerald-700"
        }`}
      >
        Open your dashboard
        <ArrowRight className="size-4" aria-hidden />
      </Link>
    );
  }
  return (
    <div className="w-full sm:w-72">
      <DemoButton variant={variant} label="Explore the live demo" className="px-5 py-3" />
    </div>
  );
}

function PreviewFrame({ children, label }) {
  return (
    <figure className="overflow-hidden rounded-2xl bg-white shadow-xl ring-1 ring-slate-200">
      <div className="flex items-center gap-1.5 border-b border-slate-100 bg-slate-50 px-4 py-2.5">
        <span className="size-2.5 rounded-full bg-slate-300" />
        <span className="size-2.5 rounded-full bg-slate-300" />
        <span className="size-2.5 rounded-full bg-slate-300" />
        <figcaption className="ml-3 text-xs text-slate-500">{label}</figcaption>
      </div>
      <div className="p-4 sm:p-6">{children}</div>
    </figure>
  );
}

function FeatureRow({ icon: Icon, eyebrow, title, children, preview, reverse = false }) {
  return (
    <div className="grid items-center gap-8 lg:grid-cols-2 lg:gap-16">
      <div className={reverse ? "lg:order-2" : ""}>
        <p className="mb-2 inline-flex items-center gap-2 text-sm font-semibold text-emerald-700">
          <Icon className="size-4" aria-hidden />
          {eyebrow}
        </p>
        <h3 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h3>
        <div className="mt-3 space-y-3 text-slate-600">{children}</div>
      </div>
      <div className={reverse ? "lg:order-1" : ""}>{preview}</div>
    </div>
  );
}

const PIPELINE = [
  ["Your rules", "“trader joe” → Groceries"],
  ["Your history", "Merchants you've categorised before"],
  ["Learned model", "Naive Bayes trained on your corrections"],
  ["Common merchants", "Built-in keywords as a fallback"],
  ["Uncategorized", "Left for you to review"],
];

const EXTRAS = [
  {
    icon: LineChart,
    title: "Month-over-month trends",
    text: "Twelve months at a glance, per category, compared with the same point last month.",
  },
  {
    icon: ShieldCheck,
    title: "Private by design",
    text: "Every query is scoped to the signed-in user, and a test fails if any endpoint answers without a login.",
  },
  {
    icon: Sparkles,
    title: "A demo that's yours",
    text: "Each visitor gets a private copy with a year of data. Edit anything; it's deleted after 24 hours.",
  },
];

export default function Landing() {
  const { token } = useAuth();

  return (
    <StaticCategoriesProvider categories={SAMPLE_CATEGORIES}>
      <div className="min-h-screen bg-slate-50 text-slate-900">
        <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2 font-semibold">
            <span className="rounded-lg bg-emerald-600 p-1.5 text-white">
              <Wallet className="size-4" aria-hidden />
            </span>
            Finance Tracker
          </Link>
          <nav className="flex items-center gap-1 text-sm sm:gap-3">
            <a
              href={REPO_URL}
              aria-label="Source code on GitHub"
              className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100"
            >
              <CodeXml className="size-4" aria-hidden />
              <span className="hidden sm:inline">Source</span>
            </a>
            {token ? (
              <Link
                to="/app"
                className="rounded-lg px-3 py-2 font-medium text-emerald-700 hover:bg-emerald-50"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100"
                >
                  Log in
                </Link>
                <Link
                  to="/signup"
                  className="rounded-lg px-3 py-2 font-medium text-emerald-700 hover:bg-emerald-50"
                >
                  Sign up
                </Link>
              </>
            )}
          </nav>
        </header>

        <main>
          <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pt-8 pb-16 sm:px-6 lg:grid-cols-[1fr_1.1fr] lg:pt-16">
            <div>
              <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
                Know where your money goes, without the spreadsheet.
              </h1>
              <p className="mt-5 text-lg text-slate-600">
                Import a bank statement and Finance Tracker skips the duplicates, categorises every
                transaction, learns from your corrections, and warns you before a budget runs out.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-start">
                <PrimaryCta />
                {!token && (
                  <Link
                    to="/signup"
                    className="inline-flex items-center justify-center rounded-lg px-5 py-3 text-sm font-semibold whitespace-nowrap text-slate-700 ring-1 ring-slate-300 hover:bg-white"
                  >
                    Create an account
                  </Link>
                )}
              </div>
              {!token && (
                <p className="mt-3 text-sm text-slate-500">
                  No sign-up needed: the demo opens a private account with a year of sample data.
                </p>
              )}
            </div>
            <PreviewFrame label="Dashboard · October 2026">
              <div className="mb-4 grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">Spent this month</p>
                  <p className="text-xl font-semibold tabular-nums">{formatMoney(SAMPLE_TOTAL)}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">Recurring per month</p>
                  <p className="text-xl font-semibold tabular-nums">{formatMoney(1587.95)}</p>
                </div>
              </div>
              <CategoryBreakdown categories={SAMPLE_BY_CATEGORY} total={SAMPLE_TOTAL} />
            </PreviewFrame>
          </section>

          <section className="border-y border-slate-200 bg-white">
            <div className="mx-auto max-w-6xl space-y-24 px-4 py-20 sm:px-6">
              <FeatureRow
                icon={FileUp}
                eyebrow="Statement import"
                title="Drop in a CSV from any bank"
                preview={
                  <PreviewFrame label="Import · review">
                    <ul className="divide-y divide-slate-100">
                      {SAMPLE_IMPORT_ROWS.map((row) => (
                        <li key={row.description} className="flex items-center gap-3 py-2.5">
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium">{row.description}</p>
                            <div className="mt-1 flex flex-wrap gap-2">
                              <CategoryBadge category={row.category} />
                              <SourceBadge source={row.source} confidence={row.confidence} />
                            </div>
                          </div>
                          <span className="text-sm font-semibold tabular-nums">
                            {formatMoney(row.amount)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </PreviewFrame>
                }
              >
                <p>
                  Match columns once, with day/month order detected from your data. Debit and credit
                  columns, European number formats and bank preamble lines are all handled.
                </p>
                <p>
                  Re-importing an overlapping statement flags what&apos;s already recorded, without
                  hiding genuine repeat purchases like two coffees on the same day.
                </p>
              </FeatureRow>

              <FeatureRow
                reverse
                icon={Tags}
                eyebrow="Categorisation that learns"
                title="Correct it once, and it remembers"
                preview={
                  <ol className="space-y-2">
                    {PIPELINE.map(([name, detail], i) => (
                      <li
                        key={name}
                        className="flex items-center gap-3 rounded-xl bg-slate-50 p-3 ring-1 ring-slate-200"
                      >
                        <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-xs font-semibold text-white">
                          {i + 1}
                        </span>
                        <div>
                          <p className="text-sm font-semibold">{name}</p>
                          <p className="text-xs text-slate-500">{detail}</p>
                        </div>
                      </li>
                    ))}
                  </ol>
                }
              >
                <p>
                  Each transaction goes through a five-step pipeline and stops at the first match. A
                  Naive Bayes classifier trained only on <em>your</em> choices suggests a category
                  when it&apos;s at least 70% sure.
                </p>
                <p>
                  It never learns from its own guesses, so a wrong suggestion can&apos;t reinforce
                  itself.
                </p>
              </FeatureRow>

              <FeatureRow
                icon={Lightbulb}
                eyebrow="Insights"
                title="It notices what you'd miss"
                preview={
                  <PreviewFrame label="Insights · October 2026">
                    <InsightList insights={SAMPLE_INSIGHTS} />
                  </PreviewFrame>
                }
              >
                <p>
                  Every month is compared with your own history, at the same day of the month:
                  spikes and drops by category, purchases far above your usual, new merchants,
                  subscription price rises, and a forecast for the month&apos;s total.
                </p>
                <p>
                  Thresholds are deliberately conservative (outside your normal variation, not just
                  a bit higher) so the cards stay worth reading.
                </p>
              </FeatureRow>

              <FeatureRow
                reverse
                icon={PiggyBank}
                eyebrow="Budgets with alerts"
                title="Warnings before the month is over"
                preview={
                  <PreviewFrame label="Budgets · October 2026">
                    <ul className="divide-y divide-slate-100">
                      {SAMPLE_BUDGETS.map((budget) => (
                        <li key={budget.id}>
                          <BudgetProgress budget={budget} />
                        </li>
                      ))}
                    </ul>
                  </PreviewFrame>
                }
              >
                <p>
                  Monthly limits per category with clear states: on track, nearing the limit, over
                  budget. If your spending pace projects past the limit, you see it mid-month.
                </p>
              </FeatureRow>

              <FeatureRow
                icon={Repeat}
                eyebrow="Subscriptions"
                title="Every recurring charge, found for you"
                preview={
                  <PreviewFrame label="Recurring charges">
                    <ul className="divide-y divide-slate-100">
                      {SAMPLE_RECURRING.map((charge) => (
                        <ChargeRow key={charge.merchant} charge={charge} />
                      ))}
                    </ul>
                  </PreviewFrame>
                }
              >
                <p>
                  Weekly to yearly charges are detected from timing and amount, including price
                  rises and subscriptions that seem to have stopped.
                </p>
              </FeatureRow>
            </div>
          </section>

          <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
            <div className="grid gap-6 sm:grid-cols-3">
              {EXTRAS.map(({ icon: Icon, title, text }) => (
                <div
                  key={title}
                  className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
                >
                  <Icon className="mb-3 size-6 text-emerald-600" aria-hidden />
                  <h3 className="font-semibold">{title}</h3>
                  <p className="mt-1 text-sm text-slate-600">{text}</p>
                </div>
              ))}
            </div>

            <div className="mt-16 rounded-2xl bg-emerald-700 px-6 py-12 text-center text-white sm:px-12">
              <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                See it with real data
              </h2>
              <p className="mx-auto mt-3 max-w-xl text-emerald-50">
                Open the demo to explore a year of spending, import the sample statement, and try
                correcting a category.
              </p>
              <div className="mx-auto mt-6 flex justify-center">
                <PrimaryCta variant="light" />
              </div>
            </div>
          </section>
        </main>

        <footer className="border-t border-slate-200 py-8 text-center text-sm text-slate-500">
          Built with React, FastAPI and PostgreSQL ·{" "}
          <a href={REPO_URL} className="font-medium text-emerald-700 hover:underline">
            View the source on GitHub
          </a>
        </footer>
      </div>
    </StaticCategoriesProvider>
  );
}
