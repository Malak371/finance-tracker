import CategoryChart from "./CategoryChart";
import SpendingTrendChart from "./SpendingTrendChart";

export default function Dashboard({ summary, budgets, weeklyData, monthlyData }) {
  return (
    <div className="grid grid-cols-1 gap-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-md flex flex-col items-center">
          <h2 className="text-lg text-black font-semibold">Total Spent</h2>
          <p className="text-3xl font-bold text-blue-600 mt-2">${summary.total_spent}</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md">
          <h2 className="text-lg text-black font-semibold mb-2">Spending by Category</h2>
          <CategoryChart summary={summary} />
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-md">
        <h2 className="text-lg text-black font-semibold mb-4">Budgets</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {budgets.map((b) => {
            const spent = summary.breakdown[b.category] || 0;
            const percent = (spent / b.amount) * 100;
            const alert = percent >= 80;

            return (
              <div
                key={b.id}
                className={`p-4 rounded shadow flex justify-between items-center ${
                  alert ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"
                }`}
              >
                <span>{b.category}</span>
                <span>${spent} / ${b.amount}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SpendingTrendChart data={weeklyData} period="Weekly" />
        <SpendingTrendChart data={monthlyData} period="Monthly" />
      </div>
    </div>
  );
}
