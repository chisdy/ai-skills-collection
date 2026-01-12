# API 设计模式

## FastAPI 最佳实践

### 1. 响应模型设计

#### 标准响应格式

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    errors: Optional[list[str]] = None

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int
```

#### 使用示例

```python
@router.get("/users/", response_model=APIResponse[list[UserResponse]])
async def get_users(
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[list[UserResponse]]:
    users = await user_service.get_users(db, page, size)
    return APIResponse(data=users)
```

### 2. 错误处理模式

#### 自定义异常

```python
class BusinessException(Exception):
    def __init__(self, message: str, code: str = "BUSINESS_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

class ValidationException(BusinessException):
    def __init__(self, field: str, message: str):
        super().__init__(f"{field}: {message}", "VALIDATION_ERROR")
        self.field = field
```

#### 全局异常处理器

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": exc.message,
            "code": exc.code,
            "errors": [exc.message]
        }
    )
```

### 3. 依赖注入模式

#### 数据库会话

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

#### 当前用户

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(
    token: str = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

### 4. 分页模式

#### 分页参数

```python
from pydantic import BaseModel, Field

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(10, ge=1, le=100, description="每页大小")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
```

#### 分页查询

```python
async def get_users_paginated(
    db: AsyncSession,
    pagination: PaginationParams
) -> PaginatedResponse[UserResponse]:
    # 获取总数
    count_query = select(func.count(User.id))
    total = await db.scalar(count_query)

    # 获取数据
    query = select(User).offset(pagination.offset).limit(pagination.size)
    result = await db.execute(query)
    users = result.scalars().all()

    return PaginatedResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=math.ceil(total / pagination.size)
    )
```

## 前端 API 集成

### 1. Axios 配置

#### 基础配置

```typescript
import axios from "axios";

const api = axios.create({
  baseURL: process.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
  timeout: 10000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
```

### 2. TanStack Query 模式

#### 查询 Hook

```typescript
import { useQuery, UseQueryOptions } from "@tanstack/react-query";

export const useUsers = (
  params?: PaginationParams,
  options?: UseQueryOptions<PaginatedResponse<UserResponse>>
) => {
  return useQuery({
    queryKey: ["users", params],
    queryFn: () => api.get("/users/", { params }).then((res) => res.data),
    staleTime: 5 * 60 * 1000, // 5分钟
    ...options,
  });
};
```

#### 变更 Hook

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";

export const useCreateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userData: UserCreate) =>
      api.post("/users/", userData).then((res) => res.data),
    onSuccess: (data) => {
      // 更新缓存
      queryClient.invalidateQueries({ queryKey: ["users"] });
      // 或者直接更新
      queryClient.setQueryData(["users", data.id], data);
    },
    onError: (error) => {
      console.error("创建用户失败:", error);
    },
  });
};
```

### 3. 错误处理

#### 错误类型定义

```typescript
interface APIError {
  success: false;
  message: string;
  code: string;
  errors: string[];
}

interface APIResponse<T> {
  success: true;
  data: T;
  message?: string;
}
```

#### 错误处理 Hook

```typescript
import { toast } from "sonner";

export const useErrorHandler = () => {
  return (error: any) => {
    if (error.response?.data?.message) {
      toast.error(error.response.data.message);
    } else {
      toast.error("操作失败，请稍后重试");
    }
  };
};
```

## 性能优化

### 1. 数据库查询优化

#### 预加载关联

```python
from sqlalchemy.orm import selectinload

async def get_user_with_posts(db: AsyncSession, user_id: int) -> User:
    query = select(User).options(selectinload(User.posts)).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

#### 批量操作

```python
async def create_users_batch(db: AsyncSession, users_data: list[UserCreate]) -> list[User]:
    users = [User(**user_data.model_dump()) for user_data in users_data]
    db.add_all(users)
    await db.commit()
    return users
```

### 2. 前端性能优化

#### 虚拟化长列表

```typescript
import { useVirtualizer } from "@tanstack/react-virtual";

export const UserList = ({ users }: { users: UserResponse[] }) => {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: users.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60,
  });

  return (
    <div ref={parentRef} className="h-96 overflow-auto">
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: virtualItem.size,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <UserCard user={users[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
};
```

#### 无限滚动

```typescript
import { useInfiniteQuery } from "@tanstack/react-query";

export const useInfiniteUsers = () => {
  return useInfiniteQuery({
    queryKey: ["users", "infinite"],
    queryFn: ({ pageParam = 1 }) =>
      api
        .get("/users/", { params: { page: pageParam, size: 20 } })
        .then((res) => res.data),
    getNextPageParam: (lastPage) => {
      return lastPage.page < lastPage.pages ? lastPage.page + 1 : undefined;
    },
    initialPageParam: 1,
  });
};
```
