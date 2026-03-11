'use client'

import React from 'react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const COLORS = ['#0071E3', '#34C759', '#FF9500', '#FF3B30', '#AF52DE', '#A2845E']

interface ChartConfig {
  type: string
  config: {
    xAxis?: string
    yAxis?: string
    title?: string
  }
}

interface QueryResults {
  columns: string[]
  rows: any[]
}

interface ChartRendererProps {
  visualization: ChartConfig
  data: QueryResults
}

export default function ChartRenderer({ visualization, data }: ChartRendererProps) {
  const chartType = visualization.type.toLowerCase()
  const chartConfig = visualization.config

  if (!data.rows || data.rows.length === 0) {
    return <div className="text-sm text-text-tertiary text-center py-4">No data to visualize</div>
  }

  try {
    switch (chartType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.rows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chartConfig.xAxis || data.columns[0]} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar
                dataKey={chartConfig.yAxis || data.columns[1]}
                fill="#0071E3"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        )

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.rows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chartConfig.xAxis || data.columns[0]} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey={chartConfig.yAxis || data.columns[1]}
                stroke="#0071E3"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )

      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data.rows}
                dataKey={chartConfig.yAxis || data.columns[1]}
                nameKey={chartConfig.xAxis || data.columns[0]}
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                {data.rows.map((_, idx) => (
                  <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        )

      case 'table':
      default:
        return <div className="text-sm text-text-tertiary">Table view</div>
    }
  } catch (error) {
    return (
      <div className="text-sm text-accent-red p-4 bg-accent-red/10 rounded">
        Failed to render chart: {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    )
  }
}
