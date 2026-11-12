import type { ReviewDecisionPayload, ReviewTaskItem } from '../types/review'
import api from './client'

export async function listModerationTasks(): Promise<ReviewTaskItem[]> {
  return (await api.get<ReviewTaskItem[]>('/moderation/tasks')).data
}

export async function getModerationTask(taskId: number): Promise<ReviewTaskItem> {
  return (await api.get<ReviewTaskItem>(`/moderation/tasks/${taskId}`)).data
}

export async function decideModerationTask(
  taskId: number,
  payload: ReviewDecisionPayload,
): Promise<ReviewTaskItem> {
  return (await api.post<ReviewTaskItem>(`/moderation/tasks/${taskId}/decision`, payload)).data
}

export async function listModerationHistory(): Promise<ReviewTaskItem[]> {
  return (await api.get<ReviewTaskItem[]>('/moderation/tasks/history')).data
}
