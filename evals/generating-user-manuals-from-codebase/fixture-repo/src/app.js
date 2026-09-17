(function () {
  window.I18N.load().then(function () {
    window.I18N.applyStatic();
    var sel = document.getElementById('role-select');
    sel.value = window.Session.role;
    sel.onchange = function () {
      window.Session.setRole(sel.value);
      window.Router.render();
    };
    window.Router.render();
  });
})();
