import { apiClient } from './client'
import type {
  PaginatedResponse, User, UserCategory, UserFilters, UserListItem, UserType
} from './types'

export const usersApi = {
  list: (filters: UserFilters = {}) =>
    apiClient.get<PaginatedResponse<UserListItem>>('/users', { params: filters }).then(r => r.data),

  getById: (id: number) =>
    apiClient.get<User>(`/users/${id}`).then(r => r.data),

  create: (data: Partial<User>) =>
    apiClient.post<User>('/users', data).then(r => r.data),

  update: (id: number, data: Partial<User>) =>
    apiClient.patch<User>(`/users/${id}`, data).then(r => r.data),

  listCategories: () =>
    apiClient.get<UserCategory[]>('/users/categories/list').then(r => r.data),

  createCategory: (name: string) =>
    apiClient.post<UserCategory>('/users/categories', { name }).then(r => r.data),

  listTypes: () =>
    apiClient.get<UserType[]>('/users/types/list').then(r => r.data),

  createType: (name: string) =>
    apiClient.post<UserType>('/users/types', { name }).then(r => r.data),
}
