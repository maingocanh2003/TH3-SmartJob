// =============================================
// SmartJob - Candidate Profile & AI CV Extraction
// =============================================

const STATUS_LABELS = { pending: 'Chờ duyệt', reviewing: 'Đang xem xét', reviewed: 'Đã xem', shortlisted: 'Vào vòng trong', interviewed: 'Đã phỏng vấn', accepted: 'Chấp nhận', rejected: 'Từ chối' };
const STATUS_COLORS = {
  pending: 'bg-yellow-100 text-yellow-700',
  reviewing: 'bg-blue-100 text-blue-700',
  reviewed: 'bg-blue-100 text-blue-700',
  shortlisted: 'bg-purple-100 text-purple-700',
  interviewed: 'bg-indigo-100 text-indigo-700',
  accepted: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700'
};

const SAMPLE_CVS = {
  backend: `Họ và tên: Nguyễn Văn An
Email: nguyen.vana@gmail.com
Số điện thoại: 0912345678
Vị trí ứng tuyển: Senior Python Backend Developer
Học vấn: Kỹ sư Công nghệ Thông tin - Đại học Bách Khoa Hà Nội (GPA 3.4/4.0)
Kinh nghiệm: 5 năm kinh nghiệm lập trình backend. Thành thạo Python, Django, FastAPI, PostgreSQL, Docker, Kubernetes, Microservices và thiết kế kiến trúc RESTful API chịu tải cao.
Mục tiêu nghề nghiệp: Phát triển các hệ thống phân tán hiệu năng cao trên nền tảng đám mây AWS.`,

  ai: `Họ và tên: Trần Thị Bích
Email: tran.thib@gmail.com
Số điện thoại: 0987654321
Vị trí ứng tuyển: AI / Machine Learning Engineer
Học vấn: Thạc sĩ Khoa học Máy tính - Đại học Quốc Gia TP. HCM
Kinh nghiệm: 4 năm kinh nghiệm nghiên cứu và phát triển Machine Learning, Deep Learning, Natural Language Processing (NLP), Computer Vision với PyTorch, TensorFlow, Python, Docker và Data Analysis.
Mục tiêu nghề nghiệp: Triển khai các giải pháp AI và hệ thống gợi ý (Recommendation Engine) thực tiễn.`,

  frontend: `Họ và tên: Lê Quốc Việt
Email: le.quocv@gmail.com
Số điện thoại: 0905123456
Vị trí ứng tuyển: Senior Frontend React Developer
Học vấn: Cử nhân Kỹ thuật Phần mềm - Đại học Bách Khoa Đà Nẵng
Kinh nghiệm: 4 năm chuyên sâu xây dựng giao diện người dùng Web với JavaScript, TypeScript, React, Redux, HTML/CSS, Tailwind CSS và tối ưu hóa UI/UX Design, REST API.
Mục tiêu nghề nghiệp: Xây dựng trải nghiệm người dùng mượt mà, trực quan và đạt chuẩn quốc tế.`
};

let candidateId = null;
let candidateData = null;
let selectedFile = null;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[c]);
}

function formatSalary(min, max) {
  const numMin = min !== null && min !== undefined ? Number(min) : null;
  const numMax = max !== null && max !== undefined ? Number(max) : null;
  if (!numMin && !numMax) return 'Thỏa thuận';
  const fmt = v => (v >= 1e6 ? (v / 1e6).toFixed(0) + ' triệu' : v.toLocaleString('vi-VN'));
  if (numMin && numMax) return `${fmt(numMin)} - ${fmt(numMax)} VNĐ`;
  if (numMin) return `Từ ${fmt(numMin)} VNĐ`;
  return `Đến ${fmt(numMax)} VNĐ`;
}

