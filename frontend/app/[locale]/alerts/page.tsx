'use client'

import { useEffect, useState } from 'react'
import { apiClient, type AlertEvent } from '@/lib/api'
import { Locale, t } from '@/lib/translations'
import { useParams } from 'next/navigation'
import { format } from 'date-fns'

export default function AlertsPage() {
  const params = useParams()
  const locale = (params?.locale || 'en-US') as Locale

  const [alerts, setAlerts] = useState<AlertEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAlerts()
  }, [])

  const loadAlerts = async () => {
    try {
      const data = await apiClient.getAlerts(50)
      setAlerts(data)
    } catch (error) {
      console.error('Error loading alerts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddPosition = async (alert: AlertEvent, qty: number = 100) => {
    try {
      await apiClient.openPosition(alert.symbol, alert.price, qty, alert.card_id)
      alert(t(locale, 'common.success'))
    } catch (error) {
      console.error('Error adding position:', error)
      alert(`Error: ${error}`)
    }
  }

  if (loading) {
    return <div className="text-center py-12">{t(locale, 'common.loading')}</div>
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{t(locale, 'alerts.title')}</h1>
        <p className="mt-2 text-sm text-gray-600">{t(locale, 'alerts.subtitle')}</p>
      </div>

      {alerts.length === 0 ? (
        <p className="text-gray-500">{t(locale, 'alerts.noAlerts')}</p>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <div key={alert.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="rounded bg-blue-100 px-3 py-1 font-mono text-lg font-semibold text-blue-900">
                      {alert.symbol}
                    </span>
                    <span className="text-2xl font-bold text-gray-900">
                      ${alert.price.toFixed(2)}
                    </span>
                  </div>

                  <p className="mt-2 text-sm text-gray-700">
                    {locale === 'zh-CN' ? alert.reason_cn : alert.reason_en || alert.reason}
                  </p>

                  <p className="mt-1 text-xs text-gray-500">
                    {format(new Date(alert.fired_at), 'PPpp')}
                  </p>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleAddPosition(alert)}
                    className="btn btn-primary"
                  >
                    {t(locale, 'alerts.addPosition')}
                  </button>
                  <button className="btn btn-secondary">
                    {t(locale, 'alerts.ignore')}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
