# API 设计规范

## 目录

1. [统一响应体格式](#1-统一响应体格式)
2. [响应类型规范](#2-响应类型规范)
3. [错误码规范](#3-错误码规范)
4. [异常处理](#4-异常处理)
5. [分页规范](#5-分页规范)
6. [前端集成](#6-前端集成)
7. [性能优化](#7-性能优化)

---

## 1. 统一响应体格式

所有 API 响应必须遵循统一结构，便于前端统一处理。

### 后端基础模型

```python
# schemas/response.py
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any
from enum import IntEnum

T = TypeVar('T')

class ResponseCode(IntEnum):
    """业务状态码（与 HTTP 状态码独立）"""
    SUCCESS = 0
    # 通用错误 1xxx
    PARAM_ERROR = 1001        # 参数校验失败
    UNAUTHORIZED = 1002       # 未登录 / Token 无效
    FORBIDDEN = 1003          # 无权限
    NOT_FOUND = 1004          # 资源不存在
    CONFLICT = 1005           # 资源冲突（如邮箱已注册）
    # 业务错误 2xxx
    BUSINESS_ERROR = 2000     # 通用业务错误
    # 系统错误 5xxx
    INTERNAL_ERROR = 5000     # 服务器内部错误

class ApiResponse(BaseModel, Generic[T]):
    code: int = ResponseCode.SUCCESS
    message: str = "success"
    data: Optional[T] = None

class ApiError(BaseModel):
    code: int
    message: str
    data: None = None
    errors: Optional[list[dict]] = None  # 字段级错误详情
```

### 响应示例

**成功**：
```json
{
  "code": 0,
  "message": "success",
  "data": { "id": 1, "email": "user@example.com" }
}
```

**失败**：
```json
{
  "code": 1001,
  "message": "参数校验失败",
  "data": null,
  "errors": [
    { "field": "email", "message": "邮箱格式不正确" }
  ]
}
```

### 快捷构造函数

```python
# schemas/response.py（续）
class ApiResponse(BaseModel, Generic[T]):
    code: int = ResponseCode.SUCCESS
    message: str = "success"
    data: Optional[T] = None

    @classmethod
    def ok(cls, data: T = None, message: str = "success") -> "ApiResponse[T]":
        return cls(code=ResponseCode.SUCCESS, message=message, data=data)

    @classmethod
    def fail(cls, code: int, message: str, errors: list[dict] | None = None) -> "ApiResponse":
        return cls(code=code, message=message, data=None)
```

---

## 2. 响应类型规范

### 2.1 详情类（单条资源）

```python
@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise NotFoundException("用户不存在")
    return ApiResponse.ok(data=user)
```

响应：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "fullName": "张三",
    "isActive": true,
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

### 2.2 列表类（分页）

```python
# schemas/response.py
class PageData(BaseModel, Generic[T]):
    """分页数据容器"""
    items: list[T]
    total: int        # 总记录数
    page: int         # 当前页码（从 1 开始）
    size: int         # 每页大小
    pages: int        # 总页数
    has_next: bool    # 是否有下一页
    has_prev: bool    # 是否有上一页
```

```python
@router.get("/", response_model=ApiResponse[PageData[UserResponse]])
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    result = await user_service.list_users(db, page=page, size=size)
    return ApiResponse.ok(data=result)
```

响应：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "size": 20,
    "pages": 5,
    "hasNext": true,
    "hasPrev": false
  }
}
```

### 2.3 列表类（无分页，简单枚举）

适用于下拉选项、标签列表等数据量有限的场景：

```python
@router.get("/options", response_model=ApiResponse[list[UserOption]])
async def get_user_options(db: AsyncSession = Depends(get_db)):
    options = await user_service.get_all_options(db)
    return ApiResponse.ok(data=options)
```

响应：
```json
{
  "code": 0,
  "message": "success",
  "data": [
    { "id": 1, "label": "张三" },
    { "id": 2, "label": "李四" }
  ]
}
```

### 2.4 创建类

HTTP 状态码 `201`，返回创建后的完整资源：

```python
@router.post("/", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await user_service.create_user(db, user_in)
    return ApiResponse.ok(data=user, message="创建成功")
```

### 2.5 更新类

HTTP 状态码 `200`，返回更新后的完整资源：

```python
@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
async def update_user(user_id: int, user_in: UserUpdate, db: AsyncSession = Depends(get_db)):
    user = await user_service.update_user(db, user_id, user_in)
    return ApiResponse.ok(data=user, message="更新成功")
```

### 2.6 删除类

HTTP 状态码 `200`，data 为 null：

```python
@router.delete("/{user_id}", response_model=ApiResponse[None])
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    await user_service.delete_user(db, user_id)
    return ApiResponse.ok(message="删除成功")
```

### 2.7 操作类（无资源返回）

适用于发送验证码、触发任务等操作：

```python
@router.post("/send-verification", response_model=ApiResponse[None])
async def send_verification(email: str):
    await email_service.send_verification(email)
    return ApiResponse.ok(message="验证码已发送")
```

### 2.8 批量操作类

```python
class BatchResult(BaseModel):
    success_count: int
    fail_count: int
    failed_ids: list[int]

@router.post("/batch-delete", response_model=ApiResponse[BatchResult])
async def batch_delete(ids: list[int], db: AsyncSession = Depends(get_db)):
    result = await user_service.batch_delete(db, ids)
    return ApiResponse.ok(data=result)
```

---

## 3. 错误码规范

| 业务码 | 含义 | HTTP 状态码 |
|--------|------|-------------|
| 0 | 成功 | 200 / 201 |
| 1001 | 参数校验失败 | 422 |
| 1002 | 未认证（Token 无效/过期） | 401 |
| 1003 | 无权限 | 403 |
| 1004 | 资源不存在 | 404 |
| 1005 | 资源冲突 | 409 |
| 2000 | 通用业务错误 | 400 |
| 2001 | 账号已被禁用 | 400 |
| 2002 | 操作频率限制 | 429 |
| 5000 | 服务器内部错误 | 500 |

> 原则：HTTP 状态码表达传输层语义，业务码表达应用层语义。前端统一读 `code` 字段判断业务结果。

---

## 4. 异常处理

### 自定义异常体系

```python
# core/exceptions.py
class AppException(Exception):
    def __init__(self, code: int, message: str, http_status: int = 400):
        self.code = code
        self.message = message
        self.http_status = http_status

class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(ResponseCode.NOT_FOUND, message, 404)

class UnauthorizedException(AppException):
    def __init__(self, message: str = "请先登录"):
        super().__init__(ResponseCode.UNAUTHORIZED, message, 401)

class ForbiddenException(AppException):
    def __init__(self, message: str = "无操作权限"):
        super().__init__(ResponseCode.FORBIDDEN, message, 403)

class ConflictException(AppException):
    def __init__(self, message: str = "资源已存在"):
        super().__init__(ResponseCode.CONFLICT, message, 409)

class BusinessException(AppException):
    def __init__(self, message: str, code: int = ResponseCode.BUSINESS_ERROR):
        super().__init__(code, message, 400)
```

### 全局异常处理器

```python
# main.py
from fastapi.exceptions import RequestValidationError

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.code, "message": exc.message, "data": None}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(loc) for loc in e["loc"][1:]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "code": ResponseCode.PARAM_ERROR,
            "message": "参数校验失败",
            "data": None,
            "errors": errors
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # 生产环境不暴露内部错误详情
    return JSONResponse(
        status_code=500,
        content={"code": ResponseCode.INTERNAL_ERROR, "message": "服务器内部错误", "data": None}
    )
```

---

## 5. 分页规范

### 分页参数依赖

```python
# api/v1/deps.py
from fastapi import Query
from dataclasses import dataclass

@dataclass
class PaginationDep:
    page: int = Query(1, ge=1, description="页码，从 1 开始")
    size: int = Query(20, ge=1, le=100, description="每页条数")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
```

### 分页查询工具

```python
# crud/base.py
import math
from sqlalchemy import select, func

async def paginate(
    db: AsyncSession,
    query,
    page: int,
    size: int,
    response_schema
) -> PageData:
    # 总数
    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    # 数据
    result = await db.execute(query.offset((page - 1) * size).limit(size))
    items = result.scalars().all()

    pages = math.ceil(total / size) if total > 0 else 0
    return PageData(
        items=[response_schema.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )
```

---

## 6. 前端集成

### TypeScript 类型定义

```typescript
// types/api.ts
export interface ApiResponse<T = null> {
  code: number;
  message: string;
  data: T;
}

export interface PageData<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface FieldError {
  field: string;
  message: string;
}

export interface ApiErrorResponse extends ApiResponse<null> {
  errors?: FieldError[];
}

// 业务码常量
export const ResponseCode = {
  SUCCESS: 0,
  PARAM_ERROR: 1001,
  UNAUTHORIZED: 1002,
  FORBIDDEN: 1003,
  NOT_FOUND: 1004,
  CONFLICT: 1005,
} as const;
```

### Axios 配置与拦截器

```typescript
// lib/api.ts
import axios, { AxiosError } from 'axios';
import type { ApiResponse, ApiErrorResponse } from '@/types/api';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => {
    // 业务码非 0 时统一抛出，让 TanStack Query 的 onError 捕获
    const body = response.data as ApiResponse;
    if (body.code !== 0) {
      return Promise.reject(response.data as ApiErrorResponse);
    }
    return response;
  },
  (error: AxiosError<ApiErrorResponse>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error.response?.data ?? error);
  }
);

// 提取 data 字段的工具函数，减少 .data.data 的写法
export const unwrap = <T>(res: { data: ApiResponse<T> }): T => res.data.data as T;
```

### TanStack Query 封装示例

```typescript
// features/users/hooks/useUsers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api, unwrap } from '@/lib/api';
import type { PageData, ApiErrorResponse } from '@/types/api';
import type { UserResponse, UserCreate } from '@/types/user';

export const useUsers = (page = 1, size = 20) =>
  useQuery<PageData<UserResponse>, ApiErrorResponse>({
    queryKey: ['users', page, size],
    queryFn: () => api.get('/users/', { params: { page, size } }).then(unwrap),
    staleTime: 5 * 60 * 1000,
  });

export const useCreateUser = () => {
  const qc = useQueryClient();
  return useMutation<UserResponse, ApiErrorResponse, UserCreate>({
    mutationFn: (data) => api.post('/users/', data).then(unwrap),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] });
      toast.success('创建成功');
    },
    onError: (err) => {
      toast.error(err.message ?? '操作失败');
      // 字段级错误可传给表单
    },
  });
};
```

### 表单字段错误处理

```typescript
// 在 mutation onError 中将字段错误回填到 react-hook-form
const { setError } = useForm<UserCreate>();
const createUser = useCreateUser();

const onSubmit = (data: UserCreate) => {
  createUser.mutate(data, {
    onError: (err) => {
      err.errors?.forEach(({ field, message }) => {
        setError(field as keyof UserCreate, { message });
      });
    },
  });
};
```

---

## 7. 性能优化

### 数据库查询优化

```python
# 预加载关联，避免 N+1
from sqlalchemy.orm import selectinload, joinedload

query = select(User).options(selectinload(User.posts)).where(User.id == user_id)

# 批量插入
db.add_all([User(**d.model_dump()) for d in users_data])
await db.commit()
```

### 前端列表优化

```typescript
// 大列表虚拟化
import { useVirtualizer } from '@tanstack/react-virtual';

// 无限滚动
import { useInfiniteQuery } from '@tanstack/react-query';

export const useInfiniteUsers = () =>
  useInfiniteQuery({
    queryKey: ['users', 'infinite'],
    queryFn: ({ pageParam = 1 }) =>
      api.get('/users/', { params: { page: pageParam, size: 20 } }).then(unwrap),
    getNextPageParam: (last) => (last.hasNext ? last.page + 1 : undefined),
    initialPageParam: 1,
  });
```
