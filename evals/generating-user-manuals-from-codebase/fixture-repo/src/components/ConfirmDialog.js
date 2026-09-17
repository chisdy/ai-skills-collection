window.ConfirmDialog = {
  open: function (opts) {
    var root = document.getElementById('modal-root');
    root.innerHTML =
      '<div class="modal-backdrop">' +
      '  <div class="modal danger" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title" aria-describedby="confirm-desc">' +
      '    <h2 id="confirm-title">' + opts.title + '</h2>' +
      '    <p id="confirm-desc">' + opts.message + '</p>' +
      '    <div class="actions">' +
      '      <button type="button" class="btn" id="confirm-cancel">' + opts.cancelText + '</button>' +
      '      <button type="button" class="btn danger" id="confirm-ok">' + opts.okText + '</button>' +
      '    </div>' +
      '  </div>' +
      '</div>';
    document.getElementById('confirm-cancel').onclick = function () { root.innerHTML = ''; };
    document.getElementById('confirm-ok').onclick = function () { root.innerHTML = ''; opts.onOk(); };
  }
};
