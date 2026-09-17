window.Views = (function () {
  var t = function (k, v) { return window.I18N.t(k, v); };
  // 用户可控字符串（素材名称等）进 innerHTML / 属性前一律转义
  var esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };

  function statusBadge(status) {
    var m = window.STATUS_LABEL[status];
    return '<span class="badge ' + m.color + '">' + t(m.key) + '</span>';
  }

  function dashboard() {
    var assets = window.Store.assets;
    var processing = assets.filter(function (a) { return a.status === 'processing'; }).length;
    return (
      '<h1>' + t('dashboard.title') + '</h1>' +
      '<div class="cards">' +
      '  <div class="card"><div class="label">' + t('dashboard.totalAssets') + '</div><div class="num">' + assets.length + '</div></div>' +
      '  <div class="card"><div class="label">' + t('dashboard.processing') + '</div><div class="num">' + processing + '</div></div>' +
      '</div>' +
      (window.hasPermission('assets.import')
        ? '<a class="btn primary" href="#/assets?import=1">' + t('dashboard.quickImport') + '</a>'
        : '')
    );
  }

  function assets(query) {
    var rows = window.Store.assets.map(function (a) {
      return (
        '<tr data-id="' + esc(a.id) + '">' +
        '<td>' + esc(a.name) + '</td>' +
        '<td>' + statusBadge(a.status) + '</td>' +
        '<td>' + esc(a.owner) + '</td>' +
        '<td>' + esc(a.updated) + '</td>' +
        '<td>' + (window.hasPermission('assets.delete')
          ? '<button class="btn small danger" data-action="delete" data-id="' + esc(a.id) + '" aria-label="' + t('assets.delete') + ' ' + esc(a.name) + '">' + t('assets.delete') + '</button>'
          : '') + '</td>' +
        '</tr>'
      );
    }).join('');

    var html =
      '<div class="page-head">' +
      '  <h1>' + t('assets.title') + '</h1>' +
      (window.hasPermission('assets.import')
        ? '  <button class="btn primary" id="btn-import">' + t('assets.import') + '</button>'
        : '') +
      '</div>' +
      (window.Store.assets.length
        ? '<table class="table"><thead><tr>' +
          '<th>' + t('assets.columns.name') + '</th><th>' + t('assets.columns.status') + '</th>' +
          '<th>' + t('assets.columns.owner') + '</th><th>' + t('assets.columns.updated') + '</th><th>' + t('assets.columns.actions') + '</th>' +
          '</tr></thead><tbody>' + rows + '</tbody></table>'
        : '<p class="empty">' + t('assets.empty') + '</p>');

    setTimeout(function () {
      var btn = document.getElementById('btn-import');
      if (btn) btn.onclick = openImport;
      if (query.import === '1' && btn) openImport();
      document.querySelectorAll('[data-action="delete"]').forEach(function (b) {
        b.onclick = function () {
          var id = b.getAttribute('data-id');
          var asset = window.Store.assets.filter(function (a) { return a.id === id; })[0];
          window.ConfirmDialog.open({
            title: t('assets.deleteTitle'),
            message: t('assets.deleteConfirm', { name: esc(asset.name) }),
            okText: t('assets.deleteAction'),
            cancelText: t('assets.cancel'),
            onOk: function () {
              window.Store.assets = window.Store.assets.filter(function (a) { return a.id !== id; });
              window.toast(t('assets.toast.deleted'), 'success');
              window.Router.render();
            }
          });
        };
      });
    }, 0);
    return html;
  }

  function openImport() {
    if (!window.hasPermission('assets.import')) { window.showError(window.ErrorCode.FORBIDDEN); return; }
    window.UploadAssetDialog.open(function (payload) {
      window.Store.assets.unshift({
        id: 'a' + Date.now(), name: payload.name, status: window.AssetStatus.PROCESSING,
        owner: '你', updated: new Date().toISOString().slice(0, 16).replace('T', ' ')
      });
      window.toast(t('assets.toast.imported'), 'success');
      location.hash = '#/assets';
      window.Router.render();
    });
  }

  function members() {
    if (!window.hasPermission('members.view')) {
      return '<h1>' + t('members.title') + '</h1><p class="forbidden">' + t('members.forbidden') + '</p>';
    }
    var rows = window.Store.members.map(function (m) {
      return '<tr><td>' + esc(m.name) + '</td><td>' + esc(m.email) + '</td><td>' + t('roles.' + m.role) + '</td></tr>';
    }).join('');
    return (
      '<div class="page-head"><h1>' + t('members.title') + '</h1>' +
      (window.hasPermission('members.invite') ? '<button class="btn primary" id="btn-invite" disabled title="演示环境不可用">' + t('members.invite') + '</button>' : '') +
      '</div>' +
      '<table class="table"><thead><tr><th>' + t('members.columns.name') + '</th><th>' + t('members.columns.email') + '</th><th>' + t('members.columns.role') + '</th></tr></thead><tbody>' + rows + '</tbody></table>'
    );
  }

  function settings() {
    var s = window.Store.settings;
    setTimeout(function () {
      var form = document.getElementById('settings-form');
      if (!form) return;
      form.onsubmit = function (e) {
        e.preventDefault();
        s.notifyOnReady = document.getElementById('notify').checked;
        window.toast(t('settings.saved'), 'success');
      };
    }, 0);
    return (
      '<h1>' + t('settings.title') + '</h1>' +
      '<form id="settings-form" class="form">' +
      '  <label class="field"><span>' + t('settings.language') + '</span><select disabled><option>简体中文</option></select></label>' +
      '  <label class="field row"><input type="checkbox" id="notify" ' + (s.notifyOnReady ? 'checked' : '') + ' /><span>' + t('settings.notifyOnReady') + '</span></label>' +
      '  <div class="actions"><button type="submit" class="btn primary">' + t('settings.save') + '</button></div>' +
      '</form>'
    );
  }

  return { dashboard: dashboard, assets: assets, members: members, settings: settings };
})();

window.toast = function (msg, kind) {
  var root = document.getElementById('toast-root');
  var el = document.createElement('div');
  el.className = 'toast ' + (kind || '');
  el.setAttribute('role', 'status');
  el.textContent = msg;
  root.appendChild(el);
  setTimeout(function () { el.remove(); }, 4000);
};
