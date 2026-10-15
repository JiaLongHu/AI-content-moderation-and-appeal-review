export type ContentType = 'post' | 'comment' | 'reply'
export type ContentStatus = 'auto_reviewing' | 'pending_manual_review' | 'published' | 'rejected'
export type RiskLevel = 'L0' | 'L1' | 'L2' | 'L3' | 'L4'

export interface ModerationSummary {
  categories: string[]
  confidences: Record<string, number>
  final_category: string
  final_level: RiskLevel
  reason: string
}

export interface SubmissionResult {
  id: number
  content_type: ContentType
  status: ContentStatus
  moderation: ModerationSummary
}

export interface PublicReply { id: number; author: string; body: string; created_at: string }
export interface PublicComment extends PublicReply { replies: PublicReply[] }
export interface PublicPost { id: number; author: string; title: string; body: string; created_at: string }
export interface PublicPostDetail extends PublicPost { comments: PublicComment[] }

export interface MyContentItem {
  id: number
  content_type: ContentType
  title: string | null
  body: string
  post_id: number | null
  parent_comment_id: number | null
  status: ContentStatus
  created_at: string
  moderation: ModerationSummary
}
