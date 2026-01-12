---
name: react-fastapi-fullstack
description: 专业的 React 前端与 FastAPI 后端全栈开发专家。擅长类型安全的跨语言开发，确保 TypeScript 与 Pydantic 模型完美对齐。适用于：(1) React + FastAPI 全栈项目开发，(2) 高性能异步 API 设计，(3) 前后端数据模型同步，(4) FastAPI 现代后端架构，(5) 现代前端状态管理（Zustand + TanStack Query），(6) 跨语言代码规范制定，(7) 自动 API 文档生成。
---

# React & FastAPI Full Stack Expert

专业的 React 前端与 FastAPI 后端全栈开发技能，专注于高性能、类型安全和现代化工程实践。

## 核心能力

### 技术栈专精

- **前端**: React 18+ + TypeScript + Vite + Zustand + TanStack Query + Tailwind CSS
- **后端**: FastAPI + Python 3.10+ + Pydantic V2 + SQLAlchemy 2.0 (Async)
- **工具链**: Ruff (Python) + Poetry/UV + React Hook Form + Zod + Axios

### 关键特色

1. **高性能异步**: FastAPI 原生异步支持，SQLAlchemy 2.0 异步 ORM
2. **类型同步**: Pydantic 模型与 TypeScript 接口完美对齐
3. **自动文档**: FastAPI 自动生成 OpenAPI 文档和交互式 API 界面
4. **命名规范**: 自动处理 snake_case (Python) ↔ camelCase (TypeScript) 转换
5. **架构分层**: 清晰的 Router → Service → CRUD 分层架构
6. **现代前端**: TanStack Query + Zustand 的现代状态管理

## 工作流程

### 1. Schema-First 开发

始终从 FastAPI + Pydantic 模型开始：

```python
# schemas/user.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        ),
        populate_by_name=True
    )

    email: str = Field(..., description="用户邮箱", example="user@example.com")
    full_name: str = Field(..., description="用户全名", min_length=1, max_length=100)
    is_active: bool = Field(True, description="是否激活")

class UserCreate(UserBase):
    password: str = Field(..., description="密码", min_length=6)

class UserUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=lambda x: ''.join(w.capitalize() if i > 0 else w for i, w in enumerate(x.split('_'))))

    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
```

### 2. FastAPI 路由设计

利用 FastAPI 的自动文档和验证特性：

```python
# api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter()

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
    description="创建新用户账户"
)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """创建新用户"""
    return await user_service.create_user(db, user_data)

@router.get(
    "/",
    response_model=List[UserResponse],
    summary="获取用户列表",
    description="分页获取用户列表"
)
async def get_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    db: AsyncSession = Depends(get_db)
) -> List[UserResponse]:
    """获取用户列表"""
    return await user_service.get_users(db, skip=skip, limit=limit)
```

### 3. 异步数据库操作

充分利用 SQLAlchemy 2.0 异步特性：

```python
# crud/user.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from models.user import User
from schemas.user import UserCreate, UserUpdate

class UserCRUD:
    async def get(self, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        result = await db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        obj_data = obj_in.model_dump()
        # 处理密码哈希等逻辑
        obj_data["hashed_password"] = get_password_hash(obj_data.pop("password"))

        db_obj = User(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
```

### 4. 前端类型同步

基于 FastAPI OpenAPI 自动生成或手动同步类型：

```typescript
// types/user.ts - 与 Pydantic 模型完全对应
export interface UserBase {
  email: string;
  fullName: string;
  isActive: boolean;
}

export interface UserCreate extends UserBase {
  password: string;
}

export interface UserUpdate {
  email?: string;
  fullName?: string;
  isActive?: boolean;
}

export interface UserResponse extends UserBase {
  id: number;
  createdAt: string;
  updatedAt?: string;
}
```

### 5. TanStack Query 集成

现代化的 API 状态管理：

