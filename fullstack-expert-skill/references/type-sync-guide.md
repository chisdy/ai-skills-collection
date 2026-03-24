# 类型同步指南

## Pydantic 到 TypeScript 转换规则

### 基础类型映射

| Python (Pydantic) | TypeScript          | 说明               |
| ----------------- | ------------------- | ------------------ |
| `str`             | `string`            | 字符串             |
| `int`             | `number`            | 整数               |
| `float`           | `number`            | 浮点数             |
| `bool`            | `boolean`           | 布尔值             |
| `datetime`        | `string`            | ISO 格式日期字符串 |
| `date`            | `string`            | YYYY-MM-DD 格式    |
| `UUID`            | `string`            | UUID 字符串        |
| `Optional[T]`     | `T \| null` 或 `T?` | 可选类型           |
| `list[T]`         | `T[]`               | 数组               |
| `dict[str, T]`    | `Record<string, T>` | 对象映射           |

### 命名转换规则

#### Python (snake_case) → TypeScript (camelCase)

**Pydantic 配置**:

```python
from pydantic import BaseModel, ConfigDict

class UserModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        ),
        populate_by_name=True  # 允许使用原始字段名
    )

    user_id: int
    full_name: str
    created_at: datetime
    is_active: bool
```

**生成的 JSON**:

```json
{
  "userId": 123,
  "fullName": "John Doe",
  "createdAt": "2024-01-01T00:00:00Z",
  "isActive": true
}
```

**对应的 TypeScript**:

```typescript
interface UserModel {
  userId: number;
  fullName: string;
  createdAt: string;
  isActive: boolean;
}
```

### 复杂类型转换

#### 1. 嵌套模型

**Python**:

```python
class Address(BaseModel):
    street: str
    city: str
    postal_code: str

class User(BaseModel):
    name: str
    address: Address
    addresses: list[Address]  # 多个地址
```

**TypeScript**:

```typescript
interface Address {
  street: string;
  city: string;
  postalCode: string;
}

interface User {
  name: string;
  address: Address;
  addresses: Address[];
}
```

#### 2. 联合类型

**Python**:

```python
from typing import Union, Literal

class Event(BaseModel):
    event_type: Literal["click", "view", "purchase"]
    data: Union[ClickData, ViewData, PurchaseData]
```

**TypeScript**:

```typescript
type EventType = "click" | "view" | "purchase";

interface Event {
  eventType: EventType;
  data: ClickData | ViewData | PurchaseData;
}
```

#### 3. 泛型模型

**Python**:

```python
from typing import Generic, TypeVar

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T
    message: Optional[str] = None
```

**TypeScript**:

```typescript
interface APIResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}
```

## 自动化同步工具

### 1. Pydantic 到 TypeScript 生成器

创建一个 Python 脚本来自动生成 TypeScript 类型：

```python
# scripts/generate_types.py
import ast
import re
from pathlib import Path
from typing import Dict, List, Set

class TypeScriptGenerator:
    def __init__(self):
        self.type_mapping = {
            'str': 'string',
            'int': 'number',
            'float': 'number',
            'bool': 'boolean',
            'datetime': 'string',
            'date': 'string',
            'UUID': 'string',
        }

    def snake_to_camel(self, snake_str: str) -> str:
        """将 snake_case 转换为 camelCase"""
        components = snake_str.split('_')
        return components[0] + ''.join(word.capitalize() for word in components[1:])

    def parse_pydantic_model(self, model_code: str) -> Dict:
        """解析 Pydantic 模型代码"""
        tree = ast.parse(model_code)
        models = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查是否继承自 BaseModel
                if any(base.id == 'BaseModel' for base in node.bases if isinstance(base, ast.Name)):
                    models[node.name] = self.extract_fields(node)

        return models

    def extract_fields(self, class_node: ast.ClassDef) -> List[Dict]:
        """提取模型字段"""
        fields = []

        for node in class_node.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                field_name = node.target.id
                field_type = self.get_type_annotation(node.annotation)

                # 检查默认值
                optional = False
                if node.value:
                    if isinstance(node.value, ast.Constant) and node.value.value is None:
                        optional = True

                fields.append({
                    'name': field_name,
                    'camel_name': self.snake_to_camel(field_name),
                    'type': field_type,
                    'optional': optional
                })

        return fields

    def get_type_annotation(self, annotation) -> str:
        """获取类型注解的字符串表示"""
        if isinstance(annotation, ast.Name):
            return self.type_mapping.get(annotation.id, annotation.id)
        elif isinstance(annotation, ast.Subscript):
            # 处理泛型类型如 Optional[str], list[int] 等
            return self.handle_generic_type(annotation)
        return 'any'

    def handle_generic_type(self, subscript: ast.Subscript) -> str:
        """处理泛型类型"""
        if isinstance(subscript.value, ast.Name):
            base_type = subscript.value.id

            if base_type == 'Optional':
                inner_type = self.get_type_annotation(subscript.slice)
                return f"{inner_type} | null"
            elif base_type == 'list':
                inner_type = self.get_type_annotation(subscript.slice)
                return f"{inner_type}[]"
            elif base_type == 'dict':
                # 假设是 dict[str, T] 格式
                return f"Record<string, {self.get_type_annotation(subscript.slice)}>"

        return 'any'

    def generate_typescript_interface(self, model_name: str, fields: List[Dict]) -> str:
        """生成 TypeScript 接口"""
        lines = [f"export interface {model_name} {{"]

        for field in fields:
            optional_marker = '?' if field['optional'] else ''
            lines.append(f"  {field['camel_name']}{optional_marker}: {field['type']};")

        lines.append("}")
        return '\n'.join(lines)

    def generate_from_file(self, pydantic_file: Path, output_file: Path):
        """从 Pydantic 文件生成 TypeScript 类型"""
        with open(pydantic_file, 'r', encoding='utf-8') as f:
            content = f.read()

        models = self.parse_pydantic_model(content)

        typescript_content = []
        typescript_content.append("// Auto-generated TypeScript types from Pydantic models")
        typescript_content.append("// Do not edit manually\n")

        for model_name, fields in models.items():
            interface = self.generate_typescript_interface(model_name, fields)
            typescript_content.append(interface)
            typescript_content.append("")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(typescript_content))

# 使用示例
if __name__ == "__main__":
    generator = TypeScriptGenerator()

    # 生成所有 schema 文件的类型
    schema_dir = Path("app/schemas")
    output_dir = Path("frontend/src/types")

    for schema_file in schema_dir.glob("*.py"):
        if schema_file.name != "__init__.py":
            output_file = output_dir / f"{schema_file.stem}.ts"
            generator.generate_from_file(schema_file, output_file)
            print(f"Generated {output_file}")
```

