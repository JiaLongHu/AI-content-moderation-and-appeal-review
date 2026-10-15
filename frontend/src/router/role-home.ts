import type { UserRole } from '../types/auth'

export function roleHomePath(role: UserRole): string {
  const paths: Record<UserRole, string> = {
    user: '/forum',
    content_reviewer: '/moderation',
    appeal_reviewer: '/appeals',
  }
  return paths[role]
}