```typescript
// hooks/useUsers.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { UserCreate, UserResponse } from "../types/user";
import { api } from "../lib/api";

export const useUsers = (skip = 0, limit = 10) => {
  return useQuery({
    queryKey: ["users", skip, limit],
    queryFn: async (): Promise<UserResponse[]> => {
      const { data } = await api.get("/users/", {
        params: { skip, limit },
      });
      return data;
    },
    staleTime: 5 * 60 * 1000, // 5分钟
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userData: UserCreate): Promise<UserResponse> => {
      const { data } = await api.post("/users/", userData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
};
```

## FastAPI 特色功能

### 1. 自动 API 文档

FastAPI 自动生成交互式文档：

```python
# main.py
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html

app = FastAPI(
    title="React FastAPI App",
    description="高性能全栈应用",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# 访问 http://localhost:8000/docs 查看交互式 API 文档
```

### 2. 依赖注入系统

强大的依赖注入和中间件：

```python
# core/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer()

async def get_current_user(
    token: str = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    # JWT 验证逻辑
    user = await authenticate_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user

# 在路由中使用
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return UserResponse.model_validate(current_user)
```

### 3. 后台任务

异步后台任务处理：

```python
from fastapi import BackgroundTasks

async def send_email_notification(email: str, message: str):
    # 发送邮件的异步任务
    await email_service.send(email, message)

@router.post("/users/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    user = await user_service.create_user(db, user_data)

    # 添加后台任务
    background_tasks.add_task(
        send_email_notification,
        user.email,
        "欢迎注册！"
    )

    return user
```

## 目录结构规范

### FastAPI 后端结构

```
app/
├── main.py              # FastAPI 应用入口
├── api/
│   └── v1/
│       ├── api.py       # 路由汇总
│       ├── endpoints/   # 具体路由
│       └── deps.py      # 依赖注入
├── core/
│   ├── config.py       # 配置管理
│   ├── security.py     # 认证授权
│   └── database.py     # 数据库连接
├── crud/               # 数据访问层
├── models/             # SQLAlchemy 模型
├── schemas/            # Pydantic 模型
├── services/           # 业务逻辑层
└── utils/              # 工具函数
```

### React 前端结构

```
src/
├── components/         # 共享 UI 组件
├── features/          # 功能模块
│   └── users/
│       ├── components/ # 用户相关组件
│       ├── hooks/     # 用户相关 hooks
│       ├── types/     # 用户相关类型
│       └── api/       # 用户 API 调用
├── lib/
│   ├── api.ts        # Axios 配置
│   └── utils.ts      # 工具函数
├── stores/           # Zustand 状态管理
└── types/            # 全局类型定义
```

## 编码规范

### FastAPI 最佳实践

1. **路由组织**: 使用 APIRouter 模块化路由
2. **依赖注入**: 充分利用 Depends 系统
3. **异常处理**: 使用 HTTPException 和自定义异常处理器
4. **文档注释**: 为所有端点添加详细的文档字符串
5. **响应模型**: 始终定义 response_model

### 类型安全原则

- **Python**: 严格类型提示，使用 Pydantic 验证
- **TypeScript**: 严格模式，避免 any 类型
- **API 契约**: Pydantic 模型是唯一数据源

## 快捷指令

- `@FastAPIModel`: 创建 SQLAlchemy 模型 + Pydantic Schema + FastAPI 路由三件套
- `@AsyncEndpoint`: 生成异步 FastAPI 端点（包含文档和验证）
- `@TypeSync`: 基于 Pydantic 模型生成 TypeScript 接口
- `@QueryHook`: 生成 TanStack Query hooks

## 参考资源

详细的实现指南和最佳实践：

- **FastAPI 模式**: 查看 [references/fastapi-patterns.md](references/fastapi-patterns.md)
- **类型同步指南**: 查看 [references/type-sync-guide.md](references/type-sync-guide.md)
- **项目模板**: 查看 [assets/project-templates/](assets/project-templates/)

## 使用场景

此技能适用于：

1. 高性能 React + FastAPI 全栈项目
2. 需要自动 API 文档的项目
3. 异步密集型应用开发
4. 类型安全的 API 设计
5. 现代化项目架构重构
