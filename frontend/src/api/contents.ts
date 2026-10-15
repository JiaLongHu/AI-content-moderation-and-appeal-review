import type { MyContentItem, PublicPost, PublicPostDetail, SubmissionResult } from '../types/content'
import api from './client'

export async function listPosts(): Promise<PublicPost[]> {
  return (await api.get<PublicPost[]>('/posts')).data
}

export async function getPost(postId: number): Promise<PublicPostDetail> {
  return (await api.get<PublicPostDetail>(`/posts/${postId}`)).data
}

export async function createPost(title: string, body: string): Promise<SubmissionResult> {
  return (await api.post<SubmissionResult>('/posts', { title, body })).data
}

export async function createComment(postId: number, body: string): Promise<SubmissionResult> {
  return (await api.post<SubmissionResult>(`/posts/${postId}/comments`, { body })).data
}

export async function createReply(commentId: number, body: string): Promise<SubmissionResult> {
  return (await api.post<SubmissionResult>(`/comments/${commentId}/replies`, { body })).data
}

export async function listMyContents(): Promise<MyContentItem[]> {
  return (await api.get<MyContentItem[]>('/me/contents')).data
}
