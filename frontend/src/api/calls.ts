import { apiClient } from './client'
import type {
  Call, CallDetail, CallFilters, CallStats, PaginatedResponse, SyncResponse
} from './types'

export const callsApi = {
  list: (filters: CallFilters = {}) =>
    apiClient.get<PaginatedResponse<Call>>('/calls', { params: filters }).then(r => r.data),

  getById: (id: number) =>
    apiClient.get<CallDetail>(`/calls/${id}`).then(r => r.data),

  getStats: () =>
    apiClient.get<CallStats>('/calls/stats').then(r => r.data),

  syncAll: () =>
    apiClient.post<SyncResponse>('/unitalk/sync/all').then(r => r.data),

  syncToday: () =>
    apiClient.post<SyncResponse>('/unitalk/sync/today').then(r => r.data),

  export: (format: 'csv' | 'xlsx' | 'txt', filters: Omit<CallFilters, 'page' | 'page_size'> = {}) =>
    apiClient.get('/calls/export', {
      params: { format, ...filters },
      responseType: 'blob',
    }).then(r => ({ blob: r.data as Blob, filename: extractFilename(r.headers['content-disposition']) })),
}

function extractFilename(disposition: string | undefined): string {
  if (!disposition) return 'export'
  const m = /filename\*=UTF-8''([^;]+)/.exec(disposition) || /filename="?([^"]+)"?/.exec(disposition)
  return m ? decodeURIComponent(m[1]) : 'export'
}
