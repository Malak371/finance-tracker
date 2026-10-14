const CURRENCY = import.meta.env.VITE_CURRENCY ?? "USD";

const moneyFormatter = new Intl.NumberFormat(undefined, { style: "currency", currency: CURRENCY });
const compactMoneyFormatter = new Intl.NumberFormat(undefined, {
  style: "currency",
  currency: CURRENCY,
  notation: "compact",
  maximumFractionDigits: 1,
});

export const formatMoney = (value) => moneyFormatter.format(Number(value) || 0);
export const formatCompactMoney = (value) => compactMoneyFormatter.format(Number(value) || 0);

// Dates from the API are plain "YYYY-MM-DD" strings; parse them as local dates, not UTC.
export function parseDate(isoDate) {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day);
}

export const formatDate = (isoDate) =>
  parseDate(isoDate).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

export function toISODate(date) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export const today = () => toISODate(new Date());

// Months are "YYYY-MM" strings throughout the app, matching the API.
export const currentMonth = () => today().slice(0, 7);

export function shiftMonth(month, delta) {
  const [year, m] = month.split("-").map(Number);
  const date = new Date(year, m - 1 + delta, 1);
  return toISODate(date).slice(0, 7);
}

export function monthRange(month) {
  const [year, m] = month.split("-").map(Number);
  // Day 0 of the next month is the last day of this one.
  return { start: `${month}-01`, end: toISODate(new Date(year, m, 0)) };
}

export function formatMonth(month, style = "long") {
  const [year, m] = month.split("-").map(Number);
  return new Date(year, m - 1, 1).toLocaleDateString(undefined, { month: style, year: "numeric" });
}
