import {BrowserRouter as Router, Routes, Route} from "react-router-dom";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import Budgets from "./pages/Budgets";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
                <Home />
            </ProtectedRoute>
          } 
        />
        <Route
          path="/budgets"
          element={
            <ProtectedRoute>
              <Budgets />
            </ProtectedRoute>
          }
        />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
      </Routes>
    </Router>
  );
}

export default App;