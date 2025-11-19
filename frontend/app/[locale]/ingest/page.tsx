'use client'

import { useState } from 'react'
import { apiClient, type IngestResponse, type DraftCard } from '@/lib/api'
import { Locale, t } from '@/lib/translations'
import { useParams } from 'next/navigation'

export default function IngestPage() {
  const params = useParams()
  const locale = (params?.locale || 'en-US') as Locale

  const [text, setText] = useState('')
  const [expertRef, setExpertRef] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<IngestResponse | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!text.trim()) {
      alert('Please enter transcript text')
      return
    }

    setLoading(true)

    try {
      const response = await apiClient.ingest({
        text,
        expert_ref: expertRef || undefined,
        locale,
      })

      setResult(response)
    } catch (error) {
      console.error('Ingest error:', error)
      alert(`Error: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveCard = async (card: DraftCard) => {
    try {
      await apiClient.createCard(card)
      alert(t(locale, 'common.success'))
    } catch (error) {
      console.error('Save error:', error)
      alert(`Error: ${error}`)
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{t(locale, 'ingest.title')}</h1>
        <p className="mt-2 text-sm text-gray-600">{t(locale, 'ingest.subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Left: Input */}
        <div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="text" className="block text-sm font-medium text-gray-700">
                {t(locale, 'ingest.placeholder')}
              </label>
              <textarea
                id="text"
                rows={20}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                placeholder={t(locale, 'ingest.placeholder')}
                value={text}
                onChange={(e) => setText(e.target.value)}
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="expert" className="block text-sm font-medium text-gray-700">
                {t(locale, 'ingest.expertRef')}
              </label>
              <input
                id="expert"
                type="text"
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                value={expertRef}
                onChange={(e) => setExpertRef(e.target.value)}
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary w-full"
            >
              {loading ? t(locale, 'ingest.processing') : t(locale, 'ingest.submit')}
            </button>
          </form>
        </div>

        {/* Right: Results */}
        <div>
          <h2 className="mb-4 text-lg font-semibold">{t(locale, 'ingest.draftCards')}</h2>

          {result && (
            <div className="mb-4 rounded-md bg-blue-50 p-4 text-sm">
              <div className="flex justify-between">
                <span>{t(locale, 'ingest.entities')}: {result.total_entities_extracted}</span>
                <span>{t(locale, 'ingest.processingTime')}: {result.processing_time.toFixed(2)}s</span>
              </div>
            </div>
          )}

          {result && result.cards.length === 0 && (
            <p className="text-gray-500">{t(locale, 'ingest.noCards')}</p>
          )}

          <div className="space-y-4">
            {result?.cards.map((card) => (
              <div key={card.id} className="card">
                <div className="mb-3 flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold">
                      {locale === 'zh-CN' ? card.summary_cn : card.summary_en}
                    </h3>
                    <div className="mt-1 flex gap-2">
                      <span className={`badge badge-${card.direction}`}>
                        {card.direction.toUpperCase()}
                      </span>
                      <span className="badge bg-gray-100">
                        {card.horizon}
                      </span>
                      <span className="badge bg-blue-100">
                        {(card.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium">{t(locale, 'playbook.instruments')}: </span>
                    {card.instruments.map(i => i.symbol).join(', ')}
                  </div>

                  <div>
                    <span className="font-medium">{t(locale, 'playbook.entryTrigger')}: </span>
                    {locale === 'zh-CN' ? card.entry_triggers[0]?.nl_cn : card.entry_triggers[0]?.nl_en}
                  </div>

                  <div>
                    <span className="font-medium">{t(locale, 'playbook.invalidator')}: </span>
                    {locale === 'zh-CN' ? card.invalidators[0]?.nl_cn : card.invalidators[0]?.nl_en}
                  </div>
                </div>

                <div className="mt-4">
                  <button
                    onClick={() => handleSaveCard(card)}
                    className="btn btn-primary btn-sm"
                  >
                    {t(locale, 'common.save')}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
