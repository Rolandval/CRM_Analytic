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

  update: (id: number, data: { name?: string; description?: string; category_id?: number | null; type_ids?: number[] }) =>
    apiClient.patch<User>(`/users/${id}`, data).then(r => r.data),

  delete: (id: number) =>
    apiClient.delete(`/users/${id}`),

  listCategories: () =>
    apiClient.get<UserCategory[]>('/users/categories/list').then(r => r.data),

  createCategory: (name: string) =>
    apiClient.post<UserCategory>('/users/categories', { name }).then(r => r.data),

  updateCategory: (id: number, name: string) =>
    apiClient.patch<UserCategory>(`/users/categories/${id}`, { name }).then(r => r.data),

  deleteCategory: (id: number) =>
    apiClient.delete(`/users/categories/${id}`),

  listTypes: () =>
    apiClient.get<UserType[]>('/users/types/list').then(r => r.data),

  createType: (name: string) =>
    apiClient.post<UserType>('/users/types', { name }).then(r => r.data),

  updateType: (id: number, name: string) =>
    apiClient.patch<UserType>(`/users/types/${id}`, { name }).then(r => r.data),

  deleteType: (id: number) =>
    apiClient.delete(`/users/types/${id}`),
}
