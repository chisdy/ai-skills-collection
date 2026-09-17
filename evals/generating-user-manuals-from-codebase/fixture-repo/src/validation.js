// 导入表单校验规则
window.IMPORT_RULES = {
  accept: ['.csv', '.xlsx'],
  maxSizeBytes: 5 * 1024 * 1024, // 5 MB，与 i18n assets.fileHint 一致
  nameMaxLength: 60,             // 界面 maxlength 属性
  // 陷阱：仅代码可见的限制——单个文件最多 500 行，超出会在"处理"阶段失败为 E2001。
  // 界面上没有任何提示，手册不应把它写成用户可预知的规则，应进编辑备注。
  maxRows: 500
};

window.validateImport = function (file, name) {
  if (!file) return window.ErrorCode.FILE_TYPE;
  var ext = '.' + file.name.split('.').pop().toLowerCase();
  if (window.IMPORT_RULES.accept.indexOf(ext) === -1) return window.ErrorCode.FILE_TYPE;
  if (file.size > window.IMPORT_RULES.maxSizeBytes) return window.ErrorCode.FILE_SIZE;
  if (!name || !name.trim()) return window.ErrorCode.NAME_REQUIRED;
  return null;
};
