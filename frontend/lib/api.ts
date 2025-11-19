/**
 * API client for thesis-ticker-engine backend.
 */

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface IngestRequest {
  text: string;
  expert_ref?: string;
  locale?: string;
}

export interface IngestResponse {
  cards: DraftCard[];
  processing_time: number;
  total_entities_extracted: number;
  language_detected: string;
}

export interface DraftCard {
  id: string;
  asof: string;
  summary_cn?: string;
  summary_en?: string;
  direction: string;
  horizon: string;
  instruments: InstrumentRef[];
  entry_triggers: TriggerExpr[];
  invalidators: TriggerExpr[];
  catalysts: string[];
  risks: string[];
  why: QuoteReference[];
  confidence: number;
}

export interface InstrumentRef {
  symbol: string;
  venue: string;
  role: string;
  display_name_en?: string;
  display_name_cn?: string;
}

export interface TriggerExpr {
  type: string;
  expr: any;
  nl_cn?: string;
  nl_en?: string;
}

export interface QuoteReference {
  quote: string;
  source_loc?: string;
  gloss_cn?: string;
  gloss_en?: string;
}

export interface PortfolioStats {
  total_positions: number;
  open_positions: number;
  closed_positions: number;
  total_pnl: number;
  total_pnl_pct: number;
  win_rate: number;
  max_drawdown: number;
  twr: number;
  exposure_by_theme: Record<string, any>;
}

export interface Position {
  id: string;
  symbol: string;
  opened_at: string;
  entry_px: number;
  closed_at?: string;
  exit_px?: number;
  qty: number;
  card_id: string;
  status: string;
  current_px?: number;
  pnl?: number;
  pnl_pct?: number;
}

export interface AlertEvent {
  id: string;
  trigger_id: string;
  card_id: string;
  fired_at: string;
  symbol: string;
  price: number;
  reason: string;
  reason_cn?: string;
  reason_en?: string;
  invalidator: string;
}

export interface SimilarityCandidate {
  symbol: string;
  venue: string;
  score: number;
  explanation_cn?: string;
  explanation_en?: string;
  matched_features: Record<string, any>;
  current_price?: number;
}

// API functions
export const apiClient = {
  // Ingest
  async ingest(request: IngestRequest): Promise<IngestResponse> {
    const response = await api.post('/ingest', request);
    return response.data;
  },

  // Cards
  async getCards(week?: string): Promise<DraftCard[]> {
    const params = week ? { week } : {};
    const response = await api.get('/cards', { params });
    return response.data;
  },

  async getCard(cardId: string): Promise<DraftCard> {
    const response = await api.get(`/cards/${cardId}`);
    return response.data;
  },

  async createCard(card: DraftCard): Promise<DraftCard> {
    const response = await api.post('/cards', card);
    return response.data;
  },

  async updateCard(cardId: string, updates: Partial<DraftCard>): Promise<DraftCard> {
    const response = await api.put(`/cards/${cardId}`, updates);
    return response.data;
  },

  async deleteCard(cardId: string): Promise<void> {
    await api.delete(`/cards/${cardId}`);
  },

  // Alerts
  async enableAlerts(cardId: string, channels: string[]): Promise<any> {
    const response = await api.post('/alerts/enable', { card_id: cardId, channels });
    return response.data;
  },

  async getAlerts(limit?: number): Promise<AlertEvent[]> {
    const params = limit ? { limit } : {};
    const response = await api.get('/alerts', { params });
    return response.data;
  },

  // Portfolio
  async getPortfolio(includeClosed?: boolean): Promise<Position[]> {
    const params = includeClosed !== undefined ? { include_closed: includeClosed } : {};
    const response = await api.get('/portfolio', { params });
    return response.data;
  },

  async getPortfolioStats(): Promise<PortfolioStats> {
    const response = await api.get('/portfolio/stats');
    return response.data;
  },

  async openPosition(symbol: string, entryPx: number, qty: number, cardId: string): Promise<any> {
    const response = await api.post('/portfolio/positions', { symbol, entry_px: entryPx, qty, card_id: cardId });
    return response.data;
  },

  async closePosition(positionId: string, exitPx: number): Promise<any> {
    const response = await api.put(`/portfolio/positions/${positionId}/close`, { exit_px: exitPx });
    return response.data;
  },

  // Similarity
  async getSimilarTickers(cardId: string, topK?: number, minScore?: number): Promise<SimilarityCandidate[]> {
    const params: any = {};
    if (topK) params.top_k = topK;
    if (minScore) params.min_score = minScore;

    const response = await api.get(`/cards/${cardId}/similar`, { params });
    return response.data;
  },
};
