import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import type { UserRole } from '../types/auth'
import AppealReviewerHomeView from '../views/AppealReviewerHomeView.vue'
import LoginView from '../views/LoginView.vue'
import ModeratorHomeView from '../views/ModeratorHomeView.vue'
import UserHomeView from '../views/UserHomeView.vue'
import { roleHomePath } from './role-home'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: UserRole[]
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', component: LoginView },
    {
      path: '/forum',
      component: UserHomeView,
      meta: { requiresAuth: true, roles: ['user'] },
    },
    {
      path: '/moderation',
      component: ModeratorHomeView,
      meta: { requiresAuth: true, roles: ['content_reviewer'] },
    },
    {
      path: '/appeals',
      component: AppealReviewerHomeView,
      meta: { requiresAuth: true, roles: ['appeal_reviewer'] },
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.roles && auth.user && !to.meta.roles.includes(auth.user.role)) {
    return roleHomePath(auth.user.role)
  }
  if (to.path === '/login' && auth.user) {
    return roleHomePath(auth.user.role)
  }
  return true
})

export default router

