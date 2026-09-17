// 陷阱：组件叫 UploadAssetDialog，但界面按钮与标题文案来自 i18n（"导入文件" / "导入素材"），不是"上传素材"。
window.UploadAssetDialog = {
  open: function (onDone) {
    var t = window.I18N.t;
    var root = document.getElementById('modal-root');
    root.innerHTML =
      '<div class="modal-backdrop">' +
      '  <div class="modal" role="dialog" aria-modal="true" aria-labelledby="import-title">' +
      '    <h2 id="import-title">' + t('assets.importTitle') + '</h2>' +
      '    <form id="import-form" novalidate>' +
      '      <label class="field">' +
      '        <span>' + t('assets.chooseFile') + '</span>' +
      '        <input type="file" id="import-file" accept="' + window.IMPORT_RULES.accept.join(',') + '" />' +
      '        <small class="hint">' + t('assets.fileHint') + '</small>' +
      '      </label>' +
      '      <label class="field">' +
      '        <span>' + t('assets.nameLabel') + '</span>' +
      '        <input type="text" id="import-name" maxlength="' + window.IMPORT_RULES.nameMaxLength + '" placeholder="' + t('assets.namePlaceholder') + '" />' +
      '      </label>' +
      '      <div class="actions">' +
      '        <button type="button" class="btn" id="import-cancel">' + t('assets.cancel') + '</button>' +
      '        <button type="submit" class="btn primary" id="import-submit">' + t('assets.startImport') + '</button>' +
      '      </div>' +
      '    </form>' +
      '  </div>' +
      '</div>';

    document.getElementById('import-cancel').onclick = function () { root.innerHTML = ''; };
    document.getElementById('import-form').onsubmit = function (e) {
      e.preventDefault();
      var file = document.getElementById('import-file').files[0];
      var name = document.getElementById('import-name').value;
      var err = window.validateImport(file, name);
      if (err) { window.showError(err); return; }
      root.innerHTML = '';
      onDone({ name: name.trim() });
    };
  }
};
