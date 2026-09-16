# 图标：识别、映射、接入

## 1. 四类来源与处理

| 来源 | `icons.json` 字段 | 处理 |
|---|---|---|
| 内联 `<svg>` | `inline[]`（hash 去重，`strokeBased`、`pathCount`、`markup`、`file`） | 映射到图标库；映射不到或是 Logo / 插画 → 直接内联 `icons/*.svg` |
| 精灵图 `<use href="#id">` | `sprites[]`（`symbolFound`、`symbolMarkup`） | 同上；symbol 不在 DOM 时去 `assets.json` 找外链 sprite 文件 |
| icon-font class | `fonts[]`（`family`、`classes`、`ligature`） | 按类名 / ligature 语义映射；**不要**再引 Font Awesome 全量字体 |
| 小图片 `<img src=*.svg / ≤64px>` | `images[]` | 语义清楚的映射；装饰性的下载复用（版权） |

超过 160px 的 SVG 归入 `illustrations`，按素材处理不按图标。

## 2. 映射流程

1. `python3 scripts/map_icons.py capture/ --libraries lucide,heroicons,tabler,ph`
   - 关键词来源：aria-label → title → data-icon → 所在按钮 / 链接文字（≤ 24 字）→ href 路径词 → class（`fa-cart-shopping` → `shopping-cart`）→ ligature → img alt / 文件名
   - 中文词表把"搜索 / 购物车 / 登录 / 菜单 / 关闭 …"翻成 `search / shopping-cart / log-in / menu / x`
   - 调 Iconify 搜索 API 拿候选；stroke 图标优先 lucide → tabler → heroicons → ph，fill 图标优先 heroicons → ph
   - class 含 `logo` / `brand` 的标为不映射
2. 打开 `icons-map.json`，对 `needsReview: true` 的逐个看 `file` 指向的 SVG 与截图裁片，人工定名或决定内联
3. 把映射表（原图标 → 库名:图标名）列给用户确认，再写代码
4. 断网：`candidates` 为空，`keywords` 仍在；对着 Lucide 官网 / `lucide.dev/icons` 手动挑

## 3. 库的选择

| 库 | 风格 | 数量 | 适合 |
|---|---|---|---|
| **Lucide** | 24px stroke 2，圆角线条 | ~1500 | 默认；与 Heroicons outline 接近，React / Vue / 静态都有官方包 |
| **Heroicons** | outline 24 / solid 24 / mini 20 / micro 16 | ~300 | Tailwind 生态；原站是 fill 图标时用 solid |
| **Tabler** | stroke，数量多 | ~5000 | Lucide 找不到时补 |
| **Phosphor** | 6 种粗细 | ~9000 | 原站图标粗细特殊（thin / bold / duotone） |
| **Iconify** | 聚合以上所有 | 20 万+ | 任意集混用；`@iconify/react` / `@iconify/vue` / `iconify-icon` web component 按需加载 |

原站用 Font Awesome / Material Icons：复刻不必同款；等价语义在 Lucide 里基本都有。用户明确要求同款时才引原库。

## 4. 接入

**静态 HTML**：
- 少量图标：把 Lucide SVG 直接内联（`lucide.dev` 复制），加 `aria-hidden="true"`，按钮上保留 `aria-label`
- 多图标：`<script type="module">import { createIcons, icons } from 'https://esm.sh/lucide'; createIcons({ icons });</script>` + `<i data-lucide="search"></i>`；或 `<iconify-icon icon="lucide:search"></iconify-icon>`

**React 19**：`pnpm add lucide-react` → `import { Search } from "lucide-react"` → `<Search size={20} strokeWidth={2} aria-hidden />`。尺寸与 `icons.json.sizes` 对齐。

**Vue 3.5**：`pnpm add lucide-vue-next` → `import { Search } from "lucide-vue-next"` → `<Search :size="20" aria-hidden="true" />`。

**尺寸与颜色**：图标用 `currentColor`，大小由父级 `font-size` 或显式 `size` 控制；原站尺寸看 `sizes`（如 `20x20`）。图标按钮命中区 ≥ 40×40（`icon-btn` 模式）。

## 5. 版权

- Lucide（ISC）、Heroicons（MIT）、Tabler（MIT）、Phosphor（MIT）可自由商用
- 原站内联 SVG 若是品牌 Logo 或定制插画：仅学习用途可内联；其他用途在交付里标注需替换
- Font Awesome Pro 图标（类名 `fa-light` / `fa-duotone` 等）是付费的，复刻里一律换开源库
