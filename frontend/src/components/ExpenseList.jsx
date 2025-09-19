import {useEffect, useState} from "react";
import api from "../api/api";

export default function ExpenseList({ expenses, refresh }) {
  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({ category: "", amount: 0, date: "", description: "" });

  const handleExport = async () => {
  try {
    const res = await api.get("/expenses/export", {
      responseType: "blob",
    });

    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "expenses.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (err) {
    console.error("Export failed:", err);
  }
};
const startEdit = (expense) => {
    setEditingId(expense.id);
    setEditData({
      category: expense.category,
      amount: expense.amount,
      date: expense.date,
      description: expense.description || "",
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditData({ category: "", amount: 0, date: "", description: "" });
  };

  const saveEdit = async (id) => {
    try {
      await api.put(`/expenses/${id}`, editData);
      cancelEdit();
      refresh();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this expense?")) return;
    try {
      await api.delete(`/expenses/${id}`);
      refresh();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="rounded-2xl bg-gray-800 p-6 shadow-lg shadow-cyan-500/50">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 gap-2">
        <h3 className="text-xl font-bold text-cyan-400">Expenses</h3>
        <button
          onClick={handleExport}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
        >
          Export CSV
        </button>
      </div>

      <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-gray-300">
        {expenses.map((e) => (
          <li key={e.id} className="rounded-lg bg-gray-700 px-4 py-2 flex flex-col shadow-sm">
            {editingId === e.id ? (
              <div className="flex flex-col gap-2">
                <input
                  type="text"
                  value={editData.category}
                  onChange={(ev) => setEditData({ ...editData, category: ev.target.value })}
                  className="p-1 rounded text-black"
                />
                <input
                  type="number"
                  value={editData.amount}
                  onChange={(ev) => setEditData({ ...editData, amount: parseFloat(ev.target.value) })}
                  className="p-1 rounded text-black"
                />
                <input
                  type="date"
                  value={editData.date}
                  onChange={(ev) => setEditData({ ...editData, date: ev.target.value })}
                  className="p-1 rounded text-black"
                />
                <input
                  type="text"
                  value={editData.description}
                  onChange={(ev) => setEditData({ ...editData, description: ev.target.value })}
                  className="p-1 rounded text-black"
                  placeholder="Description"
                />
                <div className="flex gap-2">
                  <button onClick={() => saveEdit(e.id)} className="bg-blue-600 px-2 rounded">Save</button>
                  <button onClick={cancelEdit} className="bg-gray-500 px-2 rounded">Cancel</button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex justify-between items-center mb-1">
                  <span className="font-semibold">{e.category}</span>
                  <span className="text-cyan-300 font-bold">${e.amount}</span>
                </div>
                <div className="text-sm text-gray-400">
                  {e.date} {e.description && `— ${e.description}`}
                </div>
                <div className="flex gap-2 mt-2">
                  <button onClick={() => startEdit(e)} className="bg-yellow-500 px-2 rounded">Edit</button>
                  <button onClick={() => handleDelete(e.id)} className="bg-red-500 px-2 rounded">Delete</button>
                </div>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  );

}
