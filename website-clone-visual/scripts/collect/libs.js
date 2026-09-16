/* collect/libs.js — 识别页面用了哪些前端库 / 框架 / 动画库 / CSS 框架 / 建站平台。
   证据来源：window 全局、<script src>、DOM 特征属性、class 命名模式。每条给出 evidence，方便人工核对。 */
(() => {
  const detected = [];
  const add = (name, category, evidence) => { if (!detected.some((d) => d.name === name)) detected.push({ name, category, evidence }); };
  const g = (k) => { try { return window[k]; } catch (e) { return undefined; } };

  const GLOBALS = [
    ["gsap", "gsap", "animation"], ["ScrollTrigger", "GSAP ScrollTrigger", "animation"], ["AOS", "AOS", "animation"],
    ["Swiper", "Swiper", "carousel"], ["Splide", "Splide", "carousel"], ["Flickity", "Flickity", "carousel"], ["Glide", "Glide", "carousel"],
    ["Lenis", "Lenis", "smooth-scroll"], ["LocomotiveScroll", "Locomotive Scroll", "smooth-scroll"], ["ScrollReveal", "ScrollReveal", "animation"],
    ["anime", "anime.js", "animation"], ["lottie", "Lottie", "animation"], ["bodymovin", "Lottie", "animation"], ["THREE", "Three.js", "3d"],
    ["barba", "Barba.js", "transition"], ["Alpine", "Alpine.js", "framework"], ["htmx", "htmx", "framework"],
    ["jQuery", "jQuery", "library"], ["Vue", "Vue", "framework"], ["React", "React", "framework"], ["__NEXT_DATA__", "Next.js", "framework"],
    ["__NUXT__", "Nuxt", "framework"], ["__remixContext", "Remix", "framework"], ["Webflow", "Webflow", "platform"], ["Shopify", "Shopify", "platform"],
    ["wp", "WordPress", "platform"], ["elementorFrontend", "Elementor", "platform"], ["Typed", "Typed.js", "animation"], ["particlesJS", "particles.js", "animation"],
    ["Rellax", "Rellax", "parallax"], ["simpleParallax", "simpleParallax", "parallax"], ["SplitType", "SplitType", "animation"], ["SplitText", "GSAP SplitText", "animation"],
  ];
  for (const [key, name, cat] of GLOBALS) if (g(key) !== undefined) add(name, cat, `window.${key}`);

  // React / Vue / Svelte 的 DOM 痕迹
  const root = document.querySelector("#root, #app, #__next, #__nuxt, [data-reactroot]");
  if (root) {
    for (const k of Object.keys(root)) {
      if (k.startsWith("__reactContainer") || k.startsWith("_reactRootContainer")) add("React", "framework", `${k} on ${root.id ? "#" + root.id : root.tagName}`);
      if (k === "__vue_app__" || k === "__vue__") add("Vue", "framework", `${k} on ${root.id ? "#" + root.id : root.tagName}`);
    }
  }
  if (document.querySelector("[data-svelte-h], .svelte-")) add("Svelte", "framework", "data-svelte-h / .svelte- class");
  if (document.querySelector("astro-island, [data-astro-cid]")) add("Astro", "framework", "astro-island");
  if (document.querySelector("[data-framer-name], [data-framer-component-type], .framer-")) add("Framer", "platform", "data-framer-* attributes");
  if (document.querySelector("[style*='--framer'], [data-projection-id]")) add("Framer Motion", "animation", "data-projection-id / --framer vars");
  if (document.querySelector("[data-wf-page], [data-wf-site], .w-nav, .w-container")) add("Webflow", "platform", "data-wf-page / .w-* classes");
  if (document.querySelector("[data-aos]")) add("AOS", "animation", "[data-aos] attributes");
  if (document.querySelector("[data-scroll], [data-scroll-container]")) add("Locomotive Scroll", "smooth-scroll", "[data-scroll] attributes");
  if (document.querySelector(".swiper, .swiper-container, .swiper-slide")) add("Swiper", "carousel", ".swiper classes");
  if (document.querySelector(".splide")) add("Splide", "carousel", ".splide class");
  if (document.querySelector(".slick-slider")) add("Slick", "carousel", ".slick-slider class");
  if (document.querySelector("lottie-player, dotlottie-player, [data-lottie]")) add("Lottie", "animation", "<lottie-player> / [data-lottie]");
  if (document.querySelector("canvas[data-engine*='three'], canvas.webgl")) add("Three.js", "3d", "canvas[data-engine] / .webgl");
  if (document.querySelector("[data-sal]")) add("sal.js", "animation", "[data-sal]");
  if (document.querySelector(".wow")) add("WOW.js", "animation", ".wow class");
  if (document.querySelector("[x-data]")) add("Alpine.js", "framework", "[x-data]");
  if (document.querySelector("[hx-get], [hx-post]")) add("htmx", "framework", "[hx-*]");
  if (document.querySelector("link[href*='wp-content'], script[src*='wp-content'], script[src*='wp-includes']")) add("WordPress", "platform", "wp-content assets");
  if (document.querySelector(".elementor, [data-elementor-type]")) add("Elementor", "platform", ".elementor");
  if (document.querySelector("script[src*='cdn.shopify.com'], .shopify-section")) add("Shopify", "platform", "cdn.shopify.com / .shopify-section");
  if (document.querySelector("[data-wix-], #SITE_CONTAINER, script[src*='parastorage']")) add("Wix", "platform", "wix markers");
  if (document.querySelector("script[src*='squarespace'], .sqs-block")) add("Squarespace", "platform", "sqs-block");

  // CSS 框架：class 命名模式
  const classSample = Array.from(document.body.querySelectorAll("*")).slice(0, 2000).map((e) => (typeof e.className === "string" ? e.className : "")).join(" ");
  const twHits = (classSample.match(/\b(flex|grid|items-center|justify-between|px-\d|py-\d|mt-\d|mb-\d|text-(sm|lg|xl|2xl)|bg-\w+-\d{2,3}|rounded(-\w+)?|w-full|max-w-\w+)\b/g) || []).length;
  if (twHits > 25) add("Tailwind CSS", "css", `${twHits} utility-class hits`);
  if (/\b(container|row|col-(xs|sm|md|lg|xl)-\d+|navbar-expand|btn-primary)\b/.test(classSample) && document.querySelector("link[href*='bootstrap'], .navbar-expand-lg, .col-md-6")) add("Bootstrap", "css", "bootstrap classes / link");
  if (/\bMui[A-Z]\w+-root\b/.test(classSample)) add("MUI", "css", "Mui*-root classes");
  if (/\bant-(btn|layout|menu|card)\b/.test(classSample)) add("Ant Design", "css", "ant-* classes");
  if (/\bel-(button|card|menu|input)\b/.test(classSample)) add("Element Plus", "css", "el-* classes");
  if (/\bchakra-\w+\b/.test(classSample)) add("Chakra UI", "css", "chakra-* classes");
  if (/\b(sc-[a-zA-Z0-9]{5,}|css-[a-z0-9]{5,})\b/.test(classSample)) add("CSS-in-JS (styled-components / emotion)", "css", "sc-* / css-* hashed classes");
  if (/\b[a-zA-Z]+_[a-zA-Z]+__[a-zA-Z0-9]{5}\b/.test(classSample)) add("CSS Modules", "css", "hashed module classes");

  // 图标库痕迹
  if (document.querySelector("i.fa, i.fas, i.far, i.fab, i.fa-solid, i.fa-regular, i.fa-brands, [class*='fa-']")) add("Font Awesome", "icons", "fa-* classes");
  if (document.querySelector(".material-icons, .material-symbols-outlined, .material-symbols-rounded")) add("Material Icons", "icons", "material-icons class");
  if (document.querySelector("svg.lucide, [data-lucide]")) add("Lucide", "icons", "svg.lucide");
  if (document.querySelector("svg[data-icon], .iconify")) add("Iconify / data-icon", "icons", "svg[data-icon]");
  if (document.querySelector("i[class*='bi-'], svg.bi")) add("Bootstrap Icons", "icons", "bi-* classes");
  if (document.querySelector("i[class*='ri-']")) add("Remix Icon", "icons", "ri-* classes");
  if (document.querySelector("i[class*='iconfont'], .iconfont")) add("iconfont (阿里)", "icons", ".iconfont");
  if (document.querySelector("svg > use[href^='#'], svg > use[*|href^='#']")) add("SVG sprite", "icons", "<use href=#…>");

  const scripts = Array.from(document.scripts).map((s) => s.src).filter(Boolean).map((src) => {
    const m = src.match(/(gsap|aos|swiper|lenis|three|lottie|jquery|react|vue|next|nuxt|alpine|htmx|bootstrap|tailwind|framer|webflow|wp-|elementor|shopify|splide|slick|anime|barba|locomotive|typed|particles)/i);
    return { src, hint: m ? m[1].toLowerCase() : null };
  });
  for (const s of scripts) if (s.hint) add(s.hint, "script", s.src);

  const result = {
    url: location.href,
    detected,
    scripts,
    fontLinks: Array.from(document.querySelectorAll("link[href*='fonts.googleapis'], link[href*='fonts.gstatic'], link[href*='typekit'], link[href*='fonts.bunny'], link[href*='fontshare']")).map((l) => l.href),
    stylesheetLinks: Array.from(document.querySelectorAll("link[rel='stylesheet']")).map((l) => l.href),
    generator: (document.querySelector("meta[name='generator']") || {}).content || null,
  };
  window.__wc = window.__wc || {};
  window.__wc.libs = result;
  return JSON.parse(JSON.stringify(result)); // 去掉 undefined 键：与 _read.js 分片 / 脚本路径落盘字节一致
})();
