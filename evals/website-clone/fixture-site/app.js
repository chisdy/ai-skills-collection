/* Lumen fixture 前端逻辑：渲染商品、筛选 / 排序 / 分页、详情、购物车（localStorage）、表单提交。
   所有写操作走 fetch POST 到 /api/*，静态服务器会返回 405/501——这是故意的：功能采集脚本应把它们拦下并标 blocked。 */
(function () {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const params = new URLSearchParams(location.search);

  // ---------- 购物车 ----------
  const CART_KEY = "lumen.cart";
  const cart = {
    read() { try { return JSON.parse(localStorage.getItem(CART_KEY) || "[]"); } catch { return []; } },
    write(items) { localStorage.setItem(CART_KEY, JSON.stringify(items)); renderCartCount(); },
    add(product, qty = 1) {
      const items = cart.read();
      const hit = items.find((i) => i.id === product.id);
      if (hit) hit.qty += qty; else items.push({ id: product.id, name: product.name, price: product.price, image: product.image, qty });
      cart.write(items);
    },
    remove(id) { cart.write(cart.read().filter((i) => i.id !== id)); },
    total() { return cart.read().reduce((s, i) => s + i.price * i.qty, 0); },
  };
  function renderCartCount() {
    const n = cart.read().reduce((s, i) => s + i.qty, 0);
    $$("[data-cart-count]").forEach((el) => (el.textContent = String(n)));
  }

  // ---------- Toast ----------
  function toast(msg) {
    let el = $(".toast");
    if (!el) { el = document.createElement("div"); el.className = "toast"; el.setAttribute("role", "status"); document.body.appendChild(el); }
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(el._t);
    el._t = setTimeout(() => el.classList.remove("show"), 2200);
  }

  // ---------- 滚动显现 ----------
  function initReveal() {
    const els = $$(".reveal");
    if (!("IntersectionObserver" in window)) { els.forEach((e) => e.classList.add("is-visible")); return; }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("is-visible"); io.unobserve(en.target); } });
    }, { threshold: 0.15 });
    els.forEach((e) => io.observe(e));
  }

  // ---------- 数据 ----------
  let productsCache = null;
  async function loadProducts() {
    if (productsCache) return productsCache;
    const res = await fetch("api/products.json");
    productsCache = await res.json();
    return productsCache;
  }

  function stars(rating) {
    return '<span class="product-rating" aria-label="评分 ' + rating + '">' +
      "★".repeat(Math.round(rating)) + "☆".repeat(5 - Math.round(rating)) + "</span>";
  }
  function productCard(p) {
    return `<article class="product-card" data-id="${p.id}">
      <a href="product.html?id=${p.id}"><img src="${p.image}" alt="${p.name}" loading="lazy" width="400" height="300"></a>
      <div class="product-body">
        ${p.tag ? `<span class="product-tag">${p.tag}</span>` : ""}
        <span class="product-category">${p.categoryLabel}</span>
        <a class="product-name" href="product.html?id=${p.id}">${p.name}</a>
        ${stars(p.rating)}
        <span class="product-price">¥${p.price.toLocaleString("zh-CN")}</span>
        <button class="btn btn-secondary" data-add-to-cart="${p.id}" type="button">
          <i class="fa-solid fa-cart-shopping" aria-hidden="true"></i> 加入购物车
        </button>
      </div>
    </article>`;
  }

  async function initFeatured() {
    const grid = $("[data-featured-products]");
    if (!grid) return;
    const products = await loadProducts();
    grid.innerHTML = products.slice(0, 3).map(productCard).join("");
  }

  // ---------- 列表页 ----------
  async function initCatalog() {
    const grid = $("[data-product-grid]");
    if (!grid) return;
    const products = await loadProducts();
    const state = {
      category: params.get("category") || "",
      q: params.get("q") || "",
      sort: params.get("sort") || "featured",
      maxPrice: Number(params.get("maxPrice") || 5000),
      page: Number(params.get("page") || 1),
      perPage: 6,
    };
    const search = $("[data-search]");
    const sort = $("[data-sort]");
    const price = $("[data-price]");
    const priceOut = $("[data-price-out]");
    if (search) search.value = state.q;
    if (sort) sort.value = state.sort;
    if (price) { price.value = String(state.maxPrice); if (priceOut) priceOut.textContent = "¥" + state.maxPrice; }
    $$("[data-category]").forEach((r) => (r.checked = r.value === state.category));

    function apply() {
      let list = products.filter((p) => (!state.category || p.category === state.category) && p.price <= state.maxPrice);
      if (state.q) list = list.filter((p) => p.name.toLowerCase().includes(state.q.toLowerCase()));
      const sorters = {
        featured: (a, b) => a.id - b.id,
        "price-asc": (a, b) => a.price - b.price,
        "price-desc": (a, b) => b.price - a.price,
        rating: (a, b) => b.rating - a.rating,
      };
      list.sort(sorters[state.sort] || sorters.featured);
      const pages = Math.max(1, Math.ceil(list.length / state.perPage));
      state.page = Math.min(state.page, pages);
      const slice = list.slice((state.page - 1) * state.perPage, state.page * state.perPage);
      $("[data-result-count]").textContent = `共 ${list.length} 件`;
      grid.innerHTML = slice.length ? slice.map(productCard).join("") : '<div class="empty-state">没有符合条件的灯具，试试放宽筛选。</div>';
      const pg = $("[data-pagination]");
      pg.innerHTML = `<button type="button" data-page="${state.page - 1}" ${state.page === 1 ? "disabled" : ""} aria-label="上一页">‹</button>` +
        Array.from({ length: pages }, (_, i) => `<button type="button" data-page="${i + 1}" class="${i + 1 === state.page ? "active" : ""}">${i + 1}</button>`).join("") +
        `<button type="button" data-page="${state.page + 1}" ${state.page === pages ? "disabled" : ""} aria-label="下一页">›</button>`;
      const url = new URL(location.href);
      Object.entries({ category: state.category, q: state.q, sort: state.sort, maxPrice: state.maxPrice, page: state.page }).forEach(([k, v]) => v ? url.searchParams.set(k, v) : url.searchParams.delete(k));
      history.replaceState(null, "", url);
    }
    search && search.addEventListener("input", () => { state.q = search.value; state.page = 1; apply(); });
    sort && sort.addEventListener("change", () => { state.sort = sort.value; apply(); });
    price && price.addEventListener("input", () => { state.maxPrice = Number(price.value); priceOut.textContent = "¥" + state.maxPrice; state.page = 1; apply(); });
    $$("[data-category]").forEach((r) => r.addEventListener("change", () => { state.category = r.value; state.page = 1; apply(); }));
    $("[data-pagination]").addEventListener("click", (e) => { const b = e.target.closest("[data-page]"); if (b && !b.disabled) { state.page = Number(b.dataset.page); apply(); window.scrollTo({ top: 0, behavior: "smooth" }); } });
    $("[data-reset]") && $("[data-reset]").addEventListener("click", () => { Object.assign(state, { category: "", q: "", sort: "featured", maxPrice: 5000, page: 1 }); search.value = ""; sort.value = "featured"; price.value = "5000"; priceOut.textContent = "¥5000"; $$("[data-category]").forEach((r) => (r.checked = r.value === "")); apply(); });
    apply();
  }

  // ---------- 详情页 ----------
  async function initDetail() {
    const root = $("[data-product-detail]");
    if (!root) return;
    const products = await loadProducts();
    const p = products.find((x) => String(x.id) === params.get("id")) || products[0];
    document.title = `${p.name} — Lumen`;
    $("[data-breadcrumb-name]").textContent = p.name;
    $("[data-name]").textContent = p.name;
    $("[data-category-label]").textContent = p.categoryLabel;
    $("[data-price]").textContent = "¥" + p.price.toLocaleString("zh-CN");
    $("[data-rating]").innerHTML = stars(p.rating) + ` <span class="help">${p.reviews} 条评价</span>`;
    $("[data-desc]").textContent = p.description;
    const main = $("[data-main-image]");
    main.src = p.image; main.alt = p.name;
    $("[data-thumbs]").innerHTML = [p.image, ...p.gallery].map((src, i) => `<img src="${src}" alt="${p.name} 视图 ${i + 1}" class="${i === 0 ? "active" : ""}" data-thumb>`).join("");
    $("[data-thumbs]").addEventListener("click", (e) => { const t = e.target.closest("[data-thumb]"); if (!t) return; $$("[data-thumb]").forEach((x) => x.classList.remove("active")); t.classList.add("active"); main.src = t.src; });
    $("[data-swatches]").innerHTML = p.colors.map((c, i) => `<button type="button" class="swatch ${i === 0 ? "active" : ""}" style="background:${c.hex}" aria-label="${c.name}" data-swatch></button>`).join("");
    $("[data-swatches]").addEventListener("click", (e) => { const s = e.target.closest("[data-swatch]"); if (!s) return; $$("[data-swatch]").forEach((x) => x.classList.remove("active")); s.classList.add("active"); });
    const qty = $("[data-qty]");
    $("[data-qty-dec]").addEventListener("click", () => (qty.value = Math.max(1, Number(qty.value) - 1)));
    $("[data-qty-inc]").addEventListener("click", () => (qty.value = Math.min(9, Number(qty.value) + 1)));
    $("[data-add-detail]").addEventListener("click", () => { cart.add(p, Number(qty.value)); toast(`已加入购物车：${p.name} × ${qty.value}`); });
    $("[data-wishlist]").addEventListener("click", async (e) => {
      e.currentTarget.classList.toggle("active");
      try { await fetch("/api/wishlist", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ productId: p.id }) }); } catch {}
      toast("已加入心愿单");
    });
    // Tabs
    $$("[data-tab]").forEach((b) => b.addEventListener("click", () => {
      $$("[data-tab]").forEach((x) => x.classList.remove("active")); b.classList.add("active");
      $$("[data-tab-panel]").forEach((pn) => (pn.hidden = pn.dataset.tabPanel !== b.dataset.tab));
    }));
    // 评论
    const res = await fetch("api/reviews.json");
    const reviews = (await res.json()).filter((r) => r.productId === p.id);
    $("[data-reviews]").innerHTML = reviews.length ? reviews.map((r) => `<div class="review"><div class="review-head"><strong>${r.author}</strong><span>${r.date}</span></div>${stars(r.rating)}<p>${r.body}</p></div>`).join("") : '<p class="help">还没有评价。</p>';
    // 相关商品
    $("[data-related]").innerHTML = products.filter((x) => x.category === p.category && x.id !== p.id).slice(0, 3).map(productCard).join("");
  }

  // ---------- 结算页 ----------
  function initCheckout() {
    const list = $("[data-cart-items]");
    if (!list) return;
    function render() {
      const items = cart.read();
      list.innerHTML = items.length ? items.map((i) => `<div class="cart-item" data-id="${i.id}"><img src="${i.image}" alt=""><div><div class="product-name">${i.name}</div><div class="help">¥${i.price} × ${i.qty}</div></div><button type="button" class="icon-btn" aria-label="移除 ${i.name}" data-remove="${i.id}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button></div>`).join("") : '<p class="empty-state">购物车是空的。<a href="products.html">去逛逛</a></p>';
      const subtotal = cart.total();
      const shipping = subtotal >= 999 || subtotal === 0 ? 0 : 20;
      $("[data-subtotal]").textContent = "¥" + subtotal;
      $("[data-shipping]").textContent = shipping ? "¥" + shipping : "免运费";
      $("[data-total]").textContent = "¥" + (subtotal + shipping);
      $("[data-place-order]").disabled = items.length === 0;
    }
    list.addEventListener("click", (e) => { const b = e.target.closest("[data-remove]"); if (b) { cart.remove(Number(b.dataset.remove)); render(); } });
    $$("[name=shipping]").forEach((r) => r.addEventListener("change", render));
    render();
  }

  // ---------- 表单：全部走 fetch POST，静态服务器会拒绝 ----------
  function initForms() {
    $$("form[data-form]").forEach((form) => {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const errBox = $(".error", form);
        const data = Object.fromEntries(new FormData(form).entries());
        if (form.dataset.form === "register" && data.password !== data.confirm) { if (errBox) errBox.textContent = "两次输入的密码不一致"; return; }
        try {
          const res = await fetch(form.getAttribute("action"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
          if (!res.ok) throw new Error("HTTP " + res.status);
          toast("提交成功");
        } catch (err) {
          if (errBox) errBox.textContent = "演示站点不接受提交（" + err.message + "）";
          else toast("演示站点不接受提交");
        }
      });
    });
  }

  // ---------- 全局 ----------
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-add-to-cart]");
    if (b) loadProducts().then((ps) => { const p = ps.find((x) => String(x.id) === b.dataset.addToCart); if (p) { cart.add(p, 1); toast(`已加入购物车：${p.name}`); } });
    const lang = e.target.closest("[data-lang]");
    if (lang) { $$("[data-lang]").forEach((x) => x.classList.remove("active")); lang.classList.add("active"); document.documentElement.lang = lang.dataset.lang === "en" ? "en" : "zh-CN"; }
    const s = e.target.closest("[data-action=open-search]");
    if (s) location.href = "products.html#search";
  });

  renderCartCount();
  initReveal();
  initFeatured();
  initCatalog();
  initDetail();
  initCheckout();
  initForms();
  if (window.AOS) window.AOS.init();
})();
