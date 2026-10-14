import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { GuestRoute, ProtectedRoute } from "./components/ProtectedRoute";
import Budgets from "./pages/Budgets";
import Dashboard from "./pages/Dashboard";
import DemoStart from "./pages/DemoStart";
import Expenses from "./pages/Expenses";
import Import from "./pages/Import";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Recurring from "./pages/Recurring";
import Rules from "./pages/Rules";
import Signup from "./pages/Signup";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/demo" element={<DemoStart />} />
        <Route
          path="/login"
          element={
            <GuestRoute>
              <Login />
            </GuestRoute>
          }
        />
        <Route
          path="/signup"
          element={
            <GuestRoute>
              <Signup />
            </GuestRoute>
          }
        />
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="expenses" element={<Expenses />} />
          <Route path="budgets" element={<Budgets />} />
          <Route path="recurring" element={<Recurring />} />
          <Route path="import" element={<Import />} />
          <Route path="rules" element={<Rules />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
