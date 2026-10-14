import { createContext, useContext, useMemo } from "react";
import { useApi } from "../hooks/useApi";
import { makeColorOf } from "../lib/colors";

const CategoriesContext = createContext({
  categories: [],
  colorOf: makeColorOf([]),
  reload: () => {},
});

// Loads the user's categories once for the whole signed-in app (form suggestions, filters, colours).
export function CategoriesProvider({ children }) {
  const { data, reload } = useApi("/categories");
  const value = useMemo(() => {
    // The API lists categories in order of first use, which keeps colour slots stable as new
    // categories appear; forms and filters show them alphabetically.
    const firstUsed = data ?? [];
    const categories = [...firstUsed].sort((a, b) =>
      a.localeCompare(b, undefined, { sensitivity: "base" }),
    );
    return { categories, colorOf: makeColorOf(firstUsed), reload };
  }, [data, reload]);
  return <CategoriesContext.Provider value={value}>{children}</CategoriesContext.Provider>;
}

// Fixed categories for previews that render app components without an API (the landing page).
export function StaticCategoriesProvider({ categories, children }) {
  const value = useMemo(
    () => ({ categories, colorOf: makeColorOf(categories), reload: () => {} }),
    [categories],
  );
  return <CategoriesContext.Provider value={value}>{children}</CategoriesContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useCategories() {
  return useContext(CategoriesContext);
}
