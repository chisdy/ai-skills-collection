// 演示数据（内存态）。成员列表故意含演示邮箱，用于检验手册截图是否脱敏。
window.Store = {
  assets: [
    { id: 'a1', name: '2026 春季目录', status: 'ready', owner: '林晓', updated: '2026-09-10 14:02' },
    { id: 'a2', name: '门店清单', status: 'processing', owner: '周涵', updated: '2026-09-16 09:30' },
    { id: 'a3', name: '旧版价格表', status: 'failed', owner: '林晓', updated: '2026-09-15 18:45' }
  ],
  members: [
    { name: '林晓', email: 'lin.xiao@example-corp.com', role: 'admin' },
    { name: '周涵', email: 'zhou.han@example-corp.com', role: 'editor' },
    { name: '陈默', email: 'chen.mo@example-corp.com', role: 'viewer' }
  ],
  settings: {
    language: 'zh-CN',
    notifyOnReady: true
  }
};
