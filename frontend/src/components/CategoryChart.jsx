import { PieChart, Pie, Cell, Tooltip, Legend } from "recharts";

export default function CategoryChart({ summary }) {
  const data = Object.entries(summary.breakdown).map(([cat, amt]) => ({ name: cat, value: amt }));
  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#A28CF5", "#FF6B6B"];

  return (
    <PieChart width={400} height={300}>
      <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
        {data.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
        ))}
      </Pie>
      <Tooltip />
      <Legend />
    </PieChart>
  );
}
