# Lumen 素材库

团队内部的素材管理小工具：导入 CSV / XLSX 目录文件，系统处理后供其他页面引用。

## 运行

```bash
pnpm dev   # 或 python3 -m http.server 8766
```

打开 http://localhost:8766/ 。顶栏的角色下拉用于演示不同角色看到的界面（真实环境由登录态决定）。

## 结构

- `src/router.js` 路由与菜单
- `src/i18n/zh-CN.json` 全部界面文案
- `src/permissions.js` 角色与权限点
- `src/validation.js` 导入校验规则
- `src/status.js` 素材状态
- `src/errors.js` 错误码
