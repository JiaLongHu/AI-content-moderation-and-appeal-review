export type UserRole = 'user' | 'content_reviewer' | 'appeal_reviewer'

export interface CurrentUser {
  id: number
  username: string
  role: UserRole
}

export interface LoginPayload {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: 'bearer'
  user: CurrentUser
}

