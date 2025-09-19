import {useState} from "react";
import api from "../api/api";

export default function ExpenseForm({refresh, refreshSummary}) {
    const [amount, setAmount] = useState("");
    const [category, setCategory] = useState("");
    const [date, setDate] = useState("");
    const [description, setDescription] = useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await api.post("/expenses/", {amount, category, date, description});
            setAmount(""); setCategory(""); setDate(""); setDescription("");
            refresh();
            refreshSummary();
        } catch (err) {
            alert(err.response.data.detail || "Error adding expense");
        }
    };

    return (
        <form
      onSubmit={handleSubmit}
      className="mb-8 rounded-2xl bg-gray-800 p-6 shadow-lg shadow-cyan-500/50"
    >
      <h3 className="mb-4 text-xl font-bold text-cyan-400">Add Expense</h3>

      <input
        type="number"
        placeholder="Amount"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        required
        className="mb-3 w-full rounded-lg bg-gray-700 px-4 py-2 text-white placeholder-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-1"
      />

      <input
        type="text"
        placeholder="Category"
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        required
        className="mb-3 w-full rounded-lg bg-gray-700 px-4 py-2 text-white placeholder-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-1"
      />

      <input
        type="date"
        value={date}
        onChange={(e) => setDate(e.target.value)}
        required
        className="mb-3 w-full rounded-lg bg-gray-700 px-4 py-2 text-white placeholder-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-1"
      />

      <input
        type="text"
        placeholder="Description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        className="mb-4 w-full rounded-lg bg-gray-700 px-4 py-2 text-white placeholder-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-1"
      />

      <button
        type="submit"
        className="w-full rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-gray-900 transition hover:bg-cyan-400 hover:shadow-lg hover:shadow-cyan-500/50"
      >
        Add
      </button>
    </form>
    );
}