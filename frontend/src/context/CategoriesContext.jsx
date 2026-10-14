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
    const categories = data ?? [];
    return { categories, colorOf: makeColorOf(categories), reload };
  }, [data, reload]);
  return <CategoriesContext.Provider value={value}>{children}</CategoriesContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useCategories() {
  return useContext(CategoriesContext);
}
