import type { ContentStatus, ContentType, ModerationSummary, RiskLevel } from './content'

export type RiskCategory =
  | 'normal'
  | 'sexual'
  | 'violence'
  | 'illegal_fraud'
  | 'hate_discrimination'
  | 'harassment'
  | 'privacy'
  | 'spam_advertising'

export interface ReviewTaskItem {
  task_status: 'pending' | 'completed'
  decision: 'publish' | 'reject' | null
  reviewer: string | null
  completed_at: string | null
  id: number
  content_id: number
  content_type: ContentType
  author: string
  title: string | null
  body: string
  content_status: ContentStatus
  created_at: string
  context: string | null
  moderation: ModerationSummary
}

export interface ReviewDecisionPayload {
  final_category: RiskCategory
  final_level: RiskLevel
  decision: 'publish' | 'reject'
}

export type AppealStatus = 'pending' | 'approved' | 'rejected'

export interface AppealItem {
  id: number
  content_id: number
  author: string
  content_type: ContentType
  title: string | null
  body: string
  content_status: ContentStatus
  appeal_reason: string
  appeal_status: AppealStatus
  created_at: string
  context: string | null
  original_moderation: ModerationSummary
  final_category: RiskCategory | null
  final_level: RiskLevel | null
  result_reason: string | null
}

export interface AppealDecisionPayload {
  final_category: RiskCategory
  final_level: RiskLevel
  decision: 'approved' | 'rejected'
  result_reason: string
}
