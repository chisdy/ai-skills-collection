// 极简 i18n：t('a.b.c') 读取 zh-CN.json，支持 {name} 插值
window.I18N = (function () {
  var dict = {};
  function get(path) {
    return path.split('.').reduce(function (o, k) { return o && o[k]; }, dict);
  }
  function t(key, vars) {
    var s = get(key);
    if (typeof s !== 'string') return key;
    return s.replace(/\{(\w+)\}/g, function (_, k) { return vars && vars[k] != null ? vars[k] : ''; });
  }
  function load() {
    return fetch('src/i18n/zh-CN.json').then(function (r) { return r.json(); }).then(function (d) { dict = d; });
  }
  function applyStatic(root) {
    (root || document).querySelectorAll('[data-i18n]').forEach(function (el) {
      el.textContent = t(el.getAttribute('data-i18n'));
    });
  }
  return { t: t, load: load, applyStatic: applyStatic };
})();
