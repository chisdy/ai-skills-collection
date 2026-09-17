// 素材状态枚举与展示映射
window.AssetStatus = {
  UPLOADING: 'uploading',
  PROCESSING: 'processing',
  READY: 'ready',
  FAILED: 'failed'
};

// 状态 → i18n key 与徽标颜色
window.STATUS_LABEL = {
  uploading: { key: 'status.uploading', color: 'blue' },
  processing: { key: 'status.processing', color: 'orange' },
  ready: { key: 'status.ready', color: 'green' },
  failed: { key: 'status.failed', color: 'red' }
};

// 允许的状态流转（导入 → 处理 → 就绪 / 失败；失败可重新导入回到上传中）
window.STATUS_TRANSITIONS = {
  uploading: ['processing'],
  processing: ['ready', 'failed'],
  ready: [],
  failed: ['uploading']
};
