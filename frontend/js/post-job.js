// =============================================
// SmartJob - Post Job Logic
// =============================================

let selectedSkillIds = [];
let allSkills = [];
let currentStep = 1;

const JOB_TYPES = { full_time: 'Toàn thời gian', part_time: 'Bán thời gian', contract: 'Hợp đồng', internship: 'Thực tập' };
const EXP_LABELS = { entry: 'Mới tốt nghiệp', junior: 'Dưới 2 năm', mid: '2-5 năm', senior: '5+ năm', manager: 'Quản lý' };
const LEVEL_LABELS = { junior: 'Junior', mid: 'Mid-level', senior: 'Senior', lead: 'Team Lead', manager: 'Manager' };

function goToStep(n) {
  [1, 2, 3].forEach(i => {
    document.getElementById(`step${i}`).classList.toggle('hidden', i !== n);
    const circle = document.getElementById(`step${i}-circle`);
    const label = document.getElementById(`step${i}-label`);
    if (circle && label) {
      if (i < n) {
        circle.className = 'w-8 h-8 rounded-full bg-green-500 flex items-center justify-center text-white text-sm font-bold';
        circle.innerHTML = '✓';
        label.className = 'text-sm font-medium text-green-600';
      } else if (i === n) {
        circle.className = 'w-8 h-8 rounded-full gradient-primary flex items-center justify-center text-white text-sm font-bold';
        circle.textContent = i;
        label.className = 'text-sm font-medium text-blue-600';
      } else {
        circle.className = 'w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 text-sm font-bold';
        circle.textContent = i;
        label.className = 'text-sm font-medium text-gray-400';
      }
    }
  });
  currentStep = n;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function getFormData() {
  return {
    title: document.getElementById('job-title-input').value.trim(),
    job_type: document.getElementById('job-type').value,
    level: document.getElementById('job-level').value,
    location: document.getElementById('job-location').value.trim(),
    industry: document.getElementById('job-industry').value.trim(),
    salary_min: document.getElementById('salary-min').value || null,
    salary_max: document.getElementById('salary-max').value || null,
    slots: document.getElementById('job-slots').value || 1,
    deadline: document.getElementById('job-deadline').value || null,
    description: document.getElementById('job-desc').value.trim(),
    experience_required: document.getElementById('job-exp').value,
    requirements: document.getElementById('job-req').value.trim(),
    benefits: document.getElementById('job-benefits').value.trim(),
  };
}

function renderPreview() {
  const d = getFormData();
  const skillNames = selectedSkillIds.map(id => {
    const s = allSkills.find(sk => sk.id === id);
    return s ? s.name : id;
  });

  document.getElementById('preview-content').innerHTML = `
    <div class="grid grid-cols-2 gap-4">
      <div><span class="font-medium text-gray-500">Tiêu đề:</span><p class="text-gray-800 font-semibold text-base">${d.title}</p></div>
      <div><span class="font-medium text-gray-500">Loại hình:</span><p>${JOB_TYPES[d.job_type] || d.job_type}</p></div>
      <div><span class="font-medium text-gray-500">Cấp bậc:</span><p>${LEVEL_LABELS[d.level] || d.level}</p></div>
      <div><span class="font-medium text-gray-500">Địa điểm:</span><p>${d.location || '—'}</p></div>
      <div><span class="font-medium text-gray-500">Ngành:</span><p>${d.industry || '—'}</p></div>
      <div><span class="font-medium text-gray-500">Lương:</span><p>${d.salary_min && d.salary_max ? (parseInt(d.salary_min)/1e6).toFixed(0)+'M - '+(parseInt(d.salary_max)/1e6).toFixed(0)+'M VNĐ' : 'Thỏa thuận'}</p></div>
      <div><span class="font-medium text-gray-500">Số lượng:</span><p>${d.slots} người</p></div>
      <div><span class="font-medium text-gray-500">Hạn nộp:</span><p>${d.deadline ? new Date(d.deadline).toLocaleDateString('vi-VN') : '—'}</p></div>
    </div>
    <div class="border-t pt-4"><span class="font-medium text-gray-500">Mô tả:</span><p class="mt-1 whitespace-pre-wrap text-gray-700">${d.description}</p></div>
    ${d.requirements ? `<div class="border-t pt-4"><span class="font-medium text-gray-500">Yêu cầu:</span><p class="mt-1 whitespace-pre-wrap text-gray-700">${d.requirements}</p></div>` : ''}
    ${d.benefits ? `<div class="border-t pt-4"><span class="font-medium text-gray-500">Quyền lợi:</span><p class="mt-1 whitespace-pre-wrap text-gray-700">${d.benefits}</p></div>` : ''}
    ${skillNames.length ? `<div class="border-t pt-4"><span class="font-medium text-gray-500">Kỹ năng yêu cầu:</span><div class="flex flex-wrap gap-2 mt-2">${skillNames.map(s => `<span class="skill-badge">${s}</span>`).join('')}</div></div>` : ''}
  `;
}

async function loadSkills() {
  try {
    const data = await apiGet('/skills/', false);
    allSkills = data.results ?? data;
    const sel = document.getElementById('skill-selector');
    sel.innerHTML = '<option value="">-- Chọn kỹ năng --</option>' +
      allSkills.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  } catch { showToast('Không tải được danh sách kỹ năng', 'warning'); }
}

function renderSelectedSkills() {
  const container = document.getElementById('selected-skills');
  if (!selectedSkillIds.length) {
    container.innerHTML = '<span class="text-xs text-gray-400">Chưa chọn kỹ năng nào</span>';
    return;
  }
  container.innerHTML = selectedSkillIds.map(id => {
    const s = allSkills.find(sk => sk.id === id);
    return `<span class="skill-badge flex items-center gap-1.5">${s ? s.name : id}
      <button onclick="removeSkillFromList(${id})" class="text-blue-400 hover:text-red-500">
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"/></svg>
      </button>
    </span>`;
  }).join('');
}

function removeSkillFromList(id) {
  selectedSkillIds = selectedSkillIds.filter(s => s !== id);
  renderSelectedSkills();
}

document.addEventListener('DOMContentLoaded', async () => {
  if (!requireLogin()) return;
  // requireUserType('company', 'index.html'); // Uncomment for strict role check

  loadSkills();

  // Navigation
  document.getElementById('btn-next-1').addEventListener('click', () => {
    const title = document.getElementById('job-title-input').value.trim();
    const desc = document.getElementById('job-desc').value.trim();
    if (!title) { showToast('Vui lòng nhập tiêu đề công việc', 'warning'); return; }
    if (!desc) { showToast('Vui lòng nhập mô tả công việc', 'warning'); return; }
    goToStep(2);
  });

  document.getElementById('btn-back-1').addEventListener('click', () => goToStep(1));

  document.getElementById('btn-next-2').addEventListener('click', () => {
    renderPreview();
    goToStep(3);
  });

  document.getElementById('btn-back-2').addEventListener('click', () => goToStep(2));

  // Add skill
  document.getElementById('btn-add-skill').addEventListener('click', () => {
    const sel = document.getElementById('skill-selector');
    const id = parseInt(sel.value);
    if (!id) { showToast('Vui lòng chọn kỹ năng', 'warning'); return; }
    if (selectedSkillIds.includes(id)) { showToast('Kỹ năng này đã được chọn', 'info'); return; }
    selectedSkillIds.push(id);
    sel.value = '';
    renderSelectedSkills();
  });

  // Post job
  document.getElementById('btn-post').addEventListener('click', async () => {
    const btn = document.getElementById('btn-post');
    const errEl = document.getElementById('post-error');
    errEl.classList.add('hidden');

    const d = getFormData();
    if (!d.title) { showToast('Tiêu đề không được để trống', 'error'); return; }

    const user = getUser();
    const companyId = user.company_id;

    const payload = {
      ...d,
      company: companyId,
      status: 'active',
    };
    if (d.salary_min) payload.salary_min = parseInt(d.salary_min);
    if (d.salary_max) payload.salary_max = parseInt(d.salary_max);
    if (d.slots) payload.slots = parseInt(d.slots);

    btn.disabled = true;
    btn.innerHTML = '<svg class="animate-spin w-5 h-5 inline mr-2" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>Đang đăng...';

    try {
      const newJob = await apiPost('/jobs/', payload);
      // Add skills to the job
      if (selectedSkillIds.length) {
        for (const skillId of selectedSkillIds) {
          try { await apiPost(`/jobs/${newJob.id}/skills/`, { skill_id: skillId }); } catch {}
        }
      }
      showToast('Đăng tin tuyển dụng thành công!', 'success');
      setTimeout(() => window.location.href = `employer-dashboard.html`, 1000);
    } catch (err) {
      errEl.textContent = err.message || 'Đăng tin thất bại, vui lòng thử lại';
      errEl.classList.remove('hidden');
      btn.disabled = false;
      btn.innerHTML = '<svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Đăng tin';
    }
  });
});
