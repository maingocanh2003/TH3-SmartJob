// =============================================
// SmartJob - Job Detail + AI Matching
// =============================================

const JOB_TYPES = { full_time: 'Toàn thời gian', part_time: 'Bán thời gian', contract: 'Hợp đồng', internship: 'Thực tập' };
const EXP_LABELS = { entry: 'Mới tốt nghiệp', junior: 'Dưới 2 năm', mid: '2-5 năm', senior: '5+ năm', manager: 'Quản lý' };
const LEVEL_LABELS = { junior: 'Junior', mid: 'Mid-level', senior: 'Senior', lead: 'Team Lead', manager: 'Manager' };

function formatSalary(min, max) {
  if (!min && !max) return 'Thỏa thuận';
  const fmt = v => v >= 1e6 ? (v / 1e6).toFixed(0) + 'M' : v.toLocaleString('vi-VN');
  if (min && max) return `${fmt(min)} - ${fmt(max)} VNĐ`;
  if (min) return `Từ ${fmt(min)} VNĐ`;
  return `Đến ${fmt(max)} VNĐ`;
}

function getJobId() {
  return new URLSearchParams(window.location.search).get('id');
}

let jobData = null;

function renderJob(job) {
  jobData = job;
  const company = job.company_detail ?? {};

  document.title = `${job.title} - SmartJob`;
  document.getElementById('job-loading').classList.add('hidden');
  document.getElementById('job-content').classList.remove('hidden');

  document.getElementById('company-logo').textContent = (company.name || job.title || 'J')[0].toUpperCase();
  document.getElementById('job-title').textContent = job.title;
  document.getElementById('job-company').textContent = company.name || job.company_name || '';

  const typeBadge = document.getElementById('job-type-badge');
  typeBadge.textContent = JOB_TYPES[job.job_type] || job.job_type || '';

  const statusBadge = document.getElementById('job-status-badge');
  statusBadge.textContent = job.status === 'active' ? 'Đang tuyển' : 'Đã đóng';
  statusBadge.className = `text-xs px-3 py-1 rounded-full font-medium mt-1 ${job.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`;

  document.getElementById('job-location').insertAdjacentText('beforeend', job.location || 'Không xác định');
  document.getElementById('job-salary').insertAdjacentText('beforeend', formatSalary(job.salary_min, job.salary_max));
  document.getElementById('job-exp').insertAdjacentText('beforeend', EXP_LABELS[job.experience_required] || job.experience_required || 'Không yêu cầu');

  if (job.deadline) {
    document.getElementById('job-deadline').insertAdjacentText('beforeend', 'HSD: ' + new Date(job.deadline).toLocaleDateString('vi-VN'));
  }

  document.getElementById('job-description').textContent = job.description || 'Không có mô tả';
  document.getElementById('job-requirements').textContent = job.requirements || 'Không có yêu cầu cụ thể';

  if (job.benefits) {
    document.getElementById('benefits-section').classList.remove('hidden');
    document.getElementById('job-benefits').textContent = job.benefits;
  }

  // Skills
  const skillsEl = document.getElementById('job-skills');
  const skills = job.skills_required ?? [];
  skillsEl.innerHTML = skills.length
    ? skills.map(s => `<span class="skill-badge">${s.name ?? s}</span>`).join('')
    : '<p class="text-sm text-gray-400">Không có yêu cầu kỹ năng cụ thể</p>';

  // Sidebar info
  document.getElementById('info-type').textContent = JOB_TYPES[job.job_type] || job.job_type || '—';
  document.getElementById('info-level').textContent = LEVEL_LABELS[job.level] || job.level || '—';
  document.getElementById('info-slots').textContent = job.slots ? `${job.slots} người` : '—';
  document.getElementById('info-deadline').textContent = job.deadline ? new Date(job.deadline).toLocaleDateString('vi-VN') : '—';
  document.getElementById('info-industry').textContent = job.industry || company.industry || '—';

  // Apply section
  const user = getUser();
  if (!user || !user.token) {
    document.getElementById('form-apply').classList.add('hidden');
    document.getElementById('apply-login-prompt').classList.remove('hidden');
  }

  // Matching score card
  if (user && user.token && user.user_type === 'candidate') {
    document.getElementById('matching-login-prompt').classList.add('hidden');
    document.getElementById('btn-calc-score').classList.remove('hidden');
  }
}

