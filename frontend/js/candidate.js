// =============================================
// SmartJob - Candidate Profile Logic
// =============================================

const EXP_LABELS = { entry: 'Mới tốt nghiệp', junior: 'Dưới 2 năm', mid: '2-5 năm', senior: '5+ năm', manager: 'Quản lý' };
const STATUS_LABELS = { pending: 'Chờ duyệt', reviewed: 'Đã xem', accepted: 'Chấp nhận', rejected: 'Từ chối' };
const STATUS_COLORS = { pending: 'bg-yellow-100 text-yellow-700', reviewed: 'bg-blue-100 text-blue-700', accepted: 'bg-green-100 text-green-700', rejected: 'bg-red-100 text-red-700' };

let candidateId = null;
let candidateData = null;
let allSkills = [];

function formatSalary(min, max) {
  if (!min && !max) return 'Thỏa thuận';
  const fmt = v => (v / 1e6).toFixed(0) + ' triệu';
  if (min && max) return `${fmt(min)} - ${fmt(max)} VNĐ`;
  if (min) return `Từ ${fmt(min)} VNĐ`;
  return `Đến ${fmt(max)} VNĐ`;
}

function renderProfile(data) {
  candidateData = data;
  const name = data.full_name || data.name || 'Ứng viên';
  document.getElementById('profile-name').textContent = name;
  document.getElementById('profile-position').textContent = data.desired_position || data.job_title || 'Chưa cập nhật vị trí';
  document.getElementById('profile-location').textContent = data.address || data.location || 'Chưa cập nhật';
  document.getElementById('profile-salary').textContent = formatSalary(null, data.desired_salary ?? data.expected_salary_max);
  const years = Number(data.years_of_experience);
  const experience = years >= 10 ? 'Quản lý' : years >= 5 ? '5+ năm' : years >= 2 ? '2-5 năm' : years > 0 ? 'Dưới 2 năm' : 'Mới tốt nghiệp';
  document.getElementById('profile-experience').textContent = data.years_of_experience == null
    ? 'Chưa cập nhật'
    : experience;
  document.getElementById('avatar-letter').textContent = name[0].toUpperCase();

  // Fill edit form
  document.getElementById('edit-name').value = name;
  document.getElementById('edit-position').value = data.desired_position || data.job_title || '';
  document.getElementById('edit-location').value = data.address || data.location || '';
  document.getElementById('edit-experience').value = years >= 10 ? 'manager' : years >= 5 ? 'senior' : years >= 2 ? 'mid' : years > 0 ? 'junior' : 'entry';
  document.getElementById('edit-salary-min').value = data.desired_salary ?? data.expected_salary_min ?? '';
  document.getElementById('edit-bio').value = data.bio || data.summary || '';
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character]);
}

async function loadCandidateData() {
  const user = getUser();
  candidateId = user && (user.candidate_id || user.id);
  if (!candidateId) { showToast('Không tìm thấy hồ sơ ứng viên', 'error'); return; }

  try {
    const data = await apiGet(`/candidates/${candidateId}/`);
    renderProfile(data);
  } catch (err) {
    showToast('Lỗi tải hồ sơ: ' + err.message, 'error');
  }
}

async function loadSkills() {
  try {
    const data = await apiGet(`/candidates/${candidateId}/skills/`);
    const skills = data.results ?? data;
    renderSkills(skills);
  } catch {}
}

function renderSkills(skills) {
  const list = document.getElementById('skills-list');
  if (!skills.length) {
    list.innerHTML = '<p class="text-sm text-gray-400">Chưa có kỹ năng nào. Hãy thêm kỹ năng để tăng cơ hội được gợi ý!</p>';
    return;
  }
  list.innerHTML = skills.map(s => `
    <span class="skill-badge group flex items-center gap-1.5">
      ${escapeHtml(s.skill_name ?? s.name ?? s.skill)}
      <button onclick="removeSkill(${Number(s.skill) || Number(s.skill_id) || Number(s.id)})" class="opacity-0 group-hover:opacity-100 transition text-blue-400 hover:text-red-500 ml-1">
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"/></svg>
      </button>
    </span>`).join('');
}

