import type { AppealDecisionPayload, AppealItem } from '../types/review'
import api from './client'

export async function createAppeal(contentId: number, reason: string): Promise<AppealItem> {
  return (await api.post<AppealItem>(`/contents/${contentId}/appeals`, { reason })).data
}

export async function listMyAppeals(): Promise<AppealItem[]> {
  return (await api.get<AppealItem[]>('/me/appeals')).data
}

export async function listAppealTasks(): Promise<AppealItem[]> {
  return (await api.get<AppealItem[]>('/appeal-review/tasks')).data
}

export async function getAppealTask(appealId: number): Promise<AppealItem> {
  return (await api.get<AppealItem>(`/appeal-review/tasks/${appealId}`)).data
}

export async function decideAppealTask(
  appealId: number,
  payload: AppealDecisionPayload,
): Promise<AppealItem> {
  return (await api.post<AppealItem>(`/appeal-review/tasks/${appealId}/decision`, payload)).data
}
