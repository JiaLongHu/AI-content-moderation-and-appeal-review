<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { createAppeal, listMyAppeals } from '../api/appeals'
import { createComment, createPost, createReply, getPost, listMyContents, listPosts } from '../api/contents'
import { useAuthStore } from '../stores/auth'
import type { ContentStatus, MyContentItem, PublicPost, PublicPostDetail, SubmissionResult } from '../types/content'
import type { AppealItem } from '../types/review'

type Section = 'forum' | 'create' | 'mine' | 'appeals'
const auth = useAuthStore()
const router = useRouter()
const section = ref<Section>('forum')
const posts = ref<PublicPost[]>([])
const detail = ref<PublicPostDetail | null>(null)
const mine = ref<MyContentItem[]>([])
const appeals = ref<AppealItem[]>([])
const appealReasons = ref<Record<number, string>>({})
const title = ref('')
const body = ref('')
const commentBody = ref('')
const replyBodies = ref<Record<number, string>>({})
const loading = ref(false)
const errorMessage = ref('')
const resultMessage = ref('')

const statusLabels: Record<ContentStatus, string> = {
  auto_reviewing: '自动审核中', pending_manual_review: '等待人工审核', published: '已发布', rejected: '已拒绝',
}
const typeLabels = { post: '帖子', comment: '评论', reply: '回复' }
const appealStatusLabels = { pending: '等待复核', approved: '申诉通过', rejected: '申诉驳回' }
const canSubmitPost = computed(() => title.value.trim().length > 0 && body.value.trim().length > 0)

function errorText(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { detail?: string } | undefined)?.detail ?? '请求失败，请稍后重试'
  }
  return '请求失败，请稍后重试'
}

function submissionText(result: SubmissionResult): string {
  if (result.status === 'published') return '审核通过，内容已发布。'
  if (result.status === 'rejected') return `内容未通过：${result.moderation.reason}`
  return '内容已提交，正在等待人工审核。'
}

async function run(task: () => Promise<void>): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try { await task() } catch (error) { errorMessage.value = errorText(error) } finally { loading.value = false }
}

async function loadPosts(): Promise<void> { await run(async () => { posts.value = await listPosts() }) }
async function openPost(id: number): Promise<void> { await run(async () => { detail.value = await getPost(id) }) }

async function showSection(next: Section): Promise<void> {
  section.value = next
  detail.value = null
  resultMessage.value = ''
  if (next === 'forum') await loadPosts()
  if (next === 'mine') await run(async () => {
    const [contents, ownAppeals] = await Promise.all([listMyContents(), listMyAppeals()])
    mine.value = contents
    appeals.value = ownAppeals
  })
  if (next === 'appeals') await run(async () => { appeals.value = await listMyAppeals() })
}

async function submitPost(): Promise<void> {
  if (!canSubmitPost.value) return
  await run(async () => {
    resultMessage.value = submissionText(await createPost(title.value.trim(), body.value.trim()))
    title.value = ''; body.value = ''
  })
}

async function submitComment(): Promise<void> {
  if (!detail.value || !commentBody.value.trim()) return
  const postId = detail.value.id
  await run(async () => {
    resultMessage.value = submissionText(await createComment(postId, commentBody.value.trim()))
    commentBody.value = ''; detail.value = await getPost(postId)
  })
}

async function submitReply(commentId: number): Promise<void> {
  const text = replyBodies.value[commentId]?.trim()
  if (!detail.value || !text) return
  const postId = detail.value.id
  await run(async () => {
    resultMessage.value = submissionText(await createReply(commentId, text))
    replyBodies.value[commentId] = ''; detail.value = await getPost(postId)
  })
}

function hasAppeal(contentId: number): boolean {
  return appeals.value.some((appeal) => appeal.content_id === contentId)
}

async function submitAppeal(contentId: number): Promise<void> {
  const reason = appealReasons.value[contentId]?.trim()
  if (!reason || reason.length < 10) return
  await run(async () => {
    await createAppeal(contentId, reason)
    resultMessage.value = '申诉已提交，等待复核。'
    appealReasons.value[contentId] = ''
    appeals.value = await listMyAppeals()
  })
}

function logout(): void { auth.logout(); void router.replace('/login') }
onMounted(loadPosts)
</script>

<template>
  <main class="shell forum-shell">
    <section class="community-banner"><div><span class="banner-kicker">WELCOME TO OUR COMMUNITY</span><h2>兴趣相遇，灵感发生。</h2><p>聊聊日常，分享发现。在这里，看见文字的温度。</p><button @click="showSection('create')">＋ 发布我的第一份灵感</button></div><div class="banner-art" aria-hidden="true"><span class="floating-note note-one">今天也有新发现 ✦</span><div class="smile-card">:)</div><span class="floating-note note-two">hello, world!</span><i class="art-orbit" /></div></section>
    <div class="community-layout">
    <section class="page-card forum-card">
      <header class="page-header">
        <div><p class="muted">{{ auth.user?.username }} · 普通用户</p><h1>社区动态<span class="heading-label">发现同频的你</span></h1></div>
        <el-button @click="logout">退出登录</el-button>
      </header>
      <nav class="forum-nav" aria-label="用户功能">
        <button :class="{ active: section === 'forum' }" @click="showSection('forum')">社区帖子</button>
        <button :class="{ active: section === 'create' }" @click="showSection('create')">发布帖子</button>
        <button :class="{ active: section === 'mine' }" @click="showSection('mine')">我的内容</button>
        <button :class="{ active: section === 'appeals' }" @click="showSection('appeals')">我的申诉</button>
      </nav>
      <p v-if="errorMessage" class="notice error">{{ errorMessage }}</p>
      <p v-if="resultMessage" class="notice success">{{ resultMessage }}</p>
      <p v-if="loading" class="muted loading-text">正在处理…</p>

      <section v-if="section === 'forum' && !detail" class="content-list">
        <article v-for="post in posts" :key="post.id" class="content-item clickable" tabindex="0" role="button" @keydown.enter="openPost(post.id)" @keydown.space.prevent="openPost(post.id)" @click="openPost(post.id)">
          <div class="item-meta">{{ post.author }} · {{ new Date(post.created_at).toLocaleString() }}</div>
          <h2>{{ post.title }}</h2><p>{{ post.body }}</p>
        </article>
        <el-empty v-if="!loading && posts.length === 0" description="还没有已发布的帖子" />
      </section>

      <section v-else-if="section === 'forum' && detail" class="post-detail">
        <button class="text-button" @click="detail = null">← 返回帖子列表</button>
        <article class="content-item featured"><div class="item-meta">{{ detail.author }} · {{ new Date(detail.created_at).toLocaleString() }}</div><h2>{{ detail.title }}</h2><p>{{ detail.body }}</p></article>
        <div class="composer compact"><textarea v-model="commentBody" maxlength="500" placeholder="写下你的评论（最多500字）" /><div class="composer-actions"><span>{{ commentBody.length }}/500</span><el-button type="primary" :disabled="!commentBody.trim()" @click="submitComment">发表评论</el-button></div></div>
        <h3 class="section-title">评论</h3>
        <article v-for="comment in detail.comments" :key="comment.id" class="comment-card">
          <div class="item-meta">{{ comment.author }} · {{ new Date(comment.created_at).toLocaleString() }}</div><p>{{ comment.body }}</p>
          <div v-for="reply in comment.replies" :key="reply.id" class="reply-card"><div class="item-meta">{{ reply.author }} 回复</div><p>{{ reply.body }}</p></div>
          <div class="reply-composer"><input v-model="replyBodies[comment.id]" maxlength="500" placeholder="回复这条评论"><el-button :disabled="!replyBodies[comment.id]?.trim()" @click="submitReply(comment.id)">回复</el-button></div>
        </article>
        <el-empty v-if="detail.comments.length === 0" description="还没有评论" />
      </section>

      <section v-else-if="section === 'create'" class="composer post-composer">
        <h2>发布新帖子</h2>
        <label>标题<input v-model="title" maxlength="100" placeholder="1～100字"></label>
        <label>正文<textarea v-model="body" maxlength="3000" placeholder="1～3000字" /></label>
        <div class="composer-actions"><span>{{ body.length }}/3000</span><el-button type="primary" :disabled="!canSubmitPost || loading" @click="submitPost">提交审核</el-button></div>
        <p class="muted">提交后不可编辑或删除；审核结果会显示在“我的内容”。</p>
      </section>

      <section v-else-if="section === 'mine'" class="content-list">
        <article v-for="item in mine" :key="item.id" class="content-item">
          <div class="status-row"><span class="status-pill" :data-status="item.status">{{ statusLabels[item.status] }}</span><span>{{ typeLabels[item.content_type] }} · {{ item.moderation.final_level }}</span></div>
          <h2 v-if="item.title">{{ item.title }}</h2><p>{{ item.body }}</p><p class="moderation-reason">{{ item.moderation.reason }}</p>
          <div v-if="item.status === 'rejected' && !hasAppeal(item.id)" class="appeal-box">
            <textarea v-model="appealReasons[item.id]" maxlength="500" placeholder="填写申诉说明（10～500字）" />
            <el-button type="primary" :disabled="(appealReasons[item.id]?.trim().length ?? 0) < 10" @click="submitAppeal(item.id)">提交申诉</el-button>
          </div>
          <p v-else-if="item.status === 'rejected'" class="muted">该内容已提交过申诉</p>
        </article>
        <el-empty v-if="!loading && mine.length === 0" description="你还没有发布过内容" />
      </section>
      <section v-else class="content-list">
        <article v-for="appeal in appeals" :key="appeal.id" class="content-item">
          <div class="status-row"><span class="status-pill">{{ appealStatusLabels[appeal.appeal_status] }}</span><span>{{ typeLabels[appeal.content_type] }}</span></div>
          <h2 v-if="appeal.title">{{ appeal.title }}</h2><p>{{ appeal.body }}</p>
          <p><strong>申诉说明：</strong>{{ appeal.appeal_reason }}</p>
          <p v-if="appeal.result_reason"><strong>复核结果：</strong>{{ appeal.result_reason }}</p>
        </article>
        <el-empty v-if="!loading && appeals.length === 0" description="你还没有提交申诉" />
      </section>
    </section>
    <aside class="community-sidebar">
      <section class="sidebar-profile"><div class="profile-cover" /><div class="profile-avatar">{{ auth.user?.username?.slice(0, 1).toUpperCase() }}</div><h3>{{ auth.user?.username }}</h3><p>每一次分享，都值得被看见</p><button @click="showSection('create')">＋ 写点什么</button><div class="profile-links"><button @click="showSection('mine')">我的内容 →</button><button @click="showSection('appeals')">我的申诉 →</button></div></section>
      <section class="sidebar-guide"><span class="guide-label">COMMUNITY GUIDE</span><h3>一起守护这份热爱</h3><p><b>01</b> 保持友善，尊重不同声音</p><p><b>02</b> 分享真实，保护个人隐私</p><p><b>03</b> 认真交流，让灵感自由生长</p><div class="guide-bottom">一段文字，一个新的连接 ✧</div></section>
    </aside>
    </div>
  </main>
</template>

<style scoped>
.forum-shell{align-items:flex-start}.forum-card{max-width:980px}.forum-nav{display:flex;gap:8px;margin:22px 0;padding-bottom:14px;border-bottom:1px solid #e8edf5}.forum-nav button,.text-button{border:0;background:transparent;color:#5c6980;cursor:pointer;font:inherit}.forum-nav button{padding:9px 15px;border-radius:9px}.forum-nav button.active{color:#155eef;background:#edf4ff;font-weight:650}.content-list,.post-detail{display:grid;gap:14px}.content-item,.comment-card,.composer{border:1px solid #e4eaf2;border-radius:14px;padding:18px;background:#fff}.content-item h2{margin:7px 0;font-size:19px}.content-item p,.comment-card p{margin:7px 0 0;white-space:pre-wrap;line-height:1.65}.clickable{cursor:pointer;transition:.15s ease}.clickable:hover{transform:translateY(-1px);border-color:#9fbcf8}.featured{background:#f8faff}.item-meta{color:#7d899c;font-size:13px}.composer{display:grid;gap:12px}.composer h2{margin:0}.composer label{display:grid;gap:7px;font-weight:600}.composer input,.composer textarea,.reply-composer input,.appeal-box textarea{width:100%;box-sizing:border-box;border:1px solid #cad4e2;border-radius:10px;padding:11px 12px;font:inherit;color:#263247}.composer textarea{min-height:180px;resize:vertical}.composer.compact textarea{min-height:92px}.composer-actions,.status-row,.reply-composer{display:flex;align-items:center;justify-content:space-between;gap:12px}.composer-actions span{color:#8995a8;font-size:13px}.section-title{margin:12px 0 0}.reply-card{margin:12px 0 0 20px;padding:11px 14px;border-left:3px solid #c9d9fa;background:#f7f9fc}.reply-composer{margin-top:12px}.text-button{justify-self:start;color:#155eef;padding:2px 0}.notice{padding:10px 13px;border-radius:9px}.notice.error{color:#b42318;background:#fef3f2}.notice.success{color:#067647;background:#ecfdf3}.loading-text{text-align:center}.status-pill{padding:4px 9px;border-radius:999px;background:#eef2f7;font-size:13px}.status-pill[data-status='published']{color:#067647;background:#ecfdf3}.status-pill[data-status='rejected']{color:#b42318;background:#fef3f2}.status-pill[data-status='pending_manual_review']{color:#b54708;background:#fffaeb}.moderation-reason{color:#677489;font-size:14px}.appeal-box{display:grid;gap:10px;margin-top:14px}.appeal-box textarea{min-height:84px;resize:vertical}@media(max-width:680px){.forum-nav{overflow-x:auto}.reply-composer{align-items:stretch;flex-direction:column}}
</style>

