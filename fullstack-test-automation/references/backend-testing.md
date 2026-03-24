# Backend Testing Patterns

FastAPI（Python）和 Fastify（Node.js）的测试模式参考。

---

## 目录

1. [FastAPI 测试](#fastapi-测试)
2. [Fastify 测试](#fastify-测试)

---

## FastAPI 测试

### 依赖安装

```bash
uv add --dev pytest pytest-asyncio httpx pytest-cov factory-boy
```

### pyproject.toml 配置

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["app"]
omit = ["app/main.py", "tests/*"]
```

### tests/conftest.py（核心 fixture）

```python
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# 使用内存 SQLite 做测试隔离
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    return create_async_engine(TEST_DATABASE_URL, echo=False)

@pytest.fixture(autouse=True)
async def setup_db(engine):
    """每个测试前重建表，测试后清理"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(engine):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.fixture
async def client(db_session):
    """覆盖数据库依赖，注入测试 session"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
```

### API 路由测试

```python
# tests/test_users.py
import pytest
from httpx import AsyncClient

class TestCreateUser:
    async def test_成功创建用户(self, client: AsyncClient):
        response = await client.post("/api/users", json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "secure123"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["email"] == "alice@example.com"
        assert "password" not in data["data"]  # 密码不应返回

    async def test_重复邮箱返回409(self, client: AsyncClient):
        payload = {"name": "Alice", "email": "alice@example.com", "password": "pass"}
        await client.post("/api/users", json=payload)
        response = await client.post("/api/users", json=payload)
        assert response.status_code == 409
        assert "已存在" in response.json()["message"]

    async def test_缺少必填字段返回422(self, client: AsyncClient):
        response = await client.post("/api/users", json={"name": "Alice"})
        assert response.status_code == 422

class TestGetUser:
    async def test_获取存在的用户(self, client: AsyncClient):
        # 先创建
        create_resp = await client.post("/api/users", json={
            "name": "Bob", "email": "bob@example.com", "password": "pass"
        })
        user_id = create_resp.json()["data"]["id"]

        # 再获取
        response = await client.get(f"/api/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Bob"

    async def test_不存在的用户返回404(self, client: AsyncClient):
        response = await client.get("/api/users/99999")
        assert response.status_code == 404
```

### Service 层单元测试

```python
# tests/test_user_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.user_service import UserService
from app.schemas.user import UserCreate

class TestUserService:
    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo):
        return UserService(repo=mock_repo)

    async def test_创建用户时密码应被哈希(self, service, mock_repo):
        mock_repo.create.return_value = MagicMock(id=1, email="test@example.com")

        user_data = UserCreate(name="Test", email="test@example.com", password="plain")
        await service.create(user_data)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args.password != "plain"  # 密码已被哈希
        assert call_args.password.startswith("$2b$")  # bcrypt 格式

    async def test_邮箱已存在时抛出异常(self, service, mock_repo):
        from app.exceptions import DuplicateEmailError
        mock_repo.get_by_email.return_value = MagicMock()  # 模拟已存在

        with pytest.raises(DuplicateEmailError):
            await service.create(
                UserCreate(name="Test", email="exists@example.com", password="pass")
            )
```

### 认证测试

```python
# tests/test_auth.py
import pytest
from httpx import AsyncClient

class TestAuth:
    @pytest.fixture(autouse=True)
    async def create_user(self, client: AsyncClient):
        await client.post("/api/users", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        })

    async def test_正确凭据登录成功(self, client: AsyncClient):
        response = await client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()["data"]

    async def test_需要认证的接口未携带token返回401(self, client: AsyncClient):
        response = await client.get("/api/me")
        assert response.status_code == 401

    async def test_携带有效token可访问受保护接口(self, client: AsyncClient):
        login_resp = await client.post("/api/auth/login", json={
            "email": "test@example.com", "password": "password123"
        })
        token = login_resp.json()["data"]["access_token"]

        response = await client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
```

### Factory 模式（复杂数据）

```python
# tests/factories.py
import factory
from app.models import User

class UserFactory(factory.Factory):
    class Meta:
        model = User

    name = factory.Faker("name", locale="zh_CN")
    email = factory.Faker("email")
    hashed_password = "$2b$12$fake_hash_for_testing"
    is_active = True

# 使用
user = UserFactory.build()
users = UserFactory.build_batch(5)
```

---

## Fastify 测试

### 依赖安装

```bash
pnpm add -D vitest @vitest/coverage-v8
```

### vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
    },
  },
})
```

### tests/helpers/build-app.ts

```typescript
import Fastify from 'fastify'
import { registerPlugins } from '../../src/plugins'
import { registerRoutes } from '../../src/routes'

export async function buildApp() {
  const app = Fastify({ logger: false })
  await registerPlugins(app)
  await registerRoutes(app)
  await app.ready()
  return app
}
```

### 路由测试

```typescript
// tests/routes/users.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { buildApp } from '../helpers/build-app'
import type { FastifyInstance } from 'fastify'

describe('Users API', () => {
  let app: FastifyInstance

  beforeEach(async () => {
    app = await buildApp()
  })

  afterEach(async () => {
    await app.close()
  })

  describe('POST /api/users', () => {
    it('应该成功创建用户', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/users',
        payload: { name: 'Alice', email: 'alice@example.com', password: 'pass123' },
      })

      expect(response.statusCode).toBe(201)
      const body = response.json()
      expect(body.data.email).toBe('alice@example.com')
    })

    it('应该在缺少字段时返回 400', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/users',
        payload: { name: 'Alice' }, // 缺少 email 和 password
      })

      expect(response.statusCode).toBe(400)
    })
  })

  describe('GET /api/users/:id', () => {
    it('应该返回 404 当用户不存在', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/api/users/99999',
      })

      expect(response.statusCode).toBe(404)
    })
  })
})
```

### Service 单元测试

```typescript
// tests/services/user-service.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { UserService } from '../../src/services/user-service'

describe('UserService', () => {
  let service: UserService
  const mockRepo = {
    findByEmail: vi.fn(),
    create: vi.fn(),
    findById: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    service = new UserService(mockRepo as any)
  })

  it('应该在邮箱已存在时抛出错误', async () => {
    mockRepo.findByEmail.mockResolvedValue({ id: 1, email: 'exists@example.com' })

    await expect(
      service.create({ name: 'Test', email: 'exists@example.com', password: 'pass' })
    ).rejects.toThrow('Email already exists')
  })

  it('应该在创建时哈希密码', async () => {
    mockRepo.findByEmail.mockResolvedValue(null)
    mockRepo.create.mockResolvedValue({ id: 1, email: 'new@example.com' })

    await service.create({ name: 'Test', email: 'new@example.com', password: 'plain' })

    const createCall = mockRepo.create.mock.calls[0][0]
    expect(createCall.password).not.toBe('plain')
  })
})
```

### Prisma 测试隔离

```typescript
// tests/helpers/prisma.ts
import { PrismaClient } from '@prisma/client'
import { execSync } from 'child_process'

const prisma = new PrismaClient({
  datasources: { db: { url: process.env.TEST_DATABASE_URL } },
})

export async function cleanDatabase() {
  // 按依赖顺序清理
  await prisma.post.deleteMany()
  await prisma.user.deleteMany()
}

export { prisma }
```
