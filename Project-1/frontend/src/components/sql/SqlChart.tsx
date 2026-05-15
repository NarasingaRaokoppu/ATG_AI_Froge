import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ChartSuggestion } from "../../types";

interface Props {
  rows: Record<string, unknown>[];
  chart: ChartSuggestion;
}

const PIE_COLORS = ["#0f172a", "#1d4ed8", "#16a34a", "#f59e0b", "#be123c"];

export function SqlChart({ rows, chart }: Props) {
  if (rows.length === 0 || chart.chart_type === "table") {
    return null;
  }

  const xKey = chart.x_axis ?? Object.keys(rows[0])[0];
  const yKey = chart.y_axis ?? Object.keys(rows[0])[1];

  if (!xKey || !yKey) return null;

  return (
    <div className="h-80 rounded-xl border border-slate-200 bg-white p-3">
      <ResponsiveContainer width="100%" height="100%">
        {chart.chart_type === "bar" ? (
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={yKey} fill="#0f172a" />
          </BarChart>
        ) : chart.chart_type === "line" ? (
          <LineChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={yKey} stroke="#0f172a" strokeWidth={2} />
          </LineChart>
        ) : (
          <PieChart>
            <Tooltip />
            <Legend />
            <Pie data={rows} dataKey={yKey} nameKey={xKey} outerRadius={110}>
              {rows.map((_, index) => (
                <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
