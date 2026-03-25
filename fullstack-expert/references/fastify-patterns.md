# Fastify 后端开发模式

## 目录

1. [项目初始化](#1-项目初始化)
2. [项目结构](#2-项目结构)
3. [Schema 与类型](#3-schema-与类型)
4. [路由设计](#4-路由设计)
5. [统一响应格式](#5-统一响应格式)
6. [认证（JWT）](#6-认证jwt)
7. [数据库（Prisma）](#7-数据库prisma)
8. [错误处理](#8-错误处理)

---

## 1. 项目初始化

```bash
mkdir my-api && cd my-api
pnpm init
pnpm add fastify @fastify/cors @fastify/jwt @fastify/swagger @fastify/swagger-ui
pnpm add zod fastify-zod  # 或使用 @fastify/type-provider-typebox
pnpm add prisma @prisma/client
pnpm add -D typescript tsx @types/node

# 初始化 TypeScript
npx tsc --init

# 初始化 Prisma
npx prisma init
```

`tsconfig.json` 关键配置：
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "outDir": "dist"
  }
}
```

---

## 2. 项目结构

```
src/
├── app.ts               # Fastify 实例、插件注册
├── server.ts            # 启动入口
├── plugins/
│   ├── cors.ts
│   ├── jwt.ts
│   └── swagger.ts
├── modules/             # 按业务模块（路由 + Schema + Service 放一起）
│   └── users/
│       ├── users.route.ts
│       ├── users.schema.ts
│       ├── users.service.ts
│       └── index.ts
├── lib/
│   ├── prisma.ts        # Prisma 客户端单例
│   └── response.ts      # 统一响应工具
└── types/
    └── index.ts         # 全局类型扩展
```

---

## 3. Schema 与类型

使用 Zod 定义 Schema，同时作为运行时验证和 TypeScript 类型来源：

```typescript
// modules/users/users.schema.ts
import { z } from 'zod'

export const UserCreateSchema = z.object({
  email: z.string().email(),
  fullName: z.string().min(1).max(100),
  password: z.string().min(6),
})

export const UserResponseSchema = z.object({
  id: z.number(),
  email: z.string(),
  fullName: z.string(),
  isActive: z.boolean(),
  createdAt: z.string().datetime(),
})

export const UserUpdateSchema = UserCreateSchema.partial().omit({ password: true })

export type UserCreate = z.infer<typeof UserCreateSchema>
export type UserResponse = z.infer<typeof UserResponseSchema>
export type UserUpdate = z.infer<typeof UserUpdateSchema>
```

---

## 4. 路由设计

```typescript
// modules/users/users.route.ts
import type { FastifyPluginAsync } from 'fastify'
import { UserCreateSchema, UserResponseSchema } from './users.schema'
import { userService } from './users.service'
import { ok, fail } from '@/lib/response'
import { ResponseCode } from '@/lib/response'

const usersRoute: FastifyPluginAsync = async (fastify) => {
  // 列表（分页）
  fastify.get('/', {
    schema: {
      querystring: { type: 'object', properties: { page: { type: 'integer', default: 1 }, size: { type: 'integer', default: 20 } } },
    },
  }, async (request, reply) => {
    const { page, size } = request.query as { page: number; size: number }
    const result = await userService.listUsers(page, size)
    return reply.send(ok(result))
  })

  // 详情
  fastify.get<{ Params: { id: string } }>('/:id', async (request, reply) => {
    const user = await userService.getUser(Number(request.params.id))
    if (!user) return reply.status(404).send(fail(ResponseCode.NOT_FOUND, '用户不存在'))
    return reply.send(ok(user))
  })

  // 创建
  fastify.post('/', {
    schema: { body: UserCreateSchema },
  }, async (request, reply) => {
    const user = await userService.createUser(request.body as any)
    return reply.status(201).send(ok(user, '创建成功'))
  })

  // 更新
  fastify.put<{ Params: { id: string } }>('/:id', async (request, reply) => {
    const user = await userService.updateUser(Number(request.params.id), request.body as any)
    return reply.send(ok(user, '更新成功'))
  })

  // 删除
  fastify.delete<{ Params: { id: string } }>('/:id', async (request, reply) => {
    await userService.deleteUser(Number(request.params.id))
    return reply.send(ok(null, '删除成功'))
  })
}

export default usersRoute
```

---

## 5. 统一响应格式

```typescript
// lib/response.ts
export enum ResponseCode {
  SUCCESS = 0,
  PARAM_ERROR = 1001,
  UNAUTHORIZED = 1002,
  FORBIDDEN = 1003,
  NOT_FOUND = 1004,
  CONFLICT = 1005,
  BUSINESS_ERROR = 2000,
  INTERNAL_ERROR = 5000,
}

export interface ApiResponse<T = null> {
  code: number
  message: string
  data: T
}

export function ok<T>(data: T, message = 'success'): ApiResponse<T> {
  return { code: ResponseCode.SUCCESS, message, data }
}

export function fail(code: ResponseCode, message: string): ApiResponse<null> {
  return { code, message, data: null }
}
```

---

## 6. 认证（JWT）

```typescript
// plugins/jwt.ts
import fp from 'fastify-plugin'
import fastifyJwt from '@fastify/jwt'

export default fp(async (fastify) => {
  fastify.register(fastifyJwt, {
    secret: process.env.JWT_SECRET ?? 'change-me',
  })

  fastify.decorate('authenticate', async (request: any, reply: any) => {
    try {
      await request.jwtVerify()
    } catch {
      reply.status(401).send(fail(ResponseCode.UNAUTHORIZED, '请先登录'))
    }
  })
})
```

```typescript
// 在路由中使用
fastify.get('/me', {
  onRequest: [fastify.authenticate],
}, async (request) => {
  const payload = request.user as { sub: number }
  const user = await userService.getUser(payload.sub)
  return ok(user)
})
```

---

## 7. 数据库（Prisma）

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  fullName  String
  password  String
  isActive  Boolean  @default(true)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

```typescript
// lib/prisma.ts
import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient }

export const prisma = globalForPrisma.prisma ?? new PrismaClient()

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma
```

```typescript
// modules/users/users.service.ts
import { prisma } from '@/lib/prisma'
import type { UserCreate, UserUpdate } from './users.schema'
import bcrypt from 'bcryptjs'

export const userService = {
  async listUsers(page: number, size: number) {
    const [items, total] = await Promise.all([
      prisma.user.findMany({ skip: (page - 1) * size, take: size, orderBy: { createdAt: 'desc' } }),
      prisma.user.count(),
    ])
    const pages = Math.ceil(total / size)
    return { items, total, page, size, pages, hasNext: page < pages, hasPrev: page > 1 }
  },

  async getUser(id: number) {
    return prisma.user.findUnique({ where: { id } })
  },

  async createUser(data: UserCreate) {
    const existing = await prisma.user.findUnique({ where: { email: data.email } })
    if (existing) throw { code: 1005, message: '邮箱已被注册', status: 409 }
    const hashed = await bcrypt.hash(data.password, 10)
    return prisma.user.create({ data: { ...data, password: hashed } })
  },

  async updateUser(id: number, data: UserUpdate) {
    return prisma.user.update({ where: { id }, data })
  },

  async deleteUser(id: number) {
    return prisma.user.delete({ where: { id } })
  },
}
```

---

## 8. 错误处理

```typescript
// app.ts
fastify.setErrorHandler((error: any, request, reply) => {
  // 业务异常（自定义 code/status）
  if (error.code && error.message && error.status) {
    return reply.status(error.status).send(fail(error.code, error.message))
  }

  // Zod / Fastify 参数校验错误
  if (error.validation) {
    return reply.status(422).send({
      code: ResponseCode.PARAM_ERROR,
      message: '参数校验失败',
      data: null,
      errors: error.validation.map((e: any) => ({
        field: e.instancePath.replace('/', ''),
        message: e.message,
      })),
    })
  }

  // 未知错误
  fastify.log.error(error)
  return reply.status(500).send(fail(ResponseCode.INTERNAL_ERROR, '服务器内部错误'))
})
```

---

## 与前端类型同步

Fastify + `@fastify/swagger` 自动生成 OpenAPI 文档，前端用 `openapi-typescript` 生成类型：

```typescript
// plugins/swagger.ts
import fp from 'fastify-plugin'
import swagger from '@fastify/swagger'
import swaggerUi from '@fastify/swagger-ui'

export default fp(async (fastify) => {
  await fastify.register(swagger, {
    openapi: { info: { title: 'My API', version: '1.0.0' } },
  })
  await fastify.register(swaggerUi, { routePrefix: '/docs' })
})
```

```bash
# 启动后生成前端类型
pnpm openapi-typescript http://localhost:3000/docs/json -o ../frontend/src/types/api.ts
```
