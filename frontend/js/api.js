// =============================================
// SmartJob - API Layer
// =============================================

const API_BASE = 'http://localhost:8000/api';

// ---- Auth Storage ----
function saveUser(data) {
  localStorage.setItem('smartjob_user', JSON.stringify(data));
}
function getUser() {
  try {
    return JSON.parse(localStorage.getItem('smartjob_user')) || null;
  } catch { return null; }
}
function clearUser() {
  localStorage.removeItem('smartjob_user');
}
function isLoggedIn() {
  const u = getUser();
  return !!(u && u.token && u.user_id && u.user_type);
}
function getUserType() {
  const u = getUser();
  return u ? u.user_type : null;
}
function getToken() {
  const u = getUser();
  return u ? u.token : null;
}

// ---- Fetch Wrapper ----
async function _request(method, path, body = null, auth = true) {
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
  const headers = {};
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  if (auth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Token ${token}`;
  }
  const opts = { method, headers };
  if (body !== null) {
    opts.body = isFormData ? body : JSON.stringify(body);
  }

  const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
  const resp = await fetch(url, opts);

  if (!resp.ok) {
    let errMsg = `HTTP ${resp.status}`;
    try {
      const errData = await resp.json();
      errMsg = errData.detail || errData.message || errData.error || JSON.stringify(errData);
    } catch {}
    throw new Error(errMsg);
  }

  // 204 No Content
  if (resp.status === 204) return null;
  return resp.json();
}

const apiGet    = (path, auth = true)             => _request('GET',    path, null, auth);
const apiPost   = (path, body, auth = true)       => _request('POST',   path, body, auth);
const apiPatch  = (path, body, auth = true)       => _request('PATCH',  path, body, auth);
const apiDelete = (path, auth = true)             => _request('DELETE', path, null, auth);
const apiUpload = (path, formData, auth = true)   => _request('POST',   path, formData, auth);

// ---- Matching Score Color ----
function scoreColor(score) {
  if (score >= 70) return { text: 'text-green-600', bg: 'bg-green-100', ring: '#16a34a' };
  if (score >= 40) return { text: 'text-yellow-600', bg: 'bg-yellow-100', ring: '#d97706' };
  return { text: 'text-red-600', bg: 'bg-red-100', ring: '#dc2626' };
}

// ---- Toast Notification ----
function showToast(msg, type = 'success') {
  const colors = {
    success: 'bg-green-600',
    error: 'bg-red-600',
    info: 'bg-blue-600',
    warning: 'bg-yellow-500',
  };
  const t = document.createElement('div');
  t.className = `fixed top-5 right-5 z-50 px-5 py-3 rounded-lg shadow-lg text-white text-sm font-medium transition-all ${colors[type] || colors.info}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 3500);
}

// ---- Navbar update ----
function updateNavbar() {
  const user = getUser();
  const loginLinks = document.querySelectorAll('[data-nav-login]');
  const userMenus  = document.querySelectorAll('[data-nav-user]');
  const userName   = document.querySelectorAll('[data-nav-username]');

  if (isLoggedIn()) {
    loginLinks.forEach(el => el.classList.add('hidden'));
    userMenus.forEach(el => el.classList.remove('hidden'));
    userName.forEach(el => el.textContent = user.full_name || user.email || 'Tài khoản');
  } else {
    loginLinks.forEach(el => el.classList.remove('hidden'));
    userMenus.forEach(el => el.classList.add('hidden'));
  }
}

function handleLogout(e) {
  if (e) e.preventDefault();
  clearUser();
  window.location.href = 'login.html';
}

document.addEventListener('DOMContentLoaded', () => {
  updateNavbar();
  document.querySelectorAll('[data-logout]').forEach(el => el.addEventListener('click', handleLogout));
});
