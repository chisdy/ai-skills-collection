# React 19 开发模式

## 目录

1. [项目初始化](#1-项目初始化)
2. [状态管理](#2-状态管理)
3. [数据请求](#3-数据请求)
4. [表单处理](#4-表单处理)
5. [路由](#5-路由)
6. [React 19 新特性](#6-react-19-新特性)

---

## 1. 项目初始化

```bash
pnpm create vite my-app --template react-ts
cd my-app

# Tailwind CSS V4
pnpm add tailwindcss @tailwindcss/vite

# 状态 & 请求
pnpm add zustand @tanstack/react-query axios

# 表单 & 验证
pnpm add react-hook-form zod @hookform/resolvers

# 路由
pnpm add react-router-dom

# 图标（按选型）
pnpm add lucide-react          # Lucide
pnpm add @iconify/react        # Iconify

# UI 库（按选型）
# shadcn/ui: pnpm dlx shadcn@latest init
# Ant Design: pnpm add antd
# MUI: pnpm add @mui/material @emotion/react @emotion/styled
```

`vite.config.ts`：
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': '/src' } },
})
```

`src/index.css`：
```css
@import "tailwindcss";
```

---

## 2. 状态管理（Zustand）

```typescript
// stores/authStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  user: UserResponse | null
  setAuth: (token: string, user: UserResponse) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      clearAuth: () => set({ token: null, user: null }),
    }),
    { name: 'auth', partialize: (s) => ({ token: s.token, user: s.user }) }
  )
)
```

---

## 3. 数据请求（TanStack Query）

```typescript
// lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 1, refetchOnWindowFocus: false },
  },
})
```

```typescript
// App.tsx
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* routes */}
    </QueryClientProvider>
  )
}
```

Hook 模式参考 [api-patterns.md](api-patterns.md) 中的 TanStack Query 封装示例。

---

## 4. 表单处理（React Hook Form + Zod）

```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const schema = z.object({
  email: z.string().email('邮箱格式不正确'),
  password: z.string().min(6, '密码至少 6 位'),
})
type FormData = z.infer<typeof schema>

export function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  return (
    <form onSubmit={handleSubmit((data) => console.log(data))}>
      <input {...register('email')} />
      {errors.email && <p>{errors.email.message}</p>}
    </form>
  )
}
```

---

## 5. 路由（React Router v7）

```typescript
// router.tsx
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    path: '/',
    element: <ProtectedRoute><Layout /></ProtectedRoute>,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
```

---

## 6. React 19 新特性

### ref 直接作为 prop（无需 forwardRef）

```typescript
// React 19 之前需要 forwardRef，现在直接用
function Input({ ref, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { ref?: React.Ref<HTMLInputElement> }) {
  return <input ref={ref} {...props} />
}
```

### use() 处理异步数据

```typescript
import { use, Suspense } from 'react'

function UserProfile({ userPromise }: { userPromise: Promise<UserResponse> }) {
  const user = use(userPromise)  // 自动 suspend
  return <div>{user.fullName}</div>
}

// 使用时包裹 Suspense
<Suspense fallback={<Skeleton />}>
  <UserProfile userPromise={fetchUser(id)} />
</Suspense>
```

### useActionState（表单 Action）

```typescript
import { useActionState } from 'react'

async function loginAction(prevState: unknown, formData: FormData) {
  const email = formData.get('email') as string
  // 调用 API...
  return { error: '登录失败' }
}

function LoginForm() {
  const [state, action, isPending] = useActionState(loginAction, null)
  return (
    <form action={action}>
      <input name="email" />
      {state?.error && <p>{state.error}</p>}
      <button disabled={isPending}>登录</button>
    </form>
  )
}
```

---

## 目录结构

```
src/
├── app/                # 路由、Provider 配置
├── components/         # 通用 UI 组件
│   └── ui/             # shadcn/ui 或基础组件
├── features/           # 按业务模块
│   └── {feature}/
│       ├── api/        # API 调用函数
│       ├── hooks/      # TanStack Query hooks
│       ├── components/ # 功能组件
│       └── types.ts    # 模块类型
├── lib/
│   ├── api.ts          # Axios 实例
│   └── queryClient.ts
├── stores/             # Zustand stores
└── types/              # 全局类型 / openapi-typescript 生成
```