async function removeSkill(skillId) {
  try {
    await apiDelete(`/candidates/${candidateId}/skills/${skillId}/`);
    showToast('Đã xóa kỹ năng', 'success');
    loadSkills();
  } catch { showToast('Không thể xóa kỹ năng', 'error'); }
}

async function loadAllSkills() {
  try {
    const data = await apiGet('/skills/');
    allSkills = data.results ?? data;
    const sel = document.getElementById('skill-select');
    sel.innerHTML = '<option value="">-- Chọn kỹ năng --</option>' +
      allSkills.map(s => `<option value="${Number(s.skill_id ?? s.id)}">${escapeHtml(s.skill_name ?? s.name)}</option>`).join('');
  } catch {}
}

async function loadRecommendations() {
  const list = document.getElementById('recs-list');
  list.innerHTML = '<div class="animate-pulse space-y-3"><div class="h-24 bg-gray-100 rounded-xl"></div><div class="h-24 bg-gray-100 rounded-xl"></div></div>';
  try {
    const data = await apiGet(`/candidates/${candidateId}/recommendations/`);
    const jobs = data.recommendations ?? data.results ?? data;
    if (!jobs.length) {
      list.innerHTML = '<p class="text-center text-gray-400 py-8">Chưa có gợi ý nào. Hãy thêm kỹ năng để được gợi ý việc làm!</p>';
      return;
    }
    list.innerHTML = jobs.slice(0, 6).map(item => {
      const job = item.job ?? item;
      const jobId = Number(job.id ?? job.job_id);
      if (!Number.isInteger(jobId) || jobId <= 0) return '';
      const title = job.title ?? job.job_title ?? 'Việc làm';
      const score = item.matching_score ?? item.match_score ?? item.score ?? null;
      const colors = score !== null ? scoreColor(score) : { text: 'text-gray-500', bg: 'bg-gray-100' };
      return `
      <div class="flex items-center gap-4 p-4 border border-gray-100 rounded-xl hover:border-blue-200 hover:bg-blue-50/30 transition">
        <div class="w-10 h-10 gradient-primary rounded-lg flex items-center justify-center text-white font-bold flex-shrink-0">${escapeHtml(title[0] || 'J')}</div>
        <div class="flex-1 min-w-0">
          <p class="font-medium text-gray-800 text-sm truncate">${escapeHtml(title)}</p>
          <p class="text-xs text-gray-500">${escapeHtml(job.company_name || job.location || '')}</p>
        </div>
        ${score !== null ? `<div class="flex-shrink-0 text-center"><div class="text-lg font-bold ${colors.text}">${Number(score).toFixed(1)}%</div><div class="text-xs text-gray-400">Match</div></div>` : ''}
        <div class="flex items-center gap-2 flex-shrink-0">
          ${score === null ? `<button onclick="computeMatch(${jobId}, this)" class="text-xs px-3 py-1.5 text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition">Tính điểm</button>` : ''}
          <a href="job-detail.html?id=${jobId}" class="text-xs px-3 py-1.5 gradient-primary text-white rounded-lg hover:opacity-90 transition">Xem</a>
        </div>
      </div>`;
    }).join('');
  } catch (err) {
    const message = err instanceof TypeError || err.message === 'Failed to fetch'
      ? 'Không kết nối được API. Hãy kiểm tra PostgreSQL và Django backend (localhost:8000), sau đó thử tải lại.'
      : `Lỗi tải gợi ý: ${err.message}`;
    list.replaceChildren();
    const error = document.createElement('p');
    error.className = 'text-center text-red-500 py-4';
    error.textContent = message;
    const retry = document.createElement('button');
    retry.type = 'button';
    retry.className = 'block mx-auto text-sm text-blue-600 hover:text-blue-700 underline';
    retry.textContent = 'Thử lại';
    retry.addEventListener('click', loadRecommendations);
    list.append(error, retry);
  }
}

async function computeMatch(jobId, btn) {
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = '...';
  try {
    const result = await apiPost('/ai/match/', { candidate_id: candidateId, job_id: jobId });
    const score = result.matching_score ?? result.match_score ?? result.score ?? 0;
    const colors = scoreColor(score);
    const container = btn.closest('.flex');
    btn.parentElement.innerHTML = `<div class="text-center"><div class="text-lg font-bold ${colors.text}">${score}%</div><div class="text-xs text-gray-400">Match</div></div>`;
  } catch (err) {
    showToast('Lỗi tính điểm: ' + err.message, 'error');
    btn.disabled = false; btn.textContent = orig;
  }
}

