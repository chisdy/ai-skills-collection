# MCP 工具集成指南

## Context7 集成模式

### 使用时机

- 遇到不熟悉的库或框架时
- 需要确认 API 最新变动时
- 查询最佳实践和设计模式时
- 避免使用已废弃特性时

### 查询策略

```markdown
1. 先查询库的基本信息和版本
2. 查询具体功能的实现方式
3. 查询已知问题和解决方案
4. 查询最佳实践和性能优化
```

### 示例查询

```
- "React 18 useEffect 最佳实践"
- "Next.js 13 App Router 数据获取"
- "TypeScript 5.0 新特性和迁移指南"
```

## Sequential-Thinking 集成模式

### 使用场景

- 复杂架构设计决策
- 多方案技术选型对比
- 难以复现的 Bug 分析
- 系统性能优化策略

### 思考框架

```markdown
1. 问题定义和约束条件
2. 可能解决方案枚举
3. 每个方案的优缺点分析
4. 风险评估和缓解策略
5. 最终推荐和理由
```

### 示例思考链

```
问题: 选择状态管理方案
思考1: 分析应用复杂度和团队技能
思考2: 比较 Redux、Zustand、Jotai 的特点
思考3: 评估学习成本和维护成本
思考4: 考虑性能和开发体验
思考5: 给出推荐方案和理由
```

## Playwright 集成模式

### 自动化测试场景

- 用户登录流程验证
- 表单提交和验证
- 页面导航和路由测试
- 响应式设计验证

### 调试场景

- 页面加载性能分析
- JavaScript 错误捕获
- 网络请求监控
- 用户交互问题排查

### 测试脚本模板

```javascript
// 登录流程测试
async function testLogin(page) {
  await page.goto("/login");
  await page.fill('[data-testid="email"]', "test@example.com");
  await page.fill('[data-testid="password"]', "password");
  await page.click('[data-testid="submit"]');
  await page.waitForURL("/dashboard");
}
```

## 工具组合使用模式

### 研究阶段组合

```
Context7 查询技术文档 → Sequential-Thinking 分析方案 → 确定技术路径
```

### 执行阶段组合

```
代码实现 → Playwright 功能验证 → Context7 查询优化建议
```

### 调试阶段组合

```
Playwright 问题复现 → Sequential-Thinking 根因分析 → Context7 查询解决方案
```
