# Frontend Testing Patterns

React 19 和 Vue 3.5+ 的测试模式参考。

---

## 目录

1. [Vitest 配置](#vitest-配置)
2. [MSW API Mock 设置](#msw-api-mock-设置)
3. [React 测试模式](#react-测试模式)
4. [Vue 测试模式](#vue-测试模式)
5. [通用模式](#通用模式)

---

## Vitest 配置

### vite.config.ts（React）

```typescript
/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      exclude: ['src/test/**', '**/*.d.ts', 'src/main.tsx'],
    },
  },
})
```

### vite.config.ts（Vue）

```typescript
/// <reference types="vitest" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
})
```

### src/test/setup.ts

```typescript
import '@testing-library/jest-dom'
import { server } from './mocks/server'

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

---

## MSW API Mock 设置

### src/test/mocks/handlers.ts

```typescript
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('/api/users', () => {
    return HttpResponse.json([
      { id: 1, name: 'Alice', email: 'alice@example.com' },
    ])
  }),

  http.post('/api/users', async ({ request }) => {
    const body = await request.json() as { name: string; email: string }
    return HttpResponse.json({ id: 2, ...body }, { status: 201 })
  }),

  http.get('/api/users/:id', ({ params }) => {
    if (params.id === '999') {
      return HttpResponse.json({ message: 'Not found' }, { status: 404 })
    }
    return HttpResponse.json({ id: Number(params.id), name: 'Bob' })
  }),
]
```

### src/test/mocks/server.ts

```typescript
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)
```

### 在单个测试中覆盖 handler

```typescript
import { server } from '../test/mocks/server'
import { http, HttpResponse } from 'msw'

it('处理服务器错误', async () => {
  server.use(
    http.get('/api/users', () => {
      return HttpResponse.json({ message: 'Server Error' }, { status: 500 })
    })
  )
  // ... 测试错误状态
})
```

---

## React 测试模式

### 组件渲染测试

```typescript
import { render, screen } from '@testing-library/react'
import { UserCard } from './UserCard'

describe('UserCard', () => {
  const mockUser = { id: 1, name: 'Alice', email: 'alice@example.com' }

  it('应该渲染用户名和邮箱', () => {
    render(<UserCard user={mockUser} />)
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('alice@example.com')).toBeInTheDocument()
  })

  it('应该在 loading 时显示骨架屏', () => {
    render(<UserCard user={null} loading />)
    expect(screen.getByTestId('skeleton')).toBeInTheDocument()
    expect(screen.queryByText('Alice')).not.toBeInTheDocument()
  })

  it('应该在 user 为 null 时显示空状态', () => {
    render(<UserCard user={null} />)
    expect(screen.getByText(/暂无数据/i)).toBeInTheDocument()
  })
})
```

### 用户交互测试

```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginForm } from './LoginForm'

describe('LoginForm', () => {
  it('应该在提交时调用 onSubmit 并传入表单数据', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(<LoginForm onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText(/邮箱/i), 'test@example.com')
    await user.type(screen.getByLabelText(/密码/i), 'password123')
    await user.click(screen.getByRole('button', { name: /登录/i }))

    expect(onSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    })
  })

  it('应该在邮箱格式错误时显示错误信息', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSubmit={vi.fn()} />)

    await user.type(screen.getByLabelText(/邮箱/i), 'invalid-email')
    await user.click(screen.getByRole('button', { name: /登录/i }))

    expect(screen.getByText(/邮箱格式不正确/i)).toBeInTheDocument()
  })
})
```

### 异步数据加载测试

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { UserList } from './UserList'

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

describe('UserList', () => {
  it('应该加载并显示用户列表', async () => {
    renderWithQuery(<UserList />)

    // 先显示 loading
    expect(screen.getByText(/加载中/i)).toBeInTheDocument()

    // 等待数据加载完成
    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument()
    })
  })

  it('应该在请求失败时显示错误', async () => {
    server.use(
      http.get('/api/users', () =>
        HttpResponse.json({ message: 'Error' }, { status: 500 })
      )
    )

    renderWithQuery(<UserList />)

    await waitFor(() => {
      expect(screen.getByText(/加载失败/i)).toBeInTheDocument()
    })
  })
})
```

### Custom Hook 测试

