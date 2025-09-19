import {useEffect, useState} from "react";
import api from "../api/api";
import {useAuth} from "../context/AuthContext";

export default function Budgets({refresh}) {
    const {token} = useAuth();
    const [budgets, setBudgets] = useState([]);
    const [category, setCategory] = useState("");
    const [amount, setAmount] = useState("");
    const [editingId, setEditingId] = useState(null);

    useEffect(() => {
    const fetchBudgets = async () => {
      try {
        const res = await api.get("/budgets/");
        setBudgets(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchBudgets();
  }, [token]);

    const handleAdd = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        const res = await api.put(`/budgets/${editingId}`, {
          category,
          amount: parseFloat(amount),
        });
        setBudgets(budgets.map(b => (b.id === editingId ? res.data : b)));
        setEditingId(null);
      } else {
        const res = await api.post("/budgets/", {
          category,
          amount: parseFloat(amount),
        });
        setBudgets([...budgets, res.data]);
      }
      setCategory("");
      setAmount("");
      refresh();
    } catch (err) {
      if (err.response?.data?.detail) alert(err.response.data.detail);
      console.error(err);
    }
  };

  const handleEdit = (budget) => {
    setEditingId(budget.id);
    setCategory(budget.category);
    setAmount(budget.amount);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this budget?")) return;
    try {
      await api.delete(`/budgets/${id}`);
      setBudgets(budgets.filter(b => b.id !== id));
      refresh();
    } catch (err) {
      console.error(err);
    }
  };

    return (
        <div>
      <h1 className="text-2xl font-bold mb-4">Budgets</h1>
      <form className="mb-6 flex gap-2" onSubmit={handleAdd}>
        <input
          type="text"
          placeholder="Category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="border p-2 rounded flex-1"
          required
        />
        <input
          type="number"
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="border p-2 rounded w-32"
          required
        />
        <button className="bg-blue-600 text-white px-4 rounded hover:bg-blue-700">
          {editingId ? "Update" : "Add"}
        </button>
        {editingId && (
          <button
            type="button"
            onClick={() => { setEditingId(null); setCategory(""); setAmount(""); }}
            className="bg-gray-500 text-white px-4 rounded hover:bg-gray-600"
          >
            Cancel
          </button>
        )}
      </form>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {budgets.map((b) => (
          <div key={b.id} className="p-4 bg-white rounded shadow flex justify-between items-center">
            <span>{b.category}</span>
            <span>${b.amount}</span>
            <div className="flex gap-2">
              <button onClick={() => handleEdit(b)} className="bg-yellow-500 px-2 rounded">Edit</button>
              <button onClick={() => handleDelete(b.id)} className="bg-red-500 px-2 rounded">Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
    );
}