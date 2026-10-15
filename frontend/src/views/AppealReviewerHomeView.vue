<script setup lang="ts">
import axios from 'axios'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { decideAppealTask, getAppealTask, listAppealTasks } from '../api/appeals'
import { useAuthStore } from '../stores/auth'
import type { RiskLevel } from '../types/content'
import type { AppealItem, RiskCategory } from '../types/review'

const categories: Array<{ value: RiskCategory; label: string }> = [
  { value: 'normal', label: '正常内容' },
  { value: 'sexual', label: '色情低俗' },
  { value: 'violence', label: '暴力或危险行为' },
  { value: 'illegal_fraud', label: '违法、诈骗或违禁交易' },
  { value: 'hate_discrimination', label: '仇恨或歧视' },
  { value: 'harassment', label: '辱骂、骚扰或人身攻击' },
  { value: 'privacy', label: '隐私泄露' },
  { value: 'spam_advertising', label: '广告、引流或垃圾内容' },
]
const levels: RiskLevel[] = ['L0', 'L1', 'L2', 'L3', 'L4']
const auth = useAuthStore()
const router = useRouter()
const tasks = ref<AppealItem[]>([])
const selected = ref<AppealItem | null>(null)
const finalCategory = ref<RiskCategory>('normal')
const finalLevel = ref<RiskLevel>('L2')
const resultReason = ref('')
const loading = ref(false)
const message = ref('')

function errorText(error: unknown): string {
  return axios.isAxiosError(error)
    ? ((error.response?.data as { detail?: string } | undefined)?.detail ?? '操作失败')
    : '操作失败'
}

async function loadTasks(): Promise<void> {
  loading.value = true
  try { tasks.value = await listAppealTasks() }
  catch (error) { message.value = errorText(error) }
  finally { loading.value = false }
}

async function openTask(id: number): Promise<void> {
  loading.value = true
  try {
    selected.value = await getAppealTask(id)
    finalCategory.value = selected.value.original_moderation.final_category as RiskCategory
    finalLevel.value = selected.value.original_moderation.final_level
    resultReason.value = ''
    message.value = ''
  } catch (error) { message.value = errorText(error) }
  finally { loading.value = false }
}

async function decide(decision: 'approved' | 'rejected'): Promise<void> {
  if (!selected.value || !resultReason.value.trim()) return
  loading.value = true
  try {
    await decideAppealTask(selected.value.id, {
      final_category: finalCategory.value,
      final_level: finalLevel.value,
      decision,
      result_reason: resultReason.value.trim(),
    })
    message.value = decision === 'approved' ? '复核完成，申诉已通过。' : '复核完成，申诉已驳回。'
    selected.value = null
    await loadTasks()
  } catch (error) { message.value = errorText(error) }
  finally { loading.value = false }
}

function logout(): void { auth.logout(); void router.replace('/login') }
onMounted(loadTasks)
</script>

<template>
  <main class="shell reviewer-shell">
    <section class="page-card reviewer-card">
      <header class="page-header"><div><p class="muted">{{ auth.user?.username }} · 申诉复核员</p><h1>待复核申诉</h1></div><el-button @click="logout">退出登录</el-button></header>
      <p v-if="message" class="review-message">{{ message }}</p><p v-if="loading" class="muted">正在处理…</p>
      <div v-if="!selected" class="task-list">
        <button v-for="task in tasks" :key="task.id" class="task-row" @click="openTask(task.id)"><span><strong>#{{ task.id }} {{ task.title || task.body.slice(0, 36) }}</strong><small>{{ task.author }} · {{ task.content_type }}</small></span><span>查看复核 →</span></button>
        <el-empty v-if="!loading && tasks.length === 0" description="暂无待复核申诉" />
      </div>
      <section v-else class="review-detail">
        <button class="back-button" @click="selected = null">← 返回申诉列表</button>
        <div class="review-block"><h2>{{ selected.title || '评论/回复内容' }}</h2><p>{{ selected.body }}</p><small>作者：{{ selected.author }}</small></div>
        <div v-if="selected.context" class="review-block context"><h3>最小必要上下文</h3><p>{{ selected.context }}</p></div>
        <div class="review-block appeal"><h3>用户申诉说明</h3><p>{{ selected.appeal_reason }}</p></div>
        <div class="review-block"><h3>原审核结果</h3><p>{{ selected.original_moderation.final_category }} · {{ selected.original_moderation.final_level }}</p><p>{{ selected.original_moderation.reason }}</p></div>
        <div class="decision-panel">
          <label>最终类别<select v-model="finalCategory"><option v-for="item in categories" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
          <label>最终等级<select v-model="finalLevel"><option v-for="level in levels" :key="level">{{ level }}</option></select></label>
          <label>结果说明<textarea v-model="resultReason" maxlength="300" placeholder="填写面向用户的复核结果说明" /></label>
          <p v-if="finalLevel === 'L2'" class="warning">L2不能作为申诉终审等级。</p>
          <div class="decision-actions"><el-button type="primary" :disabled="loading || !resultReason.trim() || !['L0','L1'].includes(finalLevel)" @click="decide('approved')">通过申诉并发布</el-button><el-button type="danger" :disabled="loading || !resultReason.trim() || !['L3','L4'].includes(finalLevel)" @click="decide('rejected')">驳回申诉</el-button></div>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
.reviewer-shell{align-items:flex-start}.reviewer-card{max-width:980px}.task-list,.review-detail{display:grid;gap:12px;margin-top:20px}.task-row{display:flex;justify-content:space-between;align-items:center;text-align:left;border:1px solid #e2e8f0;background:#fff;border-radius:12px;padding:16px;cursor:pointer;color:#344054}.task-row:hover{border-color:#8aaff7}.task-row small{display:block;color:#7d899c;margin-top:5px}.review-block,.decision-panel{border:1px solid #e3e9f2;border-radius:12px;padding:17px}.review-block h2,.review-block h3{margin-top:0}.review-block p{white-space:pre-wrap;line-height:1.65}.context{background:#f7f9fc}.appeal{background:#fffaeb}.decision-panel{display:grid;gap:14px}.decision-panel label{display:grid;gap:7px;font-weight:600}.decision-panel select,.decision-panel textarea{padding:10px;border:1px solid #cbd5e1;border-radius:9px;background:#fff;font:inherit}.decision-panel textarea{min-height:80px;resize:vertical}.decision-actions{display:flex;gap:10px}.back-button{justify-self:start;border:0;background:transparent;color:#155eef;cursor:pointer}.warning{color:#b54708}.review-message{padding:10px 13px;background:#eff6ff;color:#175cd3;border-radius:9px}
</style>
