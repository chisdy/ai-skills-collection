# 栈：Vue 3.5 + Tailwind CSS v4（Vite + pnpm）

适合：团队用 Vue、需要 SFC 的样式就近、后续接 Nuxt。

## 初始化

```bash
pnpm create vite@latest site --template vue-ts && cd site
pnpm add -D tailwindcss @tailwindcss/vite
pnpm add lucide-vue-next
```

`vite.config.ts` 加 `tailwindcss()`；`src/style.css` 顶部 `@import "tailwindcss";`。

## 骨架

```
src/
  style.css                 @import tailwind; @theme { token }; @keyframes; 全局 reveal 类
  main.ts  App.vue          路由（vue-router）
  components/
    layout/SiteHeader.vue SiteFooter.vue Container.vue
    sections/HeroSection.vue FeatureGrid.vue Showcase.vue Testimonial.vue Newsletter.vue   ← 对应蓝图 §7
    ui/BaseButton.vue BaseCard.vue BaseBadge.vue
  directives/reveal.ts      v-reveal（IntersectionObserver）
  data/                     文案与列表
  assets/
```

## token → `@theme`

同 React 栈（见 `stack-react.md`），写在 `style.css`。SFC 里需要局部变量时用 `<style scoped>` + `var(--color-primary)`。

## 区块实现约定

- 一个蓝图区块 = 一个 `sections/*.vue`；模板用 Tailwind 类，复杂选择器（`:hover img`、伪元素下划线）写在 `<style scoped>`
- 列数 / gap / padding 数值来源同 React 栈；Tailwind v4 断点 min-width，桌面优先的原站反着写
- `defineProps` 接收 `data/` 的内容；不要在模板里写死文案

## 动画

- `v-reveal` 指令：mounted 时 observe，进入视口加 `is-visible`；`style.css` 里定义 `.reveal / .reveal.is-visible` 与 reduced-motion 分支
- 入场 stagger：`:style="{ '--delay': i * 80 + 'ms' }"`
- `<Transition>` / `<TransitionGroup>` 处理显隐与列表变化；复杂时间线用 GSAP（`pnpm add gsap`）

## 图标

`import { Search, ShoppingCart } from "lucide-vue-next"`，`<Search :size="20" aria-hidden="true" />`；映射表来自 `icons-map.json`。Logo 内联为 `ui/BrandLogo.vue`。

## 图片与字体

同 React 栈：`src/assets/` 与 `public/`；`@font-face` 在 `style.css`。

## 运行与校验

```bash
pnpm dev --port 5173
/tmp/wc-venv/bin/python scripts/compare_pages.py <原站> http://localhost:5173/ -o compare/
```

## 交付物

项目目录、`README.md`（安装 / 运行 / 素材版权 / 已知差异 / 组件与蓝图区块对照表）、`compare/compare-report.md`。
