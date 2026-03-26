// ── Enums ─────────────────────────────────────────────────────────────────────
export type CallType = 'IN' | 'OUT'
export type CallState = 'ANSWER' | 'NOANSWER' | 'BUSY' | 'FAILED'

// ── Pagination ────────────────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface AdminUser {
  id: number
  username: string
  email: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  last_login: string | null
}

// ── Users ─────────────────────────────────────────────────────────────────────
export interface UserCategory {
  id: number
  name: string
}

export interface UserType {
  id: number
  name: string
}

export interface User {
  id: number
  phone_number: string | null
  name: string | null
  calls_count: number
  description: string | null
  created_at: string
  updated_at: string
  category: UserCategory | null
  types: UserType[]
}

export interface UserListItem {
  id: number
  phone_number: string | null
  name: string | null
  calls_count: number
  category: UserCategory | null
  types: UserType[]
}

// ── Calls ─────────────────────────────────────────────────────────────────────
export interface CallAiAnalytic {
  id: number
  call_id: number
  processing_status: string
  processed_at: string | null
  transcript: string | null
  conversation_topic: string | null
  key_points_of_the_dialogue: string | null
  next_steps: string | null
  attention_to_the_call: string | null
  operator_errors: string | null
  keywords: string | null
  clients_mood: string | null
  operators_mood: string | null
  customer_satisfaction: string | null
  operator_professionalism: string | null
  empathy: string | null
  clarity_of_communication: string | null
}

export interface Call {
  id: number
  user_id: number | null
  from_number: string | null
  to_number: string | null
  call_type: CallType | null
  call_state: CallState | null
  date: string | null
  seconds_fulltime: number
  seconds_talktime: number
  mp3_link: string | null
  callback: boolean
  created_at: string
}

export interface CallDetail extends Call {
  user: UserListItem | null
  ai_analytic: CallAiAnalytic | null
}

// ── Stats ─────────────────────────────────────────────────────────────────────
export interface CallStats {
  total: number
  by_type: Record<string, number>
  by_state: Record<string, number>
  avg_talk_duration_seconds: number
}

// ── Sync ──────────────────────────────────────────────────────────────────────
export interface SyncStats {
  total: number
  new: number
  updated: number
  skipped: number
  errors: number
}

export interface SyncResponse {
  status: string
  message: string
  stats: SyncStats
}

// ── Filters ───────────────────────────────────────────────────────────────────
export interface CallFilters {
  date_from?: string
  date_to?: string
  call_type?: CallType
  call_state?: CallState
  user_id?: number
  min_duration?: number
  max_duration?: number
  callback?: boolean
  search?: string
  page?: number
  page_size?: number
}

export interface UserFilters {
  category_id?: number
  type_id?: number
  search?: string
  has_analytics?: boolean
  sort_by?: 'id' | 'name' | 'phone_number' | 'calls_count' | 'created_at'
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}
