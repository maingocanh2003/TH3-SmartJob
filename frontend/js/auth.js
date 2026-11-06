// =============================================
// SmartJob - Authentication & Role-Based Access Control
// =============================================

async function login(email, password) {
  const data = await apiPost('/auth/login/', { email, password }, false);
  if (!data.token || !data.user_type || !data.user_id) {
    throw new Error('Phản hồi đăng nhập từ máy chủ không hợp lệ.');
  }
  saveUser(data);
  return data;
}

async function register(email, password, user_type, full_name, company_name) {
  const payload = { email, password, user_type, full_name };
  if (company_name) payload.company_name = company_name;
  const data = await apiPost('/auth/register/', payload, false);
  if (data && data.token && data.user_id) {
    saveUser(data);
  }
  return data;
}

function logout() {
  clearUser();
  window.location.href = 'login.html';
}

function getDefaultPortalForRole(userType) {
  if (userType === 'company' || userType === 'employer') {
    return 'employer-dashboard.html';
  }
  return 'candidate-profile.html';
}

function requireLogin(redirectTo = 'login.html') {
  if (!isLoggedIn()) {
    window.location.href = redirectTo;
    return false;
  }
  return true;
}

function requireUserType(expectedType, fallbackRedirect = null) {
  if (!requireLogin()) return false;
  const currentType = getUserType();
  const allowed = Array.isArray(expectedType) ? expectedType : [expectedType];

  // Admin can access employer dashboard for BI oversight
  if (currentType === 'admin' && allowed.includes('company')) {
    return true;
  }

  if (!allowed.includes(currentType)) {
    const target = fallbackRedirect || getDefaultPortalForRole(currentType);
    showToast(
      currentType === 'company'
        ? 'Tài khoản Nhà tuyển dụng đang được chuyển về trang Quản trị Tuyển dụng.'
        : 'Tài khoản Ứng viên không có quyền truy cập trang Nhà tuyển dụng.',
      'warning'
    );
    setTimeout(() => {
      window.location.href = target;
    }, 300);
    return false;
  }
  return true;
}
