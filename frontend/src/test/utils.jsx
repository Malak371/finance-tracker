import { render } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider } from "../context/AuthContext";

function CurrentPath() {
  const location = useLocation();
  return <div data-testid="current-path">{location.pathname}</div>;
}

// Renders `ui` at `path` inside the app's providers, with the current URL exposed for assertions.
export function renderAt(ui, { path = "/", route = path } = {}) {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path={path} element={ui} />
          <Route path="*" element={null} />
        </Routes>
        <CurrentPath />
      </MemoryRouter>
    </AuthProvider>,
  );
}

export function apiError(status, error) {
  return Object.assign(new Error(`HTTP ${status}`), { response: { status, data: { error } } });
}
