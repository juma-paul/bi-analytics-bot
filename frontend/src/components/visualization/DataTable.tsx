'use client'

import React, { useState } from 'react'

interface DataTableProps {
  columns: string[]
  rows: any[]
  rowCount: number
}

export default function DataTable({ columns, rows, rowCount }: DataTableProps) {
  const [page, setPage] = useState(0)
  const pageSize = 10
  const paginatedRows = rows.slice(page * pageSize, (page + 1) * pageSize)
  const totalPages = Math.ceil(rowCount / pageSize)

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-light">
              {columns.map((col) => (
                <th key={col} className="text-left py-3 px-4 font-semibold text-text-primary">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedRows.map((row, idx) => (
              <tr key={idx} className="border-b border-border-light hover:bg-bg-secondary transition-colors">
                {columns.map((col) => (
                  <td key={`${idx}-${col}`} className="py-3 px-4 text-text-secondary">
                    {row[col] !== null && row[col] !== undefined ? String(row[col]) : '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-text-tertiary">
            Showing {page * pageSize + 1} to {Math.min((page + 1) * pageSize, rowCount)} of{' '}
            {rowCount} rows
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="px-3 py-1 rounded text-sm bg-bg-secondary hover:bg-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page === totalPages - 1}
              className="px-3 py-1 rounded text-sm bg-bg-secondary hover:bg-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
