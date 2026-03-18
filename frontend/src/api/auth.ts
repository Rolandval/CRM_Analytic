import { apiClient } from './client'
import type { AdminUser, LoginRequest, TokenResponse } from './types'

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<TokenResponse>('/auth/login', data).then(r => r.data),

  me: () =>
    apiClient.get<AdminUser>('/auth/me').then(r => r.data),
}