function animateScore(score) {
  const colors = scoreColor(score);
  const circle = document.getElementById('score-circle');
  const numEl = document.getElementById('score-number');

  circle.setAttribute('stroke-dasharray', `${score} 100`);
  circle.style.stroke = colors.ring;
  numEl.textContent = score + '%';
  numEl.className = `text-2xl font-bold ${colors.text}`;
}

async function calculateMatchingScore() {
  const user = getUser();
  const candidateId = user.candidate_id || user.id;
  const jobId = getJobId();
  const btn = document.getElementById('btn-calc-score');

  btn.disabled = true;
  btn.innerHTML = '<svg class="animate-spin w-4 h-4 inline mr-2" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>Đang tính...';

  try {
    const result = await apiPost('/ai/match/', { candidate_id: candidateId, job_id: parseInt(jobId) });
    const score = result.match_score ?? result.score ?? 0;
    const skillScore = result.skill_score ?? result.skill_match ?? Math.round(score * 0.8);
    const expScore = result.experience_score ?? result.exp_match ?? Math.round(score * 1.1);
    const salScore = result.salary_score ?? result.salary_match ?? Math.round(score * 0.9);

    document.getElementById('matching-result').classList.remove('hidden');
    animateScore(score);

    document.getElementById('skill-score').textContent = skillScore + '%';
    document.getElementById('exp-score').textContent = Math.min(expScore, 100) + '%';
    document.getElementById('salary-score').textContent = Math.min(salScore, 100) + '%';

    setTimeout(() => {
      document.getElementById('skill-bar').style.width = skillScore + '%';
      document.getElementById('exp-bar').style.width = Math.min(expScore, 100) + '%';
      document.getElementById('salary-bar').style.width = Math.min(salScore, 100) + '%';
    }, 100);

    // Matched / missing skills
    const matched = result.matched_skills ?? [];
    const missing = result.missing_skills ?? [];
    if (matched.length || missing.length) {
      document.getElementById('skills-breakdown').innerHTML = `
        ${matched.length ? `<p class="text-xs font-medium text-gray-700 mb-1">Kỹ năng phù hợp:</p><div class="flex flex-wrap gap-1.5">${matched.map(s => `<span class="skill-badge matched text-xs">${s}</span>`).join('')}</div>` : ''}
        ${missing.length ? `<p class="text-xs font-medium text-gray-700 mt-3 mb-1">Kỹ năng còn thiếu:</p><div class="flex flex-wrap gap-1.5">${missing.map(s => `<span class="skill-badge missing text-xs">${s}</span>`).join('')}</div>` : ''}`;
    }

    btn.textContent = 'Tính lại';
    btn.disabled = false;
  } catch (err) {
    showToast('Lỗi tính điểm: ' + err.message, 'error');
    btn.textContent = 'Tính Matching Score';
    btn.disabled = false;
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const jobId = getJobId();
  if (!jobId) { window.location.href = 'index.html'; return; }

  try {
    const job = await apiGet(`/jobs/${jobId}/`, false);
    renderJob(job);
  } catch (err) {
    document.getElementById('job-loading').innerHTML = `<div class="text-center py-20 text-red-400"><p>Lỗi tải dữ liệu: ${err.message}</p><a href="index.html" class="mt-4 inline-block text-blue-600 hover:underline">Về trang chủ</a></div>`;
  }

  document.getElementById('btn-apply-top').addEventListener('click', () => {
    document.getElementById('apply-section').scrollIntoView({ behavior: 'smooth' });
  });

  document.getElementById('btn-calc-score').addEventListener('click', calculateMatchingScore);

  document.getElementById('form-apply').addEventListener('submit', async e => {
    e.preventDefault();
    const errEl = document.getElementById('apply-error');
    const sucEl = document.getElementById('apply-success');
    errEl.classList.add('hidden'); sucEl.classList.add('hidden');

    if (!isLoggedIn()) {
      window.location.href = 'login.html'; return;
    }
    const user = getUser();
    const candidateId = user.candidate_id || user.id;

    try {
      await apiPost('/applications/', {
        job: parseInt(jobId),
        candidate: candidateId,
        cover_letter: document.getElementById('cover-letter').value,
      });
      sucEl.textContent = 'Nộp đơn thành công! Chúc bạn may mắn 🎉';
      sucEl.classList.remove('hidden');
      document.getElementById('form-apply').reset();
    } catch (err) {
      errEl.textContent = err.message || 'Nộp đơn thất bại. Có thể bạn đã ứng tuyển vị trí này rồi.';
      errEl.classList.remove('hidden');
    }
  });
});