function renderProfile(data) {
  if (!data) return;
  candidateData = data;
  const name = data.full_name || data.name || 'Ứng viên Tiềm năng';
  document.getElementById('profile-name').textContent = name;
  document.getElementById('profile-position').textContent = data.desired_position || data.job_title || 'Chưa xác định vị trí';
  document.getElementById('profile-location').textContent = data.address || data.location || 'Hà Nội / Toàn quốc';

  const salaryVal = data.desired_salary ?? data.expected_salary_max;
  document.getElementById('profile-salary').textContent = formatSalary(null, salaryVal);

  const years = Number(data.years_of_experience);
  const expText = !isNaN(years) && years > 0 ? `${years} năm kinh nghiệm` : (data.years_of_experience == 0 ? 'Mới tốt nghiệp / Fresher' : 'Chưa cập nhật');
  document.getElementById('profile-experience').textContent = expText;

  // Education
  const educations = data.educations || [];
  let eduDegree = 'Đại học / Cử nhân';
  if (educations.length > 0 && educations[0].degree) {
    eduDegree = educations[0].degree;
  } else if (data.education_level) {
    eduDegree = data.education_level;
  }
  document.getElementById('profile-education').textContent = eduDegree;

  // Bio / Summary
  const summary = data.summary || data.bio;
  if (summary) {
    document.getElementById('profile-bio').textContent = `"${summary}"`;
  }

  // Avatar initial
  document.getElementById('avatar-letter').textContent = (name[0] || 'U').toUpperCase();

  // CV File link
  if (data.cv_file_url) {
    const box = document.getElementById('cv-file-link-box');
    const link = document.getElementById('cv-file-link');
    box.classList.remove('hidden');
    link.href = data.cv_file_url.startsWith('http') ? data.cv_file_url : `http://localhost:8000${data.cv_file_url}`;
    const filename = data.cv_file_url.split('/').pop();
    link.textContent = decodeURIComponent(filename);
  }
}

function renderSkills(skills) {
  const list = document.getElementById('skills-list');
  const countBadge = document.getElementById('skills-count-badge');
  const items = skills || [];

  countBadge.textContent = `${items.length} kỹ năng`;

  if (!items.length) {
    list.innerHTML = '<p class="text-xs text-gray-400 py-3">Chưa có kỹ năng. Hãy tải lên file CV để AI trích xuất tự động!</p>';
    return;
  }

  list.innerHTML = items.map(s => {
    const name = s.skill_name || s.name || s.skill || 'Kỹ năng';
    const level = s.proficiency_level || s.level || '';
    const levelBadge = level ? `<span class="text-[10px] opacity-75 font-normal ml-1">(${level})</span>` : '';
    return `
    <span class="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100 hover:bg-blue-100 transition">
      ${escapeHtml(name)} ${levelBadge}
    </span>`;
  }).join('');
}

