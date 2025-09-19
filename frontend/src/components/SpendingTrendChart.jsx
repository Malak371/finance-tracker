import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer } from "recharts";

export default function SpendingTrendChart({ data, period = "weekly" }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-md">
      <h2 className="text-lg text-black font-semibold mb-4">
        Spending Trend ({period})
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="total" stroke="#0088FE" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
