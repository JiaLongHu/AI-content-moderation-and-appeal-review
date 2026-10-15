<script setup lang="ts">
import axios from 'axios'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { roleHomePath } from '../router/role-home'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const errorMessage = ref('')
const form = reactive({
  username: '',
  password: '',
})

async function submit(): Promise<void> {
  errorMessage.value = ''
  if (!form.username || !form.password) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  try {
    const user = await auth.login(form)
    await router.replace(roleHomePath(user.role))
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      errorMessage.value = String(error.response.data.detail)
    } else {
      errorMessage.value = '登录失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-card">
      <div class="brand-mark">AI</div>
      <p class="eyebrow">TEXT SAFETY WORKSPACE</p>
      <h1>文字内容审核系统</h1>
      <p class="subtitle">使用预置账号登录，进入对应的社区或审核工作区。</p>

      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            autocomplete="current-password"
            placeholder="请输入密码"
            show-password
            type="password"
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-alert v-if="errorMessage" :closable="false" :title="errorMessage" type="error" />
        <el-button class="login-button" :loading="loading" type="primary" @click="submit">
          登录
        </el-button>
      </el-form>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 12% 18%, rgb(37 99 235 / 12%), transparent 28%),
    radial-gradient(circle at 88% 80%, rgb(14 165 233 / 10%), transparent 30%),
    #f4f7fb;
}

.login-card {
  width: min(420px, 100%);
  padding: 38px;
  background: rgb(255 255 255 / 96%);
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  box-shadow: 0 22px 60px rgb(15 23 42 / 12%);
}

.brand-mark {
  display: grid;
  width: 46px;
  height: 46px;
  color: #ffffff;
  font-weight: 800;
  background: #2563eb;
  border-radius: 13px;
  place-items: center;
}

.eyebrow {
  margin: 22px 0 8px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

h1 {
  margin: 0;
  color: #0f172a;
  font-size: 30px;
}

.subtitle {
  margin: 12px 0 28px;
  color: #64748b;
  line-height: 1.7;
}

.login-button {
  width: 100%;
  margin-top: 20px;
}
</style>

