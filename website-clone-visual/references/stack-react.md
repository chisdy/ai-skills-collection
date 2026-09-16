# 栈：React 19 + Tailwind CSS v4（Vite + pnpm）

适合：多页 / 组件复用多、用户后续要接功能、团队用 React。

## 初始化

```bash
pnpm create vite@latest site --template react-ts && cd site
pnpm add -D tailwindcss @tailwindcss/vite
pnpm add lucide-react
```

`vite.config.ts` 加 `tailwindcss()` 插件；`src/index.css` 顶部 `@import "tailwindcss";`。

## 骨架

```
src/
  index.css                 @import tailwind; @theme { token }; @layer base { 排版 / reset 补充 }; @keyframes
  main.tsx  App.tsx         路由（多页用 react-router 或 Vite 多入口）
  components/
    layout/Header.tsx Footer.tsx Container.tsx
    sections/Hero.tsx FeatureGrid.tsx Showcase.tsx Testimonial.tsx Newsletter.tsx   ← 与蓝图 §7 区块一一对应
    ui/Button.tsx Card.tsx Badge.tsx Icon.tsx
  hooks/useReveal.ts        IntersectionObserver
  data/                     文案与列表数据（从 dom.html 抽出来，不写死在 JSX）
  assets/                   图片（版权标注）
```

## token → `@theme`

```css
@import "tailwindcss";
@theme {
  --color-bg: #faf7f2; --color-surface: #fff; --color-text: #1f1a17; --color-muted: #6b625b;
  --color-primary: #c8742a; --color-primary-dark: #a35a1c; --color-accent: #2f5d50; --color-border: #e6ddd2;
  --font-sans: "Inter", "PingFang SC", system-ui, sans-serif; --font-serif: "Playfair Display", Georgia, serif;
  --radius-md: 12px; --radius-lg: 24px;
  --shadow-md: 0 8px 24px rgb(31 26 23 / .10);
  --ease-out: cubic-bezier(.22,1,.36,1);
  --breakpoint-md: 768px; --breakpoint-lg: 1024px;   /* 蓝图 §3 */
}
```
之后 `bg-bg text-text text-primary rounded-md shadow-md font-serif` 直接可用；任意值 `text-[56px] leading-[1.2] tracking-[0.12em]` 用于阶梯外的数值（尽量少）。

## 区块实现约定

- 一个蓝图区块 = 一个 `sections/*.tsx`；`Container` 统一 `max-w-[1200px] mx-auto px-10`（数值来自 `sections.json`）
- 列数与 gap：`grid grid-cols-3 gap-6 md:grid-cols-2 sm:grid-cols-1`（Tailwind v4 断点是 min-width，桌面优先的原站要反着写：`grid-cols-1 md:grid-cols-2 lg:grid-cols-3`）
- 文案与列表进 `data/`，组件只负责布局
- `computed.json` 里查到的字号 / 行高 / 字间距映射到最近的 Tailwind 阶梯；差 1px 以内可接受，否则用任意值

## 动画

- 滚动显现：`useReveal` 返回 `ref` 与 `visible`，class 切 `opacity-0 translate-y-6` → `opacity-100 translate-y-0`，`transition duration-[600ms] ease-[var(--ease-out)]`；`motion-reduce:transition-none motion-reduce:opacity-100`
- `@keyframes` 写在 `index.css`，用 `animate-[fadeUp_700ms_var(--ease-out)_both]` 或在 `@theme` 里定义 `--animate-fade-up`
- 需要 Motion 时 `pnpm add motion`，`import { motion } from "motion/react"`；决策见 `references/animations.md`

## 图标

`components/ui/Icon.tsx` 薄封装 lucide-react，或直接用；映射表来自 `icons-map.json`。原站 Logo 内联为 `components/ui/Logo.tsx`。

## 图片与字体

- 图片放 `src/assets/`，`import hero from "@/assets/hero.svg"`；大图用 `public/`
- 字体：`@font-face` 写在 `index.css`，文件放 `public/fonts/`；或 Google Fonts `<link>` 放 `index.html`

## 运行与校验

```bash
pnpm dev --port 5173
/tmp/wc-venv/bin/python scripts/compare_pages.py <原站> http://localhost:5173/ -o compare/
```
多页：`--map pages.json`。

## 交付物

项目目录、`README.md`（安装 / 运行 / 素材版权 / 已知差异 / 组件与蓝图区块对照表）、`compare/compare-report.md`。