```typescript
import { renderHook, act } from '@testing-library/react'
import { useCounter } from './useCounter'

describe('useCounter', () => {
  it('应该从初始值开始', () => {
    const { result } = renderHook(() => useCounter(10))
    expect(result.current.count).toBe(10)
  })

  it('应该在 increment 后增加计数', () => {
    const { result } = renderHook(() => useCounter(0))

    act(() => {
      result.current.increment()
    })

    expect(result.current.count).toBe(1)
  })
})
```

### 带 Context 的 Hook 测试

```typescript
import { renderHook } from '@testing-library/react'
import { AuthProvider } from '../contexts/AuthContext'
import { useAuth } from './useAuth'

function wrapper({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>
}

describe('useAuth', () => {
  it('应该在登录后设置用户信息', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    await act(async () => {
      await result.current.login('test@example.com', 'password')
    })

    expect(result.current.user).toEqual(
      expect.objectContaining({ email: 'test@example.com' })
    )
    expect(result.current.isAuthenticated).toBe(true)
  })
})
```

---

## Vue 测试模式

### 组件测试（Vue Test Utils）

```typescript
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import UserCard from './UserCard.vue'

describe('UserCard', () => {
  it('应该渲染用户名', () => {
    const wrapper = mount(UserCard, {
      props: { user: { id: 1, name: 'Alice', email: 'alice@example.com' } },
    })
    expect(wrapper.text()).toContain('Alice')
  })

  it('应该在点击删除按钮时 emit delete 事件', async () => {
    const wrapper = mount(UserCard, {
      props: { user: { id: 1, name: 'Alice', email: 'alice@example.com' } },
    })

    await wrapper.find('[data-testid="delete-btn"]').trigger('click')

    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')![0]).toEqual([1])
  })
})
```

### Composable 测试

```typescript
import { ref } from 'vue'
import { describe, it, expect } from 'vitest'
import { useCounter } from './useCounter'

describe('useCounter', () => {
  it('应该正确增减计数', () => {
    const { count, increment, decrement } = useCounter(5)

    increment()
    expect(count.value).toBe(6)

    decrement()
    expect(count.value).toBe(5)
  })
})
```

### 带 Pinia 的组件测试

```typescript
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach } from 'vitest'
import UserProfile from './UserProfile.vue'
import { useUserStore } from '../stores/user'

describe('UserProfile', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('应该显示 store 中的用户信息', () => {
    const store = useUserStore()
    store.user = { id: 1, name: 'Alice' }

    const wrapper = mount(UserProfile)
    expect(wrapper.text()).toContain('Alice')
  })
})
```

---

## 通用模式

### 快照测试（谨慎使用）

```typescript
// 只对稳定的 UI 组件使用快照，避免对频繁变化的组件使用
it('应该匹配快照', () => {
  const { container } = render(<Button variant="primary">提交</Button>)
  expect(container.firstChild).toMatchSnapshot()
})
```

### 测试工具函数

```typescript
// utils/format.test.ts
import { formatDate, formatCurrency } from './format'

describe('formatDate', () => {
  it('应该格式化为 YYYY-MM-DD', () => {
    expect(formatDate(new Date('2024-01-15'))).toBe('2024-01-15')
  })

  it('应该处理 null 输入', () => {
    expect(formatDate(null)).toBe('—')
  })
})
```

### E2E 测试（Playwright）

```typescript
// e2e/login.spec.ts
import { test, expect } from '@playwright/test'

test.describe('登录流程', () => {
  test('应该成功登录并跳转到首页', async ({ page }) => {
    await page.goto('/login')

    await page.getByLabel('邮箱').fill('test@example.com')
    await page.getByLabel('密码').fill('password123')
    await page.getByRole('button', { name: '登录' }).click()

    await expect(page).toHaveURL('/dashboard')
    await expect(page.getByText('欢迎回来')).toBeVisible()
  })

  test('应该在密码错误时显示错误信息', async ({ page }) => {
    await page.goto('/login')

    await page.getByLabel('邮箱').fill('test@example.com')
    await page.getByLabel('密码').fill('wrongpassword')
    await page.getByRole('button', { name: '登录' }).click()

    await expect(page.getByText('邮箱或密码错误')).toBeVisible()
    await expect(page).toHaveURL('/login')
  })
})
```

### playwright.config.ts

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
})
```
