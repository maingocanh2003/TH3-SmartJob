// =============================================
// SmartJob - Job Detail + AI Matching
// =============================================

const JOB_TYPES = {
  full_time: 'Toàn thời gian',
  'full-time': 'Toàn thời gian',
  part_time: 'Bán thời gian',
  'part-time': 'Bán thời gian',
  contract: 'Hợp đồng',
  internship: 'Thực tập'
};
const EXP_LABELS = { entry: 'Mới tốt nghiệp', junior: 'Dưới 2 năm', mid: '2-5 năm', senior: '5+ năm', manager: 'Quản lý' };
const LEVEL_LABELS = { junior: 'Junior', mid: 'Mid-level', senior: 'Senior', lead: 'Team Lead', manager: 'Manager' };

function formatSalary(min, max) {
  const numMin = min !== null && min !== undefined ? Number(min) : null;
  const numMax = max !== null && max !== undefined ? Number(max) : null;
  if (!numMin && !numMax) return 'Thỏa thuận';
  const fmt = v => v >= 1e6 ? (v / 1e6).toFixed(0) + ' triệu' : v.toLocaleString('vi-VN');
  if (numMin && numMax) return `${fmt(numMin)} - ${fmt(numMax)} VNĐ`;
  if (numMin) return `Từ ${fmt(numMin)} VNĐ`;
  return `Đến ${fmt(numMax)} VNĐ`;
}

function getJobId() {
  return new URLSearchParams(window.location.search).get('id');
}

let jobData = null;

function renderJob(job) {
  jobData = job;
  const company = job.company_detail ?? {};
  const title = job.title ?? job.job_title ?? 'Chi tiết tuyển dụng';
  const rawType = job.job_type ?? job.employment_type ?? '';
  const typeLabel = JOB_TYPES[rawType] || JOB_TYPES[rawType.replace('-', '_')] || rawType;
  const companyName = company.name || job.company_name || '';

  document.title = `${title} - SmartJob`;
  document.getElementById('job-loading').classList.add('hidden');
  document.getElementById('job-content').classList.remove('hidden');

  document.getElementById('company-logo').textContent = (companyName || title || 'J')[0].toUpperCase();
  document.getElementById('job-title').textContent = title;
  document.getElementById('job-company').textContent = companyName;

  const typeBadge = document.getElementById('job-type-badge');
  typeBadge.textContent = typeLabel;

  const statusBadge = document.getElementById('job-status-badge');
  statusBadge.textContent = job.status === 'active' ? 'Đang tuyển' : 'Đã đóng';
  statusBadge.className = `text-xs px-3 py-1 rounded-full font-medium mt-1 ${job.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`;

  document.getElementById('job-location').textContent = job.location || 'Không xác định';
  document.getElementById('job-salary').textContent = formatSalary(job.salary_min, job.salary_max);
  
  const expVal = job.experience_required ?? job.years_of_experience_required;
  const expText = typeof expVal === 'number' ? `${expVal} năm kinh nghiệm` : (EXP_LABELS[expVal] || expVal || 'Không yêu cầu');
  document.getElementById('job-exp').textContent = expText;

  const deadline = job.deadline ?? job.application_deadline;
  if (deadline) {
    document.getElementById('job-deadline').textContent = 'HSD: ' + new Date(deadline).toLocaleDateString('vi-VN');
  }

  document.getElementById('job-description').textContent = job.description ?? job.job_description ?? 'Không có mô tả';
  document.getElementById('job-requirements').textContent = job.requirements || 'Không có yêu cầu cụ thể';

  if (job.benefits) {
    document.getElementById('benefits-section').classList.remove('hidden');
    document.getElementById('job-benefits').textContent = job.benefits;
  }

  // Skills
  const skillsEl = document.getElementById('job-skills');
  const skills = job.skills_required ?? job.skills ?? [];
  skillsEl.innerHTML = skills.length
    ? skills.map(s => `<span class="skill-badge">${typeof s === 'string' ? s : (s.skill_name || s.name || '')}</span>`).join('')
    : '<p class="text-sm text-gray-400">Không có yêu cầu kỹ năng cụ thể</p>';

  // Sidebar info
  document.getElementById('info-type').textContent = typeLabel || '—';
  const levelVal = job.level ?? job.position_level;
  document.getElementById('info-level').textContent = LEVEL_LABELS[levelVal] || levelVal || '—';
  document.getElementById('info-slots').textContent = job.slots ?? job.num_of_positions ? `${job.slots ?? job.num_of_positions} người` : '—';
  document.getElementById('info-deadline').textContent = deadline ? new Date(deadline).toLocaleDateString('vi-VN') : '—';
  document.getElementById('info-industry').textContent = job.industry || job.company_industry || company.industry || '—';

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
    const score = Math.round(result.match_score ?? result.score ?? 0);
    const breakdown = result.breakdown || {};
    const skillScore = Math.round(breakdown.skill_match ?? result.skill_score ?? (score * 0.8));
    const expScore = Math.round(breakdown.experience_match ?? result.experience_score ?? score);
    const salScore = Math.round(breakdown.salary_match ?? result.salary_score ?? score);

    document.getElementById('matching-result').classList.remove('hidden');
    animateScore(score);

    document.getElementById('skill-score').textContent = skillScore + '%';
    document.getElementById('exp-score').textContent = Math.min(expScore, 100) + '%';
    document.getElementById('salary-score').textContent = Math.min(salScore, 100) + '%';

    setTimeout(() => {
      document.getElementById('skill-bar').style.width = Math.min(skillScore, 100) + '%';
      document.getElementById('exp-bar').style.width = Math.min(expScore, 100) + '%';
      document.getElementById('salary-bar').style.width = Math.min(salScore, 100) + '%';
    }, 100);

    // Matched / missing skills
    const details = result.details || {};
    const matched = details.matched_skills ?? result.matched_skills ?? [];
    const missing = details.missing_skills ?? result.missing_skills ?? [];
    if (matched.length || missing.length) {
      document.getElementById('skills-breakdown').innerHTML = `
        ${matched.length ? `<p class="text-xs font-medium text-gray-700 mb-1">Kỹ năng phù hợp:</p><div class="flex flex-wrap gap-1.5">${matched.map(s => `<span class="skill-badge matched text-xs">${typeof s === 'string' ? s : s.skill_name}</span>`).join('')}</div>` : ''}
        ${missing.length ? `<p class="text-xs font-medium text-gray-700 mt-3 mb-1">Kỹ năng còn thiếu:</p><div class="flex flex-wrap gap-1.5">${missing.map(s => `<span class="skill-badge missing text-xs">${typeof s === 'string' ? s : s.skill_name}</span>`).join('')}</div>` : ''}`;
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
