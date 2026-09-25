import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { RootCause } from '../types';

interface RootCauseChartProps {
  data: RootCause[];
}

const COLORS = [
  '#8884d8', // timing - purple
  '#82ca9d', // state_leakage - green
  '#ffc658', // ordering - yellow
  '#ff7300', // environment - orange
  '#d0ed57', // unknown - lime
];

export default function RootCauseChart({ data }: RootCauseChartProps) {
  const chartData = data.map(item => ({
    name: item.cause.replace(/_/g, ' '),
    value: item.count,
    percentage: item.percentage
  }));
  
  return (
    <div className="root-cause-chart">
      <h2>Root Cause Distribution</h2>
      
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
              label={({ name, percentage }) => `${name}: ${percentage}%`}
            >
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              formatter={(value: number, name: string) => [
                `${value} tests (${chartData.find(d => d.name === name)?.percentage}%)`,
                name
              ]}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
      
      <div className="cause-list">
        {data.map((cause, index) => (
          <div key={cause.cause} className="cause-item">
            <div 
              className="cause-color"
              style={{ backgroundColor: COLORS[index % COLORS.length] }}
            />
            <span className="cause-name">{cause.cause.replace(/_/g, ' ')}</span>
            <span className="cause-count">{cause.count}</span>
            <span className="cause-percentage">{cause.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
