'use client'

import { useEffect, useState } from 'react'
import { apiClient, type DraftCard, type SimilarityCandidate } from '@/lib/api'
import { Locale, t } from '@/lib/translations'
import { useParams } from 'next/navigation'

export default function PlaybookPage() {
  const params = useParams()
  const locale = (params?.locale || 'en-US') as Locale

  const [cards, setCards] = useState<DraftCard[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCard, setSelectedCard] = useState<string | null>(null)
  const [similarTickers, setSimilarTickers] = useState<Record<string, SimilarityCandidate[]>>({})

  useEffect(() => {
    loadCards()
  }, [])

  const loadCards = async () => {
    try {
      const data = await apiClient.getCards()
      setCards(data)
    } catch (error) {
      console.error('Error loading cards:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadSimilarTickers = async (cardId: string) => {
    if (similarTickers[cardId]) {
      return // Already loaded
    }

    try {
      const data = await apiClient.getSimilarTickers(cardId, 5)
      setSimilarTickers(prev => ({ ...prev, [cardId]: data }))
    } catch (error) {
      console.error('Error loading similar tickers:', error)
    }
  }

  const handleEnableAlerts = async (cardId: string) => {
    try {
      await apiClient.enableAlerts(cardId, ['email'])
      alert(t(locale, 'common.success'))
    } catch (error) {
      console.error('Error enabling alerts:', error)
      alert(`Error: ${error}`)
    }
  }

  if (loading) {
    return <div className="text-center py-12">{t(locale, 'common.loading')}</div>
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{t(locale, 'playbook.title')}</h1>
        <p className="mt-2 text-sm text-gray-600">{t(locale, 'playbook.subtitle')}</p>
      </div>

      {cards.length === 0 ? (
        <p className="text-gray-500">{t(locale, 'playbook.noCards')}</p>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {cards.map((card) => (
            <div key={card.id} className="card">
              {/* Header */}
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {locale === 'zh-CN' ? card.summary_cn : card.summary_en}
                </h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  <span className={`badge badge-${card.direction}`}>
                    {card.direction}
                  </span>
                  <span className="badge bg-gray-100">
                    {card.horizon}
                  </span>
                  <span className="badge bg-blue-100">
                    {t(locale, 'playbook.confidence')}: {(card.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Instruments */}
              <div className="mb-3">
                <h4 className="text-xs font-semibold uppercase text-gray-500">
                  {t(locale, 'playbook.instruments')}
                </h4>
                <div className="mt-1 flex flex-wrap gap-1">
                  {card.instruments.map((inst, idx) => (
                    <span key={idx} className="rounded bg-gray-100 px-2 py-1 text-sm font-mono">
                      {inst.symbol}
                    </span>
                  ))}
                </div>
              </div>

              {/* Entry Trigger */}
              <div className="mb-3 text-sm">
                <h4 className="text-xs font-semibold uppercase text-gray-500">
                  {t(locale, 'playbook.entryTrigger')}
                </h4>
                <p className="mt-1 text-green-700">
                  {locale === 'zh-CN' ? card.entry_triggers[0]?.nl_cn : card.entry_triggers[0]?.nl_en}
                </p>
              </div>

              {/* Invalidator */}
              <div className="mb-3 text-sm">
                <h4 className="text-xs font-semibold uppercase text-gray-500">
                  {t(locale, 'playbook.invalidator')}
                </h4>
                <p className="mt-1 text-red-700">
                  {locale === 'zh-CN' ? card.invalidators[0]?.nl_cn : card.invalidators[0]?.nl_en}
                </p>
              </div>

              {/* Catalysts */}
              {card.catalysts && card.catalysts.length > 0 && (
                <div className="mb-3 text-sm">
                  <h4 className="text-xs font-semibold uppercase text-gray-500">
                    {t(locale, 'playbook.catalysts')}
                  </h4>
                  <ul className="mt-1 list-inside list-disc text-gray-700">
                    {card.catalysts.slice(0, 2).map((cat, idx) => (
                      <li key={idx}>{cat}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Why */}
              {card.why && card.why.length > 0 && (
                <div className="mb-4 text-sm">
                  <h4 className="text-xs font-semibold uppercase text-gray-500">
                    {t(locale, 'playbook.why')}
                  </h4>
                  <div className="mt-1 space-y-1">
                    {card.why.slice(0, 2).map((quote, idx) => (
                      <p key={idx} className="text-xs italic text-gray-600">
                        "{quote.quote.substring(0, 100)}..."
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={() => handleEnableAlerts(card.id)}
                  className="btn btn-primary flex-1 text-xs"
                >
                  {t(locale, 'playbook.enableAlerts')}
                </button>
                <button
                  onClick={() => {
                    setSelectedCard(selectedCard === card.id ? null : card.id)
                    if (selectedCard !== card.id) {
                      loadSimilarTickers(card.id)
                    }
                  }}
                  className="btn btn-secondary flex-1 text-xs"
                >
                  {t(locale, 'playbook.similar')}
                </button>
              </div>

              {/* Similar tickers */}
              {selectedCard === card.id && similarTickers[card.id] && (
                <div className="mt-4 border-t pt-4">
                  <h4 className="mb-2 text-sm font-semibold">{t(locale, 'playbook.similar')}</h4>
                  <div className="space-y-2">
                    {similarTickers[card.id].slice(0, 3).map((sim, idx) => (
                      <div key={idx} className="rounded bg-gray-50 p-2 text-xs">
                        <div className="flex justify-between">
                          <span className="font-mono font-semibold">{sim.symbol}</span>
                          <span className="text-gray-500">{(sim.score * 100).toFixed(0)}%</span>
                        </div>
                        <p className="mt-1 text-gray-600">
                          {locale === 'zh-CN' ? sim.explanation_cn : sim.explanation_en}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
