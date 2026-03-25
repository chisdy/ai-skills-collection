# MCP 工具集成指南

## Context7 查询策略

遇到第三方库时，按以下顺序查询以提高效率：

1. 先查库的基本信息和当前版本
2. 查具体功能的实现方式
3. 查已知问题和 breaking changes
4. 查最佳实践和性能优化建议

**示例查询**:
- `"React 18 useEffect 最佳实践"`
- `"Next.js App Router 数据获取方式"`
- `"TypeScript 5.0 迁移指南"`

---

## Sequential-Thinking 思考框架

处理复杂决策时，按以下结构推演：

1. 问题定义和约束条件
2. 可能解决方案枚举
3. 每个方案的优缺点分析
4. 风险评估和缓解策略
5. 最终推荐和理由

**示例**:
```
问题: 选择状态管理方案
思考1: 分析应用复杂度和团队技能
思考2: 比较 Redux、Zustand、Jotai 的特点
思考3: 评估学习成本和维护成本
思考4: 考虑性能和开发体验
思考5: 给出推荐方案和理由
```

---

## Playwright 测试模板

### 基础交互测试

```javascript
async function testLogin(page) {
  await page.goto("/login");
  await page.fill('[data-testid="email"]', "test@example.com");
  await page.fill('[data-testid="password"]', "password");
  await page.click('[data-testid="submit"]');
  await page.waitForURL("/dashboard");
}
```

### 调试场景组合

```
Playwright 问题复现 → Sequential-Thinking 根因分析 → Context7 查询解决方案
```

---

## 工具组合模式

| 场景 | 工具组合 |
|------|---------|
| 研究阶段 | Context7 查文档 → Sequential-Thinking 分析方案 |
| 执行阶段 | 代码实现 → Playwright 功能验证 |
| 调试阶段 | Playwright 复现 → Sequential-Thinking 根因分析 → Context7 查解决方案 |