async function loadApplications() {
  const list = document.getElementById('applications-list');
  try {
    const data = await apiGet('/applications/');
    const apps = data.results ?? data;
    if (!apps.length) {
      list.innerHTML = '<p class="text-sm text-gray-400 text-center py-6">Bạn chưa nộp đơn ứng tuyển nào.</p>';
      return;
    }
    list.innerHTML = apps.slice(0, 5).map(a => `
      <div class="flex items-center gap-4 p-3 border border-gray-100 rounded-xl">
        <div class="flex-1 min-w-0">
          <p class="font-medium text-sm text-gray-800 truncate">${a.job_title ?? a.job?.title ?? 'Việc làm'}</p>
          <p class="text-xs text-gray-400">${new Date(a.applied_at || a.created_at).toLocaleDateString('vi-VN')}</p>
        </div>
        <span class="text-xs px-2.5 py-1 rounded-full font-medium ${STATUS_COLORS[a.status] || 'bg-gray-100 text-gray-600'}">${STATUS_LABELS[a.status] || a.status}</span>
      </div>`).join('');
  } catch { list.innerHTML = '<p class="text-sm text-gray-400">Không thể tải danh sách đơn</p>'; }
}

document.addEventListener('DOMContentLoaded', async () => {
  if (!requireLogin()) return;

  await loadCandidateData();
  if (!candidateId) return;

  loadSkills();
  loadRecommendations();
  loadApplications();
  loadAllSkills();

  // Edit profile toggle
  document.getElementById('btn-edit-profile').addEventListener('click', () => {
    document.getElementById('edit-form-section').classList.toggle('hidden');
  });
  document.getElementById('btn-cancel-edit').addEventListener('click', () => {
    document.getElementById('edit-form-section').classList.add('hidden');
  });

  // Save profile
  document.getElementById('form-edit-profile').addEventListener('submit', async e => {
    e.preventDefault();
    const errEl = document.getElementById('edit-error');
    errEl.classList.add('hidden');
    try {
      const experienceYears = { entry: 0, junior: 1, mid: 3, senior: 6, manager: 10 };
      const payload = {
        full_name: document.getElementById('edit-name').value,
        desired_position: document.getElementById('edit-position').value,
        address: document.getElementById('edit-location').value,
        years_of_experience: experienceYears[document.getElementById('edit-experience').value],
        desired_salary: document.getElementById('edit-salary-min').value || null,
        summary: document.getElementById('edit-bio').value,
      };
      const updated = await apiPatch(`/candidates/${candidateId}/`, payload);
      renderProfile(updated);
      document.getElementById('edit-form-section').classList.add('hidden');
      showToast('Cập nhật hồ sơ thành công!', 'success');
    } catch (err) {
      errEl.textContent = err.message; errEl.classList.remove('hidden');
    }
  });

  // Add skill panel
  document.getElementById('btn-add-skill').addEventListener('click', () => {
    document.getElementById('add-skill-panel').classList.toggle('hidden');
  });
  document.getElementById('btn-cancel-skill').addEventListener('click', () => {
    document.getElementById('add-skill-panel').classList.add('hidden');
  });
  document.getElementById('btn-confirm-skill').addEventListener('click', async () => {
    const sel = document.getElementById('skill-select');
    const skillId = sel.value;
    if (!skillId) { showToast('Vui lòng chọn kỹ năng', 'warning'); return; }
    try {
      await apiPost(`/candidates/${candidateId}/skills/`, { skill_id: parseInt(skillId) });
      showToast('Đã thêm kỹ năng!', 'success');
      document.getElementById('add-skill-panel').classList.add('hidden');
      sel.value = '';
      loadSkills();
    } catch (err) { showToast('Lỗi: ' + err.message, 'error'); }
  });

  // Refresh recommendations
  document.getElementById('btn-refresh-recs').addEventListener('click', () => loadRecommendations());
});
