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
}
