// Validated categorical palette (colour-blind safe adjacent pairs), used in this fixed order.
export const CATEGORY_PALETTE = [
  "#2a78d6", // blue
  "#eb6834", // orange
  "#1baf7a", // aqua
  "#eda100", // yellow
  "#e87ba4", // magenta
  "#008300", // green
  "#4a3aa7", // violet
  "#e34948", // red
];
export const OTHER_COLOR = "#94a3b8";

/**
 * Colour follows the category, not its rank: each of the user's categories gets a slot by the
 * order in which they first used it, so it keeps the same colour on every page and month, and
 * adding a category never repaints existing ones. Past the palette size we fall back to neutral
 * grey instead of cycling hues.
 */
export function makeColorOf(categories) {
  const slots = new Map(categories.map((c, i) => [c.toLowerCase(), CATEGORY_PALETTE[i]]));
  return (category) => slots.get(category.toLowerCase()) ?? OTHER_COLOR;
}
