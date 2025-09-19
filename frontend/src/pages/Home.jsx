import { useEffect, useState } from "react";
import api from "../api/api";
import ExpenseForm from "../components/ExpenseForm";
import ExpenseList from "../components/ExpenseList";
import Dashboard from "../components/Dashboard";
import { useNavigate } from 'react-router-dom';

export default function Home() {
    const [expenses, setExpenses] = useState([]);
    const [summary, setSummary] = useState({total_spent: 0, breakdown: {}});
    const [budgets, setBudgets] = useState([]);
    const [weeklyData, setWeeklyData] = useState([]);
    const [monthlyData, setMonthlyData] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState("");
    const navigate = useNavigate();

      const goToBudget = () => {
        navigate('/budgets');
      };


    const fetchExpenses = async (category = selectedCategory) => {
    const categoryParam = category ? `?category=${category}` : "";
    try {
      const res = await api.get(`/expenses/${categoryParam}`);
      setExpenses(res.data);
    } catch (err) {
      console.error("Failed to fetch expenses:", err);
    }
  };

  const fetchSummary = async () => {
    try {
      const res = await api.get("/dashboard/summary");
      setSummary(res.data);
    } catch (err) {
      console.error("Failed to fetch summary:", err);
    }
  };

  const fetchBudgets = async () => {
    try {
      const res = await api.get("/budgets/");
      setBudgets(res.data);
    } catch (err) {
      console.error("Failed to fetch budgets:", err);
    }
  };

  const fetchTrends = async (category = selectedCategory) => {
    const categoryParam = category ? `?category=${category}` : "";
    try {
      const weeklyRes = await api.get(`/expenses/trends/weekly${categoryParam}`);
      setWeeklyData(weeklyRes.data);

      const monthlyRes = await api.get(`/expenses/trends/monthly${categoryParam}`);
      setMonthlyData(monthlyRes.data);
    } catch (err) {
      console.error("Failed to fetch trends:", err);
    }
  };

    const applyFilter = async () => {
  await fetchExpenses();
  await fetchTrends();
};


    const refreshAll = async () => {
    await fetchExpenses();
    await fetchSummary();
    await fetchBudgets();
    await fetchTrends();
  };

  useEffect(() => {
    refreshAll();
  }, []);

    return (

        <div className="min-h-screen bg-gray-900 text-white px-6 py-8">
      <h1 className="mb-8 text-center text-4xl font-bold text-cyan-400">
        Finance Tracker
      </h1>
      <button
    onClick={goToBudget}
    className="bg-cyan-500 px-4 py-2 rounded hover:bg-cyan-600 text-white"
  >
    Make Budget
  </button>

      <div className="mb-4 flex gap-4 items-center">
  <label className="font-semibold" htmlFor="categoryFilter">
    Filter by Category:
  </label>
  <select
    id="categoryFilter"
    className="bg-gray-800 text-white p-2 rounded"
    value={selectedCategory}
    onChange={(e) => setSelectedCategory(e.target.value)}
  >
    <option value="">All</option>
    {budgets.map((b) => (
      <option key={b.id} value={b.category}>
        {b.category}
      </option>
    ))}
  </select>
  <button
    onClick={applyFilter}
    className="bg-cyan-500 px-4 py-2 rounded hover:bg-cyan-600 text-white"
  >
    Apply
  </button>
</div>


      <div className="mb-8">
        <Dashboard
            summary={summary}
            budgets={budgets}
            weeklyData={weeklyData}
            monthlyData={monthlyData}
        />

      </div>

      <div className="mb-8 max-w-xl mx-auto">
        <ExpenseForm refresh={fetchExpenses} refreshSummary={fetchSummary} />
      </div>

      <div className="mb-8">
        <ExpenseList expenses={expenses} refresh={fetchExpenses}/>
      </div>
    </div>
    );
}