import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Quote {
  id: string
  text: string
  context?: string
  source?: string
  umap_x?: number
  umap_y?: number
  created_at: string
  author: Person
  similarity_score?: number
}

export interface Person {
  id: string
  name: string
  bio?: string
  created_at: string
}

export interface GraphNode {
  id: string
  label: string
  type: string
  data: Record<string, any>
}

export interface GraphEdge {
  source: string
  target: string
  type: string
  weight: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export const quoteApi = {
  list: (params?: { person?: string; limit?: number }) =>
    api.get<Quote[]>('/api/quotes', { params }),

  get: (id: string) =>
    api.get<Quote & { similar_quotes: Quote[] }>(`/api/quotes/${id}`),

  create: (data: { text: string; author: string; context?: string; source?: string }) =>
    api.post<Quote>('/api/quotes', data),

  update: (id: string, data: Partial<{ text: string; author: string; context?: string; source?: string }>) =>
    api.put<Quote>(`/api/quotes/${id}`, data),

  delete: (id: string) =>
    api.delete(`/api/quotes/${id}`),

  search: (query: string, limit?: number) =>
    api.get<Quote[]>('/api/search', { params: { q: query, limit } }),

  similar: (id: string, topK?: number) =>
    api.get<Quote[]>(`/api/similar/${id}`, { params: { top_k: topK } }),
}

export const graphApi = {
  get: () =>
    api.get<GraphData>('/api/graph'),
}

export const analyticsApi = {
  stats: () =>
    api.get('/api/analytics/stats'),

  recomputeSimilarities: () =>
    api.post('/api/analytics/recompute-similarities'),
}