async function loadCandidateData() {
  const user = getUser();
  candidateId = user && (user.candidate_id || user.id);
  if (!candidateId) {
    showToast('Vui lòng đăng nhập với tài khoản ứng viên', 'error');
    window.location.href = 'login.html';
    return;
  }

  try {
    const data = await apiGet(`/candidates/${candidateId}/`);
    renderProfile(data);
    if (data.skills) {
      renderSkills(data.skills);
    } else {
      loadSkills();
    }
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

function renderRecommendations(jobs) {
  const list = document.getElementById('recs-list');
  if (!jobs || !jobs.length) {
    list.innerHTML = `
      <div class="text-center py-10 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
        <svg class="w-12 h-12 text-gray-300 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        <p class="text-sm font-semibold text-gray-600">Chưa có công việc gợi ý nào</p>
        <p class="text-xs text-gray-400 mt-1">Hãy tải lên bản CV của bạn ở ô trên để AI đối sánh với các tin tuyển dụng!</p>
      </div>`;
    return;
  }

  list.innerHTML = jobs.map((item, idx) => {
    const job = item.job ?? item;
    const jobId = Number(job.id ?? job.job_id);
    const title = job.title ?? job.job_title ?? 'Vị trí tuyển dụng';
    const company = job.company_name || 'Doanh nghiệp';
    const location = job.location || 'Hà Nội';
    const score = Math.round(Number(item.matching_score ?? item.match_score ?? item.score ?? 0));
    const breakdown = item.breakdown || {};
    const details = item.details || {};
    const matchedSkills = details.matched_skills || item.matched_skills || [];
    const missingSkills = details.missing_skills || item.missing_skills || [];
    const reasoning = item.reasoning || item.explanation || '';

    // Level label
    let levelBadge = '';
    if (score >= 75) {
      levelBadge = '<span class="text-xs px-2.5 py-1 rounded-full font-semibold bg-emerald-100 text-emerald-800">Cực kỳ phù hợp</span>';
    } else if (score >= 50) {
      levelBadge = '<span class="text-xs px-2.5 py-1 rounded-full font-semibold bg-blue-100 text-blue-800">Khá phù hợp</span>';
    } else {
      levelBadge = '<span class="text-xs px-2.5 py-1 rounded-full font-semibold bg-amber-100 text-amber-800">Tiềm năng</span>';
    }

    const ringColor = score >= 70 ? 'text-emerald-600' : (score >= 45 ? 'text-blue-600' : 'text-amber-600');
    const bgBadge = score >= 70 ? 'bg-emerald-50 border-emerald-200' : (score >= 45 ? 'bg-blue-50 border-blue-200' : 'bg-amber-50 border-amber-200');

    return `
    <div class="p-5 rounded-2xl border border-gray-100 hover:border-blue-200 hover:shadow-md transition bg-white space-y-3">
      <div class="flex items-start justify-between gap-4">
        <div class="flex items-start gap-3.5 min-w-0">
          <div class="w-12 h-12 rounded-xl gradient-primary flex items-center justify-center text-white font-bold text-lg flex-shrink-0 shadow-sm">
            #${idx + 1}
          </div>
          <div class="min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <h4 class="font-bold text-gray-900 text-base leading-tight">${escapeHtml(title)}</h4>
              ${levelBadge}
            </div>
            <p class="text-sm font-medium text-gray-600 mt-1">${escapeHtml(company)} · <span class="text-gray-400 text-xs">${escapeHtml(location)}</span></p>
          </div>
        </div>

        <!-- Matching Score Circle -->
        <div class="flex-shrink-0 text-center px-4 py-2 rounded-xl border ${bgBadge}">
          <div class="text-2xl font-black ${ringColor}">${score}%</div>
          <div class="text-[10px] font-semibold tracking-wider text-gray-500 uppercase">AI Match</div>
        </div>
      </div>

      <!-- Score Breakdown Bars -->
      <div class="grid grid-cols-3 gap-2 text-xs pt-1">
        <div class="bg-gray-50 p-2 rounded-lg border border-gray-100">
          <span class="text-gray-400 block text-[11px]">Kỹ năng (50%)</span>
          <span class="font-bold text-gray-700">${Math.round(breakdown.skill_match ?? 0)}%</span>
        </div>
        <div class="bg-gray-50 p-2 rounded-lg border border-gray-100">
          <span class="text-gray-400 block text-[11px]">Kinh nghiệm (15%)</span>
          <span class="font-bold text-gray-700">${Math.round(breakdown.experience_match ?? 0)}%</span>
        </div>
        <div class="bg-gray-50 p-2 rounded-lg border border-gray-100">
          <span class="text-gray-400 block text-[11px]">Ngữ nghĩa (20%)</span>
          <span class="font-bold text-gray-700">${Math.round(breakdown.semantic_match ?? 0)}%</span>
        </div>
      </div>

      <!-- Skills Matched / Missing -->
      <div class="flex flex-wrap gap-1.5 text-xs">
        ${matchedSkills.slice(0, 5).map(s => `
          <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
            ✓ ${escapeHtml(typeof s === 'string' ? s : s.skill_name)}
          </span>`).join('')}
        ${missingSkills.slice(0, 3).map(s => `
          <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-amber-50 text-amber-700 border border-amber-200">
            + ${escapeHtml(typeof s === 'string' ? s : s.skill_name)}
          </span>`).join('')}
      </div>

      <!-- AI Reasoning -->
      ${reasoning ? `
      <div class="p-3 bg-purple-50/60 rounded-xl border border-purple-100 text-xs text-purple-900 flex items-start gap-2">
        <span class="text-purple-600 font-bold">🤖 AI:</span>
        <p class="leading-relaxed">${escapeHtml(reasoning)}</p>
      </div>` : ''}

      <!-- Bottom action -->
      <div class="flex items-center justify-between pt-2 border-t border-gray-50">
        <span class="text-xs text-gray-400">${job.salary_min ? formatSalary(job.salary_min, job.salary_max) : 'Lương thỏa thuận'}</span>
        <a href="job-detail.html?id=${jobId}" class="text-xs px-4 py-2 gradient-primary text-white font-medium rounded-lg hover:opacity-90 transition flex items-center gap-1">
          Xem chi tiết & Ứng tuyển &rarr;
        </a>
      </div>
    </div>`;
  }).join('');
}

async function loadRecommendations(preloaded = null) {
  if (preloaded && Array.isArray(preloaded)) {
    renderRecommendations(preloaded);
    return;
  }

  const list = document.getElementById('recs-list');
  list.innerHTML = '<div class="animate-pulse space-y-3"><div class="h-28 bg-gray-100 rounded-2xl"></div><div class="h-28 bg-gray-100 rounded-2xl"></div></div>';

  try {
    const data = await apiGet(`/candidates/${candidateId}/recommendations/`);
    const jobs = data.recommendations ?? data.results ?? data;
    renderRecommendations(jobs);
  } catch (err) {
    list.innerHTML = `<p class="text-center text-red-500 py-4 text-xs">Lỗi tải gợi ý việc làm: ${err.message}</p>`;
  }
}

async function loadApplications() {
  const list = document.getElementById('applications-list');
  try {
    const data = await apiGet('/applications/');
    const apps = data.results ?? data;
    if (!apps.length) {
      list.innerHTML = '<p class="text-xs text-gray-400 text-center py-6">Bạn chưa nộp đơn ứng tuyển nào.</p>';
      return;
    }
    list.innerHTML = apps.slice(0, 5).map(a => `
      <div class="flex items-center gap-4 p-3.5 border border-gray-100 rounded-xl hover:bg-gray-50 transition">
        <div class="flex-1 min-w-0">
          <p class="font-semibold text-sm text-gray-800 truncate">${escapeHtml(a.job_title ?? a.job?.title ?? 'Việc làm')}</p>
          <p class="text-xs text-gray-400 mt-0.5">${new Date(a.applied_at || a.created_at).toLocaleDateString('vi-VN')} · ${escapeHtml(a.company_name || 'Doanh nghiệp')}</p>
        </div>
        <span class="text-xs px-2.5 py-1 rounded-full font-medium ${STATUS_COLORS[a.status] || 'bg-gray-100 text-gray-600'}">
          ${STATUS_LABELS[a.status] || a.status}
        </span>
      </div>`).join('');
  } catch {
    list.innerHTML = '<p class="text-xs text-gray-400">Không thể tải danh sách đơn</p>';
  }
}

// ---- UPLOAD & TRÍCH XUẤT CV ----
async function handleUploadCV(textOverride = null) {
  const progressBox = document.getElementById('upload-progress-box');
  const successBox = document.getElementById('upload-success-box');
  const btn = document.getElementById('btn-upload-cv');

  progressBox.classList.remove('hidden');
  successBox.classList.add('hidden');
  btn.disabled = true;

  try {
    let resp = null;

    if (textOverride) {
      // Dùng CV mẫu
      resp = await apiPost(`/candidates/${candidateId}/upload-cv/`, { cv_text: textOverride });
    } else if (selectedFile) {
      // Dùng file đã chọn
      const fd = new FormData();
      fd.append('cv_file', selectedFile);
      resp = await apiUpload(`/candidates/${candidateId}/upload-cv/`, fd);
    } else {
      progressBox.classList.add('hidden');
      btn.disabled = false;
      showToast('Vui lòng kéo thả file CV hoặc chọn một CV mẫu để tiếp tục', 'warning');
      return;
    }

    progressBox.classList.add('hidden');
    btn.disabled = false;

    // Hiển thị thông báo thành công
    const profile = resp.extracted_profile || {};
    const skills = resp.skills || [];
    const recs = resp.recommendations || [];

    document.getElementById('upload-success-desc').textContent =
      `Đã trích xuất ${skills.length} kỹ năng, số năm kinh nghiệm: ${profile.years_of_experience || 0} năm và tính điểm tương thích với ${recs.length} việc làm.`;
    successBox.classList.remove('hidden');

    // Cập nhật lại giao diện hồ sơ
    renderProfile(resp.candidate);
    renderSkills(skills);
    renderRecommendations(recs);

    showToast('Tải lên và trích xuất hồ sơ bằng AI thành công!', 'success');

    // Cuộn nhẹ tới danh sách việc làm gợi ý
    document.getElementById('recs-list').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (err) {
    progressBox.classList.add('hidden');
    btn.disabled = false;
    showToast('Lỗi trích xuất CV: ' + err.message, 'error');
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  if (!requireLogin()) return;

  await loadCandidateData();
  if (!candidateId) return;

  loadRecommendations();
  loadApplications();

  // Drop zone events
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('cv-file-input');
  const promptView = document.getElementById('drop-zone-prompt');
  const selectedView = document.getElementById('drop-zone-selected');
  const fileNameEl = document.getElementById('selected-file-name');
  const fileSizeEl = document.getElementById('selected-file-size');
  const removeBtn = document.getElementById('btn-remove-file');

  dropZone.addEventListener('click', e => {
    if (e.target !== removeBtn) fileInput.click();
  });

  ['dragenter', 'dragover'].forEach(name => {
    dropZone.addEventListener(name, e => {
      e.preventDefault();
      dropZone.classList.add('border-blue-500', 'bg-blue-50/40');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropZone.addEventListener(name, e => {
      e.preventDefault();
      dropZone.classList.remove('border-blue-500', 'bg-blue-50/40');
    });
  });

  dropZone.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length) {
      selectedFile = files[0];
      displaySelectedFile(selectedFile);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
      selectedFile = fileInput.files[0];
      displaySelectedFile(selectedFile);
    }
  });

  function displaySelectedFile(file) {
    fileNameEl.textContent = file.name;
    const kb = (file.size / 1024).toFixed(1);
    fileSizeEl.textContent = kb > 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`;
    promptView.classList.add('hidden');
    selectedView.classList.remove('hidden');
  }

  removeBtn.addEventListener('click', e => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = '';
    promptView.classList.remove('hidden');
    selectedView.classList.add('hidden');
  });

  // Sample CV buttons
  document.querySelectorAll('.btn-sample-cv').forEach(btn => {
    btn.addEventListener('click', () => {
      const type = btn.dataset.sample;
      const cvText = SAMPLE_CVS[type];
      if (cvText) {
        showToast(`Đã nạp mẫu CV ${type.toUpperCase()} - Đang trích xuất...`, 'info');
        handleUploadCV(cvText);
      }
    });
  });

  // Upload button
  document.getElementById('btn-upload-cv').addEventListener('click', () => {
    handleUploadCV();
  });

  // Refresh recommendations button
  document.getElementById('btn-refresh-recs').addEventListener('click', () => {
    loadRecommendations();
  });
});
