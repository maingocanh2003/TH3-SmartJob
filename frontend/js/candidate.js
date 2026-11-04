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

  // CV File link (Left column & Main Current CV Card)
  const cvUrl = data.cv_file_url;
  const cvBox = document.getElementById('cv-file-link-box');
  const cvLink = document.getElementById('cv-file-link');
  const currentCvName = document.getElementById('current-cv-name');
  const currentCvDesc = document.getElementById('current-cv-desc');
  const currentCvBadge = document.getElementById('current-cv-badge');
  const currentCvActions = document.getElementById('current-cv-actions');
  const btnViewCurrentCv = document.getElementById('btn-view-current-cv');

  if (cvUrl) {
    const resolvedUrl = cvUrl.startsWith('http') ? cvUrl : `http://localhost:8000${cvUrl}`;
    const filename = decodeURIComponent(cvUrl.split('/').pop());

    if (cvBox) cvBox.classList.remove('hidden');
    if (cvLink) {
      cvLink.href = resolvedUrl;
      cvLink.textContent = filename;
    }

    if (currentCvName) currentCvName.textContent = filename;
    if (currentCvDesc) currentCvDesc.textContent = 'Hồ sơ đã được phân tích và đồng bộ kỹ năng với hệ thống AI matching.';
    if (currentCvBadge) currentCvBadge.classList.remove('hidden');
    if (currentCvActions) currentCvActions.classList.remove('hidden');
    if (btnViewCurrentCv) btnViewCurrentCv.href = resolvedUrl;
  } else {
    if (cvBox) cvBox.classList.add('hidden');
    if (currentCvName) currentCvName.textContent = 'Chưa có tệp CV';
    if (currentCvDesc) currentCvDesc.textContent = 'Tải lên tệp CV bên dưới để kích hoạt hồ sơ ứng viên thông minh.';
    if (currentCvBadge) currentCvBadge.classList.add('hidden');
    if (currentCvActions) currentCvActions.classList.add('hidden');
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
function setUploadLoading(isLoading, customMessage = null) {
  const progressBox = document.getElementById('upload-progress-box');
  const progressMsg = document.getElementById('upload-progress-msg');
  const uploadBtns = document.querySelectorAll('#btn-upload-direct, #btn-upload-cv, .btn-sample-cv');

  if (progressBox) {
    if (isLoading) {
      progressBox.classList.remove('hidden');
      if (progressMsg && customMessage) progressMsg.textContent = customMessage;
    } else {
      progressBox.classList.add('hidden');
    }
  }

  uploadBtns.forEach(b => {
    if (b) b.disabled = isLoading;
  });
}

async function handleUploadCV(textOverride = null) {
  const successBox = document.getElementById('upload-success-box');
  if (successBox) successBox.classList.add('hidden');

  if (!candidateId) {
    showToast('Không tìm thấy thông tin ứng viên. Vui lòng đăng nhập lại.', 'error');
    window.location.href = 'login.html';
    return;
  }

  if (!textOverride && !selectedFile) {
    showToast('Vui lòng chọn hoặc kéo thả tệp CV (PDF, DOCX, TXT) trước khi bấm tải lên.', 'warning');
    return;
  }

  setUploadLoading(true, textOverride ? 'Đang nạp mẫu CV và phân tích kỹ năng bằng AI...' : 'Đang gửi tệp CV lên máy chủ và phân tích bằng AI...');

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
    }

    setUploadLoading(false);

    if (!resp) throw new Error('Không nhận được phản hồi từ máy chủ.');

    // Hiển thị thông báo & bảng kết quả trích xuất chi tiết
    const profile = resp.extracted_profile || {};
    const skills = resp.skills || [];
    const recs = resp.recommendations || [];

    // Cập nhật các trường tóm tắt nhận diện
    const posEl = document.getElementById('extracted-position');
    const expEl = document.getElementById('extracted-experience');
    const eduEl = document.getElementById('extracted-education');
    const skillCountEl = document.getElementById('extracted-skills-count');
    const skillTagsEl = document.getElementById('extracted-skills-tags');

    if (posEl) posEl.textContent = profile.desired_position || profile.title || resp.candidate?.desired_position || 'Chuyên viên';
    if (expEl) expEl.textContent = `${profile.years_of_experience ?? resp.candidate?.years_of_experience ?? 0} năm KN`;
    if (eduEl) eduEl.textContent = profile.education_level || resp.candidate?.education_level || 'Đại học / Cử nhân';
    if (skillCountEl) skillCountEl.textContent = `${skills.length} kỹ năng`;

    if (skillTagsEl) {
      if (skills.length > 0) {
        skillTagsEl.innerHTML = skills.map(s => {
          const sName = typeof s === 'string' ? s : (s.skill_name || s.name || s.skill || '');
          return `<span class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">${escapeHtml(sName)}</span>`;
        }).join('');
      } else {
        skillTagsEl.innerHTML = '<span class="text-xs text-emerald-700">Chưa nhận diện thêm kỹ năng cụ thể</span>';
      }
    }

    const successDescEl = document.getElementById('upload-success-desc');
    if (successDescEl) {
      successDescEl.textContent = `Hệ thống đã nhận diện ${skills.length} kỹ năng và tính điểm tương thích với ${recs.length} việc làm.`;
    }
    if (successBox) successBox.classList.remove('hidden');

    // Reset vùng chọn file
    selectedFile = null;
    const fileInp = document.getElementById('cv-file-input');
    if (fileInp) fileInp.value = '';
    const pView = document.getElementById('drop-zone-prompt');
    const sView = document.getElementById('drop-zone-selected');
    if (pView) pView.classList.remove('hidden');
    if (sView) sView.classList.add('hidden');

    // Cập nhật lại giao diện hồ sơ
    if (resp.candidate) renderProfile(resp.candidate);
    renderSkills(skills);
    renderRecommendations(recs);

    showToast('Tải lên và trích xuất hồ sơ bằng AI thành công!', 'success');

    // Cuộn nhẹ tới kết quả
    if (successBox) successBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (err) {
    setUploadLoading(false);
    console.error('Lỗi upload CV:', err);
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

  if (dropZone && fileInput) {
    dropZone.addEventListener('click', e => {
      // Do not trigger fileInput if clicking inside buttons, links, or when a file is already selected
      if (e.target.closest('button') || e.target.closest('a') || e.target.closest('#drop-zone-selected')) {
        return;
      }
      fileInput.click();
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
      const files = e.dataTransfer && e.dataTransfer.files;
      if (files && files.length) {
        selectedFile = files[0];
        displaySelectedFile(selectedFile);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files.length) {
        selectedFile = fileInput.files[0];
        displaySelectedFile(selectedFile);
      }
    });

    function displaySelectedFile(file) {
      if (!file) return;
      if (fileNameEl) fileNameEl.textContent = file.name;
      const kb = (file.size / 1024).toFixed(1);
      if (fileSizeEl) fileSizeEl.textContent = kb > 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`;
      if (promptView) promptView.classList.add('hidden');
      if (selectedView) selectedView.classList.remove('hidden');
    }

    if (removeBtn) {
      removeBtn.addEventListener('click', e => {
        e.stopPropagation();
        selectedFile = null;
        fileInput.value = '';
        if (promptView) promptView.classList.remove('hidden');
        if (selectedView) selectedView.classList.add('hidden');
        fileInput.click();
      });
    }
  }

  // Sample CV buttons
  document.querySelectorAll('.btn-sample-cv').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const type = btn.dataset.sample;
      const cvText = SAMPLE_CVS[type];
      if (cvText) {
        handleUploadCV(cvText);
      }
    });
  });

  // Upload buttons (wire all buttons that could trigger upload)
  document.querySelectorAll('#btn-upload-direct, #btn-upload-cv').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      handleUploadCV();
    });
  });

  const btnScrollRecs = document.getElementById('btn-scroll-recs');
  if (btnScrollRecs) btnScrollRecs.addEventListener('click', (e) => {
    e.preventDefault();
    const recsEl = document.getElementById('recs-list');
    if (recsEl) recsEl.scrollIntoView({ behavior: 'smooth' });
  });

  // Refresh recommendations button
  const btnRefresh = document.getElementById('btn-refresh-recs');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => {
      loadRecommendations();
    });
  }
});
