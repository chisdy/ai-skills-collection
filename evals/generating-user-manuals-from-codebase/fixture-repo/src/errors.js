// 错误码 → i18n key。界面上通过 toast 显示 I18N.t(ERROR_MESSAGES[code])
window.ErrorCode = {
  FILE_TYPE: 'E1001',
  FILE_SIZE: 'E1002',
  NAME_REQUIRED: 'E1003',
  PROCESS_FAILED: 'E2001',
  FORBIDDEN: 'E3001'
};

window.ERROR_MESSAGES = {
  E1001: 'errors.E1001',
  E1002: 'errors.E1002',
  E1003: 'errors.E1003',
  E2001: 'errors.E2001',
  E3001: 'errors.E3001'
};

window.showError = function (code) {
  window.toast(window.I18N.t(window.ERROR_MESSAGES[code] || code), 'error');
};
