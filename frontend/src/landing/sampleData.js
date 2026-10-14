// Static sample data for the landing page previews. Shapes match the API responses.
export const SAMPLE_CATEGORIES = [
  "Rent",
  "Groceries",
  "Dining",
  "Transport",
  "Subscriptions",
  "Shopping",
  "Utilities",
  "Health",
];

export const SAMPLE_BY_CATEGORY = [
  { category: "Rent", total: 1450, count: 1 },
  { category: "Groceries", total: 412.35, count: 9 },
  { category: "Dining", total: 268.9, count: 14 },
  { category: "Transport", total: 161.32, count: 6 },
  { category: "Subscriptions", total: 102.95, count: 5 },
  { category: "Shopping", total: 96.4, count: 3 },
];

export const SAMPLE_TOTAL = SAMPLE_BY_CATEGORY.reduce((sum, c) => sum + c.total, 0);

export const SAMPLE_BUDGETS = [
  {
    id: 1,
    category: "Shopping",
    amount: 80,
    spent: 96.4,
    remaining: -16.4,
    percent: 120.5,
    status: "over",
    projected: null,
  },
  {
    id: 2,
    category: "Dining",
    amount: 300,
    spent: 268.9,
    remaining: 31.1,
    percent: 89.6,
    status: "warning",
    projected: null,
  },
  {
    id: 3,
    category: "Groceries",
    amount: 600,
    spent: 412.35,
    remaining: 187.65,
    percent: 68.7,
    status: "ok",
    projected: 640,
  },
];

export const SAMPLE_IMPORT_ROWS = [
  { description: "TRADER JOE'S #552", amount: 48.17, category: "Groceries", source: "rule" },
  { description: "STARBUCKS #2087", amount: 5.85, category: "Dining", source: "history" },
  {
    description: "AMZN Mktp books",
    amount: 23.99,
    category: "Books",
    source: "model",
    confidence: 0.91,
  },
  { description: "BLUE BOTTLE COFFEE", amount: 6.5, category: "Dining", source: "default" },
  { description: "ZEN FLOW YOGA STUDIO", amount: 25, category: "Uncategorized", source: "none" },
];

export const SAMPLE_RECURRING = [
  {
    merchant: "NETFLIX.COM",
    category: "Subscriptions",
    cadence: "monthly",
    amount: 17.99,
    occurrences: 13,
    first_date: "2025-10-07",
    last_date: "2026-10-07",
    next_date: "2026-11-07",
    active: true,
    previous_amount: 15.49,
    price_changed_on: "2026-07-07",
  },
  {
    merchant: "PUREGYM MEMBERSHIP",
    category: "Health",
    cadence: "monthly",
    amount: 34.99,
    occurrences: 13,
    first_date: "2025-10-03",
    last_date: "2026-10-03",
    next_date: "2026-11-03",
    active: true,
    previous_amount: null,
    price_changed_on: null,
  },
];
