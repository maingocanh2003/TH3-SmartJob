// =============================================
// SmartJob - Authentication Module
// =============================================
// This file supplements api.js auth helpers with login/register/logout logic.

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
  return data;
}

function logout() {
  clearUser();
  window.location.href = 'login.html';
}

function requireLogin(redirectTo = 'login.html') {
  if (!isLoggedIn()) {
    window.location.href = redirectTo;
    return false;
  }
  return true;
}

function requireUserType(type, redirectTo = 'index.html') {
  if (getUserType() !== type) {
    window.location.href = redirectTo;
    return false;
  }
  return true;
}
