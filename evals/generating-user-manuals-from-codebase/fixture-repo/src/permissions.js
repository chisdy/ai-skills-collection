// 角色与权限点。演示用：角色由顶栏下拉切换，真实系统里来自登录态。
window.ROLES = ['viewer', 'editor', 'admin'];

window.PERMISSIONS = {
  viewer: ['assets.view'],
  editor: ['assets.view', 'assets.import'],
  admin: ['assets.view', 'assets.import', 'assets.delete', 'members.view', 'members.invite']
};

window.Session = {
  role: localStorage.getItem('demo-role') || 'viewer',
  setRole: function (r) {
    this.role = r;
    localStorage.setItem('demo-role', r);
  }
};

window.hasPermission = function (perm) {
  return (window.PERMISSIONS[window.Session.role] || []).indexOf(perm) !== -1;
};
