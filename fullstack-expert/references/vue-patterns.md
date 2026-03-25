# Vue 3.5+ 开发模式

## 目录

1. [项目初始化](#1-项目初始化)
2. [状态管理（Pinia）](#2-状态管理pinia)
3. [数据请求（TanStack Query for Vue）](#3-数据请求tanstack-query-for-vue)
4. [表单处理](#4-表单处理)
5. [路由（Vue Router 4）](#5-路由vue-router-4)
6. [Vue 3.5 新特性](#6-vue-35-新特性)

---

## 1. 项目初始化

```bash
pnpm create vue@latest my-app
# 选择：TypeScript ✓ | Vue Router ✓ | Pinia ✓ | ESLint ✓

cd my-app

# Tailwind CSS V4
pnpm add tailwindcss @tailwindcss/vite

# 数据请求
pnpm add @tanstack/vue-query axios

# 表单 & 验证
pnpm add vee-validate zod @vee-validate/zod

# 图标（按选型）
pnpm add @iconify/vue           # Iconify
pnpm add lucide-vue-next        # Lucide

# UI 库（按选型）
# Element Plus:    pnpm add element-plus
# Naive UI:        pnpm add naive-ui
# Ant Design Vue:  pnpm add ant-design-vue
# shadcn-vue:      pnpm dlx shadcn-vue@latest init
```

`vite.config.ts`：
```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: { alias: { '@': '/src' } },
})
```

`src/assets/main.css`：
```css
@import "tailwindcss";
```

---

## 2. 状态管理（Pinia）

```typescript
// stores/auth.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserResponse | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  function setAuth(newToken: string, newUser: UserResponse) {
    token.value = newToken
    user.value = newUser
    localStorage.setItem('token', newToken)
  }

  function clearAuth() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isAuthenticated, setAuth, clearAuth }
}, { persist: true })  // 需要 pinia-plugin-persistedstate
```

---

## 3. 数据请求（TanStack Query for Vue）

```typescript
// main.ts
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 1, refetchOnWindowFocus: false },
  },
})

app.use(VueQueryPlugin, { queryClient })
```

```typescript
// features/users/hooks/useUsers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { api, unwrap } from '@/lib/api'
import type { PageData } from '@/types/api'
import type { UserResponse, UserCreate } from '@/types/user'

export function useUsers(page: Ref<number>, size = 20) {
  return useQuery({
    queryKey: ['users', page, size],
    queryFn: () => api.get('/users/', { params: { page: page.value, size } }).then(unwrap<PageData<UserResponse>>),
  })
}

export function useCreateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: UserCreate) => api.post('/users/', data).then(unwrap<UserResponse>),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })
}
```

---

## 4. 表单处理（VeeValidate + Zod）

```vue
<script setup lang="ts">
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'

const schema = toTypedSchema(z.object({
  email: z.string().email('邮箱格式不正确'),
  password: z.string().min(6, '密码至少 6 位'),
}))

const { defineField, handleSubmit, errors } = useForm({ validationSchema: schema })
const [email, emailAttrs] = defineField('email')
const [password, passwordAttrs] = defineField('password')

const onSubmit = handleSubmit((values) => {
  console.log(values)
})
</script>

<template>
  <form @submit="onSubmit">
    <input v-bind="emailAttrs" v-model="email" />
    <p v-if="errors.email">{{ errors.email }}</p>
    <button type="submit">登录</button>
  </form>
</template>
```

---

## 5. 路由（Vue Router 4）

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/LoginView.vue') },
    {
      path: '/',
      component: () => import('@/layouts/DefaultLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', component: () => import('@/views/DashboardView.vue') },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return '/login'
  }
})

export default router
```

---

## 6. Vue 3.5 新特性

### useTemplateRef()（替代 ref 获取 DOM）

```vue
<script setup lang="ts">
import { useTemplateRef, onMounted } from 'vue'

const inputRef = useTemplateRef<HTMLInputElement>('myInput')

onMounted(() => inputRef.value?.focus())
</script>

<template>
  <input ref="myInput" />
</template>
```

### Props 解构默认保持响应性（无需 toRefs）

```typescript
// Vue 3.5 之前需要 toRefs(props)，现在直接解构
const { title, count = 0 } = defineProps<{
  title: string
  count?: number
}>()
// title 和 count 自动保持响应性
```

### useId()（生成唯一 ID）

```vue
<script setup lang="ts">
import { useId } from 'vue'
const id = useId()
</script>

<template>
  <label :for="id">邮箱</label>
  <input :id="id" type="email" />
</template>
```

### 响应式 Props 解构 + 默认值

```typescript
const { items = [], loading = false } = defineProps<{
  items?: string[]
  loading?: boolean
}>()
```

---

## 目录结构

```
src/
├── components/         # 通用 UI 组件
│   └── ui/             # 基础组件（按钮、输入框等）
├── composables/        # 通用 Composable（useDebounce 等）
├── features/           # 按业务模块
│   └── {feature}/
│       ├── api/        # API 调用函数
│       ├── hooks/      # TanStack Query composables
│       ├── components/ # 功能组件
│       └── types.ts
├── layouts/            # 布局组件
├── lib/
│   ├── api.ts          # Axios 实例
│   └── queryClient.ts
├── router/             # Vue Router 配置
├── stores/             # Pinia stores
├── types/              # 全局类型 / openapi-typescript 生成
└── views/              # 页面级组件
```
