'use client'

import { useEffect, useState } from 'react'
import { apiClient, type Position, type PortfolioStats } from '@/lib/api'
import { Locale, t } from '@/lib/translations'
import { useParams } from 'next/navigation'
import { format } from 'date-fns'

export default function ScoreboardPage() {
  const params = useParams()
  const locale = (params?.locale || 'en-US') as Locale

  const [positions, setPositions] = useState<Position[]>([])
  const [stats, setStats] = useState<PortfolioStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [positionsData, statsData] = await Promise.all([
        apiClient.getPortfolio(true),
        apiClient.getPortfolioStats(),
      ])

      setPositions(positionsData)
      setStats(statsData)
    } catch (error) {
      console.error('Error loading portfolio:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">{t(locale, 'common.loading')}</div>
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{t(locale, 'scoreboard.title')}</h1>
        <p className="mt-2 text-sm text-gray-600">{t(locale, 'scoreboard.subtitle')}</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="mb-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div className="card">
            <h3 className="text-sm font-medium text-gray-500">{t(locale, 'scoreboard.totalPnL')}</h3>
            <p className={`mt-2 text-3xl font-bold ${stats.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${stats.total_pnl.toFixed(2)}
            </p>
            <p className="mt-1 text-sm text-gray-500">
              {stats.total_pnl_pct >= 0 ? '+' : ''}{stats.total_pnl_pct.toFixed(2)}%
            </p>
          </div>

          <div className="card">
            <h3 className="text-sm font-medium text-gray-500">{t(locale, 'scoreboard.winRate')}</h3>
            <p className="mt-2 text-3xl font-bold text-blue-600">
              {stats.win_rate.toFixed(1)}%
            </p>
            <p className="mt-1 text-sm text-gray-500">
              {stats.closed_positions} {t(locale, 'scoreboard.closed')}
            </p>
          </div>

          <div className="card">
            <h3 className="text-sm font-medium text-gray-500">{t(locale, 'scoreboard.maxDrawdown')}</h3>
            <p className="mt-2 text-3xl font-bold text-red-600">
              {stats.max_drawdown.toFixed(1)}%
            </p>
          </div>

          <div className="card">
            <h3 className="text-sm font-medium text-gray-500">{t(locale, 'scoreboard.twr')}</h3>
            <p className={`mt-2 text-3xl font-bold ${stats.twr >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {stats.twr >= 0 ? '+' : ''}{stats.twr.toFixed(2)}%
            </p>
          </div>
        </div>
      )}

      {/* Positions */}
      <div className="mb-4 flex justify-between items-center">
        <h2 className="text-xl font-semibold">{t(locale, 'scoreboard.positions')}</h2>
        <div className="text-sm text-gray-500">
          {stats?.open_positions} {t(locale, 'scoreboard.open')} · {stats?.closed_positions} {t(locale, 'scoreboard.closed')}
        </div>
      </div>

      {positions.length === 0 ? (
        <p className="text-gray-500">{t(locale, 'scoreboard.noPositions')}</p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Symbol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Entry
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Current/Exit
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Qty
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  P&L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  P&L %
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {positions.map((pos) => (
                <tr key={pos.id}>
                  <td className="whitespace-nowrap px-6 py-4 font-mono font-semibold">
                    {pos.symbol}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm">
                    ${Number(pos.entry_px).toFixed(2)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm">
                    ${(pos.current_px ? Number(pos.current_px) : pos.exit_px ? Number(pos.exit_px) : 0).toFixed(2)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm">
                    {Number(pos.qty)}
                  </td>
                  <td className={`whitespace-nowrap px-6 py-4 text-sm font-semibold ${
                    (pos.pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {pos.pnl ? (pos.pnl >= 0 ? '+' : '') + Number(pos.pnl).toFixed(2) : '-'}
                  </td>
                  <td className={`whitespace-nowrap px-6 py-4 text-sm ${
                    (pos.pnl_pct || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {pos.pnl_pct ? (pos.pnl_pct >= 0 ? '+' : '') + pos.pnl_pct.toFixed(2) + '%' : '-'}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm">
                    <span className={`badge ${pos.status === 'open' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {pos.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