### 2. Zod Schema 生成器

同时生成 Zod schema 用于前端验证：

```python
def generate_zod_schema(self, model_name: str, fields: List[Dict]) -> str:
    """生成 Zod schema"""
    lines = [f"export const {model_name}Schema = z.object({{"]

    for field in fields:
        zod_type = self.get_zod_type(field['type'])
        if field['optional']:
            zod_type += ".optional()"

        lines.append(f"  {field['camel_name']}: {zod_type},")

    lines.append("});")
    lines.append(f"export type {model_name} = z.infer<typeof {model_name}Schema>;")
    return '\n'.join(lines)

def get_zod_type(self, ts_type: str) -> str:
    """将 TypeScript 类型转换为 Zod 类型"""
    mapping = {
        'string': 'z.string()',
        'number': 'z.number()',
        'boolean': 'z.boolean()',
        'Date': 'z.date()',
    }

    if ts_type.endswith('[]'):
        inner_type = ts_type[:-2]
        return f"z.array({self.get_zod_type(inner_type)})"

    return mapping.get(ts_type, 'z.any()')
```

## 运行时类型验证

### 1. 前端验证

```typescript
import { z } from "zod";

// 从后端响应验证数据
const validateApiResponse = <T>(schema: z.ZodSchema<T>, data: unknown): T => {
  try {
    return schema.parse(data);
  } catch (error) {
    console.error("API response validation failed:", error);
    throw new Error("Invalid API response format");
  }
};

// 使用示例
const users = validateApiResponse(
  z.array(UserResponseSchema),
  apiResponse.data
);
```

### 2. 后端验证增强

```python
from pydantic import BaseModel, validator, Field

class UserCreate(BaseModel):
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    full_name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=0, le=150)

    @validator('email')
    def validate_email_domain(cls, v):
        if not v.endswith(('@company.com', '@partner.com')):
            raise ValueError('Email must be from allowed domains')
        return v

    @validator('full_name')
    def validate_name_format(cls, v):
        if not v.replace(' ', '').isalpha():
            raise ValueError('Name must contain only letters and spaces')
        return v
```

## 最佳实践

### 1. 版本控制

- 为 API 模型添加版本号
- 使用语义化版本控制
- 保持向后兼容性

```python
class UserV1(BaseModel):
    model_config = ConfigDict(
        alias_generator=camelCase,
        extra='forbid'  # 禁止额外字段
    )

    version: Literal["1.0"] = "1.0"
    # ... 其他字段
```

### 2. 文档生成

- 使用 Pydantic 的 `Field` 添加描述
- 自动生成 OpenAPI 文档
- 保持文档与代码同步

```python
class User(BaseModel):
    id: int = Field(..., description="用户唯一标识符")
    email: str = Field(..., description="用户邮箱地址", example="user@example.com")
    full_name: str = Field(..., description="用户全名", min_length=1, max_length=100)
    created_at: datetime = Field(..., description="账户创建时间")
```

### 3. 测试策略

```python
# 测试 Pydantic 模型
def test_user_model_validation():
    # 有效数据
    valid_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "age": 25
    }
    user = UserCreate(**valid_data)
    assert user.email == "test@example.com"

    # 无效数据
    with pytest.raises(ValidationError):
        UserCreate(email="invalid-email", full_name="", age=-1)
```

```typescript
// 测试 TypeScript 类型
import { UserCreateSchema } from "../types/user";

describe("User Type Validation", () => {
  it("should validate correct user data", () => {
    const validUser = {
      email: "test@example.com",
      fullName: "Test User",
      age: 25,
    };

    expect(() => UserCreateSchema.parse(validUser)).not.toThrow();
  });

  it("should reject invalid user data", () => {
    const invalidUser = {
      email: "invalid-email",
      fullName: "",
      age: -1,
    };

    expect(() => UserCreateSchema.parse(invalidUser)).toThrow();
  });
});
```
