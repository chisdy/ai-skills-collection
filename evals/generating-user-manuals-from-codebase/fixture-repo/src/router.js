// hash 路由。meta.titleKey 是菜单文案的 i18n key；meta.permission 是进入该页所需权限点。
window.ROUTES = [
  { path: '/dashboard', view: 'dashboard', meta: { titleKey: 'nav.dashboard' } },
  { path: '/assets', view: 'assets', meta: { titleKey: 'nav.assets', permission: 'assets.view' } },
  { path: '/members', view: 'members', meta: { titleKey: 'nav.members', permission: 'members.view', hideWhenForbidden: true } },
  { path: '/settings', view: 'settings', meta: { titleKey: 'nav.settings' } }
];

window.Router = (function () {
  function parse() {
    var h = location.hash.replace(/^#/, '') || '/dashboard';
    var parts = h.split('?');
    var query = {};
    (parts[1] || '').split('&').forEach(function (kv) {
      if (!kv) return;
      var p = kv.split('=');
      query[decodeURIComponent(p[0])] = decodeURIComponent(p[1] || '');
    });
    return { path: parts[0], query: query };
  }

  function renderNav() {
    var nav = document.getElementById('sidebar');
    var cur = parse().path;
    nav.innerHTML = window.ROUTES.filter(function (r) {
      // 守卫：hideWhenForbidden 的路由在无权限时不显示菜单项（其他无权限路由仍显示，进入后看到提示）
      return !(r.meta.hideWhenForbidden && r.meta.permission && !window.hasPermission(r.meta.permission));
    }).map(function (r) {
      return '<a class="nav-item' + (r.path === cur ? ' active' : '') + '" href="#' + r.path + '">' + window.I18N.t(r.meta.titleKey) + '</a>';
    }).join('');
  }

  function render() {
    var loc = parse();
    var route = window.ROUTES.filter(function (r) { return r.path === loc.path; })[0] || window.ROUTES[0];
    document.getElementById('view').innerHTML = window.Views[route.view](loc.query);
    document.title = window.I18N.t(route.meta.titleKey) + ' · ' + window.I18N.t('app.name');
    renderNav();
  }

  window.addEventListener('hashchange', render);
  return { render: render, parse: parse };
})();
