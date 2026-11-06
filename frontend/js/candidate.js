// =========================================================================
// SmartJob - Candidate Portal Logic (frontend/js/candidate.js)
// Hỗ trợ 4 Tab thanh menu bên trái:
//   1. Hồ sơ cá nhân (Upload CV & hiển thị thông tin trích xuất từ CV)
//   2. Gợi ý việc làm (Thẻ việc làm AI Matching + Kỹ năng thiếu & Đề xuất + Nút Ứng tuyển)
//   3. Phân tích hồ sơ AI (Mức độ hoàn thiện, đánh giá kỹ năng/kinh nghiệm & đề xuất cải thiện)
//   4. Ứng tuyển của tôi (Theo dõi danh sách việc làm đã ứng tuyển & trạng thái xử lý)
// =========================================================================

let currentCandidateId = null;
let currentCandidateData = null;
let selectedCvFile = null;
let appliedJobMap = {}; // job_id -> application object
let pendingApplyJob = null; // { job_id, job_title, company_name, matching_score }

const SAMPLE_CVS = {
  backend: `NGUYEN VAN AN
Senior Python Backend Developer
Email: nguyenvanan.dev@gmail.com | Phone: 0912 345 678 | Location: Cau Giay, Ha Noi
Education: Bachelor of Information Technology - Hanoi University of Science and Technology (GPA 3.5/4.0)
Experience: 4 years of software engineering experience

PROFESSIONAL SUMMARY
Experienced Backend Engineer with 4 years building scalable microservices, RESTful APIs, and AI-powered recruitment platforms using Python, Django, FastAPI, PostgreSQL, and Docker.

TECHNICAL SKILLS
- Programming: Python, SQL, JavaScript, TypeScript
- Frameworks: Django, FastAPI, REST API, React
- Databases & Caching: PostgreSQL, Redis, MongoDB
- DevOps & Cloud: Docker, Kubernetes, AWS, Git, Linux, CI/CD
- Data & AI: Machine Learning, NLP, Pandas, Scikit-learn`,

  ai: `TRAN THI BICH
AI & Data Scientist
Email: tranthibich.ai@gmail.com | Phone: 0987 654 321 | Location: Quan 1, TP. Ho Chi Minh
Education: Master of Computer Science & Data Science - VNUHCM University of Science
Experience: 3 years in Machine Learning, Deep Learning & NLP

PROFESSIONAL SUMMARY
Data Scientist & AI Engineer with 3 years of hands-on experience designing NLP pipelines, CV-JD semantic matching models, and BI analytics dashboards using Python, PyTorch, TensorFlow, and SQL.

TECHNICAL SKILLS
- AI & Machine Learning: Machine Learning, Deep Learning, NLP, PyTorch, TensorFlow, Scikit-learn
- Data Engineering & BI: Python, SQL, Pandas, NumPy, Apache Spark, Tableau, Power BI
- Backend & Deployment: FastAPI, Django, REST API, PostgreSQL, Docker, Git`,

  frontend: `LE QUOC VIET
Senior Frontend Engineer (React / Next.js)
Email: lequocviet.fe@gmail.com | Phone: 0905 112 233 | Location: Hai Chau, Da Nang
Education: Bachelor of Software Engineering - Da Nang University of Science and Technology
Experience: 3 years of Frontend & UI/UX Engineering

PROFESSIONAL SUMMARY
Creative Frontend Developer with 3 years of experience building responsive web applications, interactive BI dashboards, and modern design systems using React, TypeScript, Next.js, and Tailwind CSS.

TECHNICAL SKILLS
- Frontend Core: JavaScript, TypeScript, React, Next.js, Vue.js, HTML5, CSS3, Tailwind CSS
- State & APIs: Redux, GraphQL, REST API, Node.js
- Tools & Testing: Git, Docker, Figma, Webpack, Jest`
};

// Safely set textContent on an element if it exists
function safeSetText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

// Safely set value on an input if it exists
function safeSetValue(id, value) {
  const el = document.getElementById(id);
  if (el && 'value' in el) el.value = value ?? '';
}

function escapeHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatViSalary(minVal, maxVal) {
  const fmt = v => v >= 1_000_000 ? `${Math.round(v / 1_000_000)} triệu` : v.toLocaleString('vi-VN');
  if (minVal && maxVal) return `${fmt(minVal)} – ${fmt(maxVal)} VNĐ`;
  if (minVal) return `Từ ${fmt(minVal)} VNĐ`;
  if (maxVal) return `Đến ${fmt(maxVal)} VNĐ`;
  return 'Thỏa thuận';
}

// =========================================================================
// CHUYỂN TAB TRÊN THANH MENU BÊN TRÁI
// =========================================================================
function switchCandidateTab(tabName) {
  const buttons = document.querySelectorAll('.cand-tab-btn');
  const panels = document.querySelectorAll('.cand-tab-panel');

  buttons.forEach(btn => {
    const isTarget = btn.dataset.tabTarget === tabName;
    if (isTarget) {
      btn.className = 'cand-tab-btn w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-bold transition bg-blue-600 text-white shadow-sm';
    } else {
      btn.className = 'cand-tab-btn w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-semibold text-gray-600 hover:bg-gray-100 transition';
    }
  });

  panels.forEach(panel => {
    if (panel.id === `tab-panel-${tabName}`) {
      panel.classList.remove('hidden');
    } else {
      panel.classList.add('hidden');
    }
  });

  // Khi chuyển sang tab, tự động làm mới dữ liệu nếu cần
  if (tabName === 'recommendations' && currentCandidateId) {
    loadRecommendations();
  } else if (tabName === 'ai-analysis' && currentCandidateId) {
    loadAiAnalysis();
  } else if (tabName === 'applications' && currentCandidateId) {
    loadApplications();
  }
}
window.switchCandidateTab = switchCandidateTab;

// =========================================================================
// KHỞI TẠO TRANG ỨNG VIÊN
// =========================================================================
document.addEventListener('DOMContentLoaded', async () => {
  // Kiểm tra đăng nhập & phân quyền
  if (typeof requireUserType === 'function') {
    if (!requireUserType(['candidate'])) return;
  } else if (!isLoggedIn()) {
    window.location.href = 'login.html';
    return;
  }

  const user = getUser();
  currentCandidateId = user?.candidate_id || user?.profile_id || 1;

  // Gắn sự kiện click cho các tab ở thanh menu bên trái
  document.querySelectorAll('.cand-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      switchCandidateTab(btn.dataset.tabTarget);
    });
  });

  // Kiểm tra query param ?tab=...
  const urlParams = new URLSearchParams(window.location.search);
  const initialTab = urlParams.get('tab') || 'profile';

  initCvUploader();
  initApplyModal();

  // Nút làm mới ở các tab
  document.getElementById('btn-refresh-recs')?.addEventListener('click', () => loadRecommendations(true));
  document.getElementById('btn-refresh-analysis')?.addEventListener('click', () => loadAiAnalysis(true));
  document.getElementById('btn-refresh-apps')?.addEventListener('click', () => loadApplications(true));

  // Tải đồng thời Hồ sơ cá nhân + Đơn ứng tuyển + Gợi ý việc làm + Phân tích AI
  await Promise.all([
    loadProfile(),
    loadApplications(),
  ]);
  loadRecommendations();
  loadAiAnalysis();

  if (['profile', 'recommendations', 'ai-analysis', 'applications'].includes(initialTab)) {
    switchCandidateTab(initialTab);
  }
});

// =========================================================================
// TAB 1: TẢI & HIỂN THỊ THÔNG TIN HỒ SƠ CÁ NHÂN (TRÍCH XUẤT TỪ CV)
// =========================================================================
async function loadProfile() {
  try {
    const data = await apiGet(`/candidates/${currentCandidateId}/`);
    currentCandidateData = data;
    renderCandidateProfile(data);
  } catch (err) {
    showToast('Không thể tải hồ sơ ứng viên: ' + err.message, 'error');
  }
}

function renderCandidateProfile(data) {
  const user = getUser();
  const fullName = data.full_name || user?.full_name || 'Ứng viên';
  const position = data.current_position || 'Chưa cập nhật vị trí (Tải CV để trích xuất)';
  const email = data.email || user?.email || 'Chưa có email';
  const phone = data.phone || 'Chưa cập nhật SĐT';
  const location = data.address || 'Chưa cập nhật địa điểm';
  const expYears = data.years_of_experience != null ? `${data.years_of_experience} năm kinh nghiệm` : '0 năm kinh nghiệm';

  // Học vấn
  let eduText = data.education_level || '';
  if (Array.isArray(data.education) && data.education.length > 0) {
    const e0 = data.education[0];
    eduText = [e0.degree, e0.major, e0.school_name].filter(Boolean).join(' · ') || eduText;
  }
  if (!eduText) eduText = 'Chưa cập nhật học vấn (Tải CV để trích xuất)';

  // Sidebar mini card
  safeSetText('avatar-letter', fullName.charAt(0).toUpperCase());
  safeSetText('sidebar-name', fullName);
  safeSetText('sidebar-position', position);

  // Các trường thông tin cá nhân trên Tab 1
  safeSetText('profile-name', fullName);
  safeSetText('profile-position', position);
  safeSetText('profile-email', email);
  safeSetText('profile-phone', phone);
  safeSetText('profile-location', location);
  safeSetText('profile-experience', expYears);
  safeSetText('profile-education', eduText);
  safeSetText('profile-bio', data.summary || 'Chưa có tóm tắt hồ sơ. Hãy tải lên tệp CV để AI tự động trích xuất tóm tắt chuyên môn của bạn.');

  // Đồng bộ các input ẩn tương thích ngược
  safeSetValue('edit-name', fullName);
  safeSetValue('edit-position', data.current_position || '');
  safeSetValue('edit-location', data.address || '');
  safeSetValue('edit-experience', data.years_of_experience ?? 0);
  safeSetValue('edit-bio', data.summary || '');

  // Cập nhật thông tin tệp CV hiện tại
  const cvActions = document.getElementById('current-cv-actions');
  const cvViewBtn = document.getElementById('btn-view-current-cv');
  const cvBadge = document.getElementById('current-cv-badge');
  const cvNameEl = document.getElementById('current-cv-name');
  const cvDescEl = document.getElementById('current-cv-desc');
  const cvLinkBox = document.getElementById('cv-file-link-box');
  const cvLink = document.getElementById('cv-file-link');

  if (data.cv_file_url) {
    const fileUrl = data.cv_file_url.startsWith('http')
      ? data.cv_file_url
      : `http://localhost:8000${data.cv_file_url}`;
    const fileName = decodeURIComponent(data.cv_file_url.split('/').pop());

    cvNameEl && (cvNameEl.textContent = fileName);
    cvDescEl && (cvDescEl.textContent = 'Thông tin cá nhân, kỹ năng và điểm Matching bên dưới được trích xuất trực tiếp từ tệp CV này.');
    cvBadge?.classList.remove('hidden');

    if (cvActions && cvViewBtn) {
      cvViewBtn.href = fileUrl;
      cvActions.classList.remove('hidden');
    }
    if (cvLinkBox && cvLink) {
      cvLink.href = fileUrl;
      cvLink.textContent = fileName;
      cvLinkBox.classList.remove('hidden');
    }
  } else {
    cvNameEl && (cvNameEl.textContent = 'Chưa tải lên tệp CV');
    cvDescEl && (cvDescEl.textContent = 'Hãy tải lên tệp CV (PDF, DOCX, TXT) hoặc chọn CV mẫu bên dưới để AI trích xuất hồ sơ tự động.');
    cvBadge?.classList.add('hidden');
    cvActions?.classList.add('hidden');
    cvLinkBox?.classList.add('hidden');
  }

  // Render danh sách kỹ năng trích xuất từ CV
  renderSkills(data.skills || []);
}

function renderSkills(skills) {
  const container = document.getElementById('skills-list');
  const countBadge = document.getElementById('skills-count-badge');
  if (countBadge) countBadge.textContent = `${skills.length} kỹ năng`;
  if (!container) return;

  if (!skills.length) {
    container.innerHTML = `<p class="text-xs text-gray-400 py-2">Chưa có kỹ năng nào được trích xuất. Hãy tải lên CV của bạn!</p>`;
    return;
  }

  const levelBadge = {
    expert: 'bg-purple-100 text-purple-800 border-purple-200',
    advanced: 'bg-blue-100 text-blue-800 border-blue-200',
    intermediate: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    beginner: 'bg-gray-100 text-gray-700 border-gray-200',
  };

  container.innerHTML = skills.map(s => {
    const name = s.skill_name || s.name || s;
    const level = (s.proficiency_level || s.level || 'intermediate').toLowerCase();
    const cls = levelBadge[level] || levelBadge.intermediate;
    return `
      <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border ${cls}">
        <span>${escapeHtml(name)}</span>
        <span class="text-[10px] opacity-75 font-medium">(${escapeHtml(level)})</span>
      </span>
    `;
  }).join('');
}

// =========================================================================
// UPLOAD CV & TRÍCH XUẤT TỰ ĐỘNG BẰNG AI
// =========================================================================
function initCvUploader() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('cv-file-input');
  const promptBox = document.getElementById('drop-zone-prompt');
  const selectedBox = document.getElementById('drop-zone-selected');
  const fileNameEl = document.getElementById('selected-file-name');
  const fileSizeEl = document.getElementById('selected-file-size');
  const uploadBtn = document.getElementById('btn-upload-direct');
  const removeBtn = document.getElementById('btn-remove-file');

  if (!dropZone || !fileInput) return;

  function showSelectedFile(file) {
    selectedCvFile = file;
    if (fileNameEl) fileNameEl.textContent = file.name;
    if (fileSizeEl) {
      const kb = (file.size / 1024).toFixed(1);
      fileSizeEl.textContent = kb > 1024 ? `${(kb / 1024).toFixed(2)} MB` : `${kb} KB`;
    }
    promptBox?.classList.add('hidden');
    selectedBox?.classList.remove('hidden');
  }

  function clearSelectedFile(e) {
    if (e) e.stopPropagation();
    selectedCvFile = null;
    fileInput.value = '';
    selectedBox?.classList.add('hidden');
    promptBox?.classList.remove('hidden');
  }

  dropZone.addEventListener('click', (e) => {
    if (e.target.closest('#btn-upload-direct') || e.target.closest('#btn-remove-file')) return;
    fileInput.click();
  });

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-blue-500', 'bg-blue-50/40');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-blue-500', 'bg-blue-50/40');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-blue-500', 'bg-blue-50/40');
    const file = e.dataTransfer?.files?.[0];
    if (file) showSelectedFile(file);
  });

  fileInput.addEventListener('change', () => {
    const file = fileInput.files?.[0];
    if (file) showSelectedFile(file);
  });

  removeBtn?.addEventListener('click', clearSelectedFile);

  uploadBtn?.addEventListener('click', async (e) => {
    e.stopPropagation();
    if (!selectedCvFile) {
      showToast('Vui lòng chọn tệp CV trước khi tải lên', 'warning');
      return;
    }
    await submitCvExtraction({ file: selectedCvFile });
    clearSelectedFile();
  });

  // Các nút nạp CV mẫu nhanh
  document.querySelectorAll('.btn-sample-cv').forEach(btn => {
    btn.addEventListener('click', async () => {
      const key = btn.dataset.sample;
      const sampleText = SAMPLE_CVS[key];
      if (!sampleText) return;
      const fileNames = {
        backend: 'CV_Nguyen_Van_An_Python_Backend.txt',
        ai: 'CV_Tran_Thi_Bich_AI_Data_Scientist.txt',
        frontend: 'CV_Le_Quoc_Viet_Frontend_Developer.txt',
      };
      const blob = new Blob([sampleText], { type: 'text/plain;charset=utf-8' });
      const sampleFile = new File([blob], fileNames[key] || 'sample_cv.txt', { type: 'text/plain' });
      await submitCvExtraction({ file: sampleFile, cvText: sampleText });
    });
  });
}

async function submitCvExtraction({ file = null, cvText = '' }) {
  const progressBox = document.getElementById('upload-progress-box');
  const successBox = document.getElementById('upload-success-box');
  const successDesc = document.getElementById('upload-success-desc');

  progressBox?.classList.remove('hidden');
  successBox?.classList.add('hidden');

  try {
    const formData = new FormData();
    if (file) formData.append('cv_file', file);
    if (cvText) formData.append('cv_text', cvText);

    const res = await apiUpload(`/candidates/${currentCandidateId}/upload-cv/`, formData);

    // Cập nhật localStorage nếu tên ứng viên thay đổi từ CV
    const cand = res.candidate || {};
    const user = getUser();
    if (user && cand.full_name) {
      user.full_name = cand.full_name;
      saveUser(user);
      updateNavbar();
    }

    if (cand.candidate_id) {
      currentCandidateData = cand;
      renderCandidateProfile(cand);
    } else {
      await loadProfile();
    }

    // Đồng bộ lại Gợi ý việc làm & Phân tích hồ sơ AI
    await Promise.all([
      loadRecommendations(),
      loadAiAnalysis(),
    ]);

    const skillsCount = (res.extracted_profile?.skills || cand.skills || []).length;
    const jobsMatched = (res.top_recommendations || []).length;
    if (successDesc) {
      successDesc.textContent = `AI đã trích xuất ${skillsCount} kỹ năng chuyên môn, cập nhật thông tin cá nhân và tính toán điểm tương thích với ${jobsMatched} công việc đang tuyển.`;
    }
    progressBox?.classList.add('hidden');
    successBox?.classList.remove('hidden');
    showToast('Đã trích xuất hồ sơ từ CV và tính điểm Matching thành công!', 'success');
  } catch (err) {
    progressBox?.classList.add('hidden');
    showToast('Lỗi tải và trích xuất CV: ' + err.message, 'error');
  }
}

// =========================================================================
// TAB 2: GỢI Ý VIỆC LÀM TỪ AI (MỖI THẺ CÓ CHẤM ĐIỂM MATCHING, KỸ NĂNG THIẾU,
//        ĐỀ XUẤT CẢI THIỆN VÀ NÚT ỨNG TUYỂN NGAY)
// =========================================================================
async function loadRecommendations(showNotification = false) {
  const listEl = document.getElementById('recs-list');
  const badgeEl = document.getElementById('badge-tab-recs');
  if (!listEl) return;

  try {
    const data = await apiGet(`/candidates/${currentCandidateId}/recommendations/`);
    const recs = Array.isArray(data) ? data : (data.results || []);

    if (badgeEl) badgeEl.textContent = recs.length;

    if (!recs.length) {
      listEl.innerHTML = `
        <div class="bg-white rounded-2xl p-10 text-center border border-gray-100">
          <p class="text-base font-bold text-gray-800">Chưa có gợi ý việc làm phù hợp</p>
          <p class="text-xs text-gray-500 mt-1">Hãy tải lên CV ở Tab Hồ sơ cá nhân để AI phân tích và đề xuất công việc phù hợp nhất.</p>
        </div>
      `;
      return;
    }

    listEl.innerHTML = recs.map(r => renderRecommendationCard(r)).join('');

    // Gắn sự kiện cho các nút "Ứng tuyển ngay" trên từng thẻ công việc
    listEl.querySelectorAll('.btn-apply-job-card').forEach(btn => {
      btn.addEventListener('click', () => {
        const jobId = Number(btn.dataset.jobId);
        const jobTitle = btn.dataset.jobTitle;
        const companyName = btn.dataset.companyName;
        const score = Number(btn.dataset.score || 0);
        openApplyModal({ job_id: jobId, job_title: jobTitle, company_name: companyName, matching_score: score });
      });
    });

    if (showNotification) {
      showToast(`Đã cập nhật ${recs.length} việc làm gợi ý từ AI Matching Engine!`, 'info');
    }
  } catch (err) {
    listEl.innerHTML = `
      <div class="bg-white rounded-2xl p-6 text-center border border-red-100 text-red-600 text-xs font-semibold">
        Không thể tải danh sách gợi ý việc làm: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

function renderRecommendationCard(r) {
  const jobId = r.job_id;
  const title = r.job_title || r.title || `Công việc #${jobId}`;
  const company = r.company_name || 'Doanh nghiệp đối tác SmartJob';
  const location = r.location || r.city || 'Việt Nam';
  const empType = r.employment_type || 'full-time';
  const score = Math.round(Number(r.matching_score ?? r.overall_score ?? 0));
  const skillScore = Math.round(Number(r.skill_match_score ?? r.skill_score ?? score));
  const expScore = Math.round(Number(r.experience_match_score ?? r.experience_score ?? score));
  const semanticScore = Math.round(Number(r.semantic_score ?? r.position_score ?? score));

  const matchedSkills = Array.isArray(r.matched_skills) ? r.matched_skills : [];
  const missingSkills = Array.isArray(r.missing_skills) ? r.missing_skills : [];

  // Đề xuất cải thiện kỹ năng cụ thể cho từng thẻ công việc
  let improvementAdvice = '';
  if (missingSkills.length > 0) {
    const topMissing = missingSkills.slice(0, 4).join(', ');
    improvementAdvice = `Bổ sung hoặc làm nổi bật kinh nghiệm thực tế với <strong>${escapeHtml(topMissing)}</strong> trong CV để nâng điểm Matching từ <strong>${score}%</strong> lên trên <strong>${Math.min(98, score + missingSkills.length * 7)}%</strong>.`;
  } else {
    improvementAdvice = `Hồ sơ CV của bạn đã đáp ứng đầy đủ các kỹ năng cốt lõi của vị trí này. Hãy nhấn <strong>Ứng tuyển ngay</strong> để gửi CV tới nhà tuyển dụng!`;
  }

  // Kiểm tra xem ứng viên đã ứng tuyển công việc này chưa
  const existingApp = appliedJobMap[jobId];
  const isApplied = !!existingApp;

  const scoreBadgeClass = score >= 75
    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
    : score >= 50
      ? 'bg-amber-50 text-amber-700 border-amber-200'
      : 'bg-rose-50 text-rose-700 border-rose-200';

  const barColor = score >= 75 ? 'bg-emerald-500' : score >= 50 ? 'bg-amber-500' : 'bg-rose-500';

  return `
    <article class="bg-white rounded-2xl p-6 shadow-xs border border-gray-100 hover:border-blue-200 transition space-y-4">
      <!-- Hàng trên: Thông tin công việc + Điểm AI Matching -->
      <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div class="space-y-1">
          <div class="flex flex-wrap items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-100">${escapeHtml(empType)}</span>
            <span class="text-xs text-gray-400">•</span>
            <span class="text-xs font-semibold text-gray-600">📍 ${escapeHtml(location)}</span>
            ${r.salary_min || r.salary_max ? `<span class="text-xs text-gray-400">•</span><span class="text-xs font-bold text-emerald-700">💰 ${formatViSalary(r.salary_min, r.salary_max)}</span>` : ''}
          </div>
          <h3 class="text-lg font-extrabold text-gray-900">
            <a href="job-detail.html?id=${jobId}" class="hover:text-blue-600 transition">${escapeHtml(title)}</a>
          </h3>
          <p class="text-xs font-semibold text-gray-500">🏢 ${escapeHtml(company)}</p>
        </div>

        <!-- Huy hiệu điểm AI Matching -->
        <div class="flex items-center gap-3 self-start">
          <div class="px-4 py-2.5 rounded-2xl border ${scoreBadgeClass} text-center min-w-[115px]">
            <span class="text-[10px] font-bold uppercase tracking-wider block opacity-80">AI Matching</span>
            <span class="text-2xl font-black">${score}%</span>
          </div>
        </div>
      </div>

      <!-- Thanh phân rã điểm tương thích AI/ML -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 rounded-xl bg-slate-50 border border-gray-100 text-xs">
        <div>
          <div class="flex justify-between font-semibold text-gray-600 mb-1">
            <span>Tương thích Kỹ năng</span>
            <span class="font-bold text-gray-900">${skillScore}%</span>
          </div>
          <div class="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div class="h-full ${barColor} rounded-full" style="width:${Math.min(100, skillScore)}%"></div>
          </div>
        </div>
        <div>
          <div class="flex justify-between font-semibold text-gray-600 mb-1">
            <span>Tương thích Kinh nghiệm</span>
            <span class="font-bold text-gray-900">${expScore}%</span>
          </div>
          <div class="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div class="h-full bg-blue-500 rounded-full" style="width:${Math.min(100, expScore)}%"></div>
          </div>
        </div>
        <div>
          <div class="flex justify-between font-semibold text-gray-600 mb-1">
            <span>Độ khớp Ngữ nghĩa CV-JD</span>
            <span class="font-bold text-gray-900">${semanticScore}%</span>
          </div>
          <div class="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div class="h-full bg-purple-500 rounded-full" style="width:${Math.min(100, semanticScore)}%"></div>
          </div>
        </div>
      </div>

      <!-- Kỹ năng phù hợp & Phát hiện kỹ năng còn thiếu -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div class="p-3.5 rounded-xl bg-emerald-50/60 border border-emerald-100">
          <p class="text-[11px] font-bold text-emerald-800 uppercase tracking-wider mb-2">
            ✓ Kỹ năng phù hợp trong CV (${matchedSkills.length})
          </p>
          <div class="flex flex-wrap gap-1.5">
            ${matchedSkills.length
              ? matchedSkills.map(s => `<span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-white text-emerald-700 border border-emerald-200">✓ ${escapeHtml(s)}</span>`).join('')
              : `<span class="text-xs text-gray-500 italic">Đang đối chiếu kỹ năng...</span>`
            }
          </div>
        </div>

        <div class="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200">
          <p class="text-[11px] font-bold text-amber-900 uppercase tracking-wider mb-2">
            ⚠️ Phát hiện kỹ năng còn thiếu (${missingSkills.length})
          </p>
          <div class="flex flex-wrap gap-1.5">
            ${missingSkills.length
              ? missingSkills.map(s => `<span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-white text-amber-800 border border-amber-300">+ ${escapeHtml(s)}</span>`).join('')
              : `<span class="text-xs font-semibold text-emerald-700">🎉 Hồ sơ của bạn không thiếu kỹ năng yêu cầu nào!</span>`
            }
          </div>
        </div>
      </div>

      <!-- Đề xuất kỹ năng cần cải thiện & Nút Ứng Tuyển Ngay -->
      <div class="pt-3 border-t border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div class="flex items-start gap-2.5 text-xs text-gray-700 bg-indigo-50/60 border border-indigo-100 px-3.5 py-2.5 rounded-xl flex-1">
          <span class="text-base leading-none mt-0.5">💡</span>
          <div>
            <span class="font-bold text-indigo-900">Đề xuất cải thiện từ AI: </span>
            <span>${improvementAdvice}</span>
          </div>
        </div>

        <div class="flex items-center gap-2.5 flex-shrink-0">
          <a href="job-detail.html?id=${jobId}" class="px-3.5 py-2.5 rounded-xl border border-gray-200 text-xs font-bold text-gray-600 hover:bg-gray-50 transition">
            Chi tiết JD
          </a>
          ${isApplied
            ? `<button type="button" onclick="switchCandidateTab('applications')" class="px-4 py-2.5 rounded-xl bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs font-extrabold flex items-center gap-1.5">
                 <span>✓ Đã ứng tuyển (${escapeHtml(existingApp.status_label || 'Đã tiếp nhận')})</span>
               </button>`
            : `<button type="button"
                 class="btn-apply-job-card px-5 py-2.5 rounded-xl gradient-primary text-white text-xs font-extrabold hover:opacity-95 transition shadow-sm flex items-center gap-1.5"
                 data-job-id="${jobId}"
                 data-job-title="${escapeHtml(title)}"
                 data-company-name="${escapeHtml(company)}"
                 data-score="${score}">
                 <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>
                 <span>Ứng tuyển ngay</span>
               </button>`
          }
        </div>
      </div>
    </article>
  `;
}

// =========================================================================
// MODAL XÁC NHẬN & NỘP ĐƠN ỨNG TUYỂN TRỰC TIẾP TRÊN THẺ CÔNG VIỆC
// =========================================================================
function initApplyModal() {
  const modal = document.getElementById('apply-modal');
  const closeBtn = document.getElementById('btn-close-apply-modal');
  const cancelBtn = document.getElementById('btn-cancel-apply');
  const confirmBtn = document.getElementById('btn-confirm-apply');

  const closeModal = () => {
    modal?.classList.add('hidden');
    pendingApplyJob = null;
  };

  closeBtn?.addEventListener('click', closeModal);
  cancelBtn?.addEventListener('click', closeModal);

  confirmBtn?.addEventListener('click', async () => {
    if (!pendingApplyJob) return;
    const coverLetter = document.getElementById('modal-apply-cover-letter')?.value?.trim() || '';
    const originalText = confirmBtn.innerHTML;
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = `<span>Đang phân tích AI & gửi hồ sơ...</span>`;

    try {
      const created = await apiPost('/applications/', {
        candidate_id: currentCandidateId,
        job_id: pendingApplyJob.job_id,
        cover_letter: coverLetter || `Ứng tuyển vị trí ${pendingApplyJob.job_title} bằng hồ sơ CV đã trích xuất trên hệ thống SmartJob AI.`,
      });

      appliedJobMap[pendingApplyJob.job_id] = created;
      closeModal();
      showToast(`Ứng tuyển vị trí "${pendingApplyJob.job_title}" thành công!`, 'success');

      // Cập nhật lại danh sách Gợi ý việc làm & Tab Ứng tuyển của tôi
      await Promise.all([
        loadApplications(),
        loadRecommendations(),
      ]);
    } catch (err) {
      showToast('Không thể gửi hồ sơ ứng tuyển: ' + err.message, 'error');
    } finally {
      confirmBtn.disabled = false;
      confirmBtn.innerHTML = originalText;
    }
  });
}

function openApplyModal({ job_id, job_title, company_name, matching_score }) {
  pendingApplyJob = { job_id, job_title, company_name, matching_score };
  safeSetText('modal-apply-job-title', job_title);
  safeSetText('modal-apply-company', company_name);
  safeSetText('modal-apply-score', `${matching_score}%`);
  const coverEl = document.getElementById('modal-apply-cover-letter');
  if (coverEl) {
    coverEl.value = `Kính gửi Ban Tuyển dụng ${company_name},\nTôi xin ứng tuyển vị trí ${job_title}. Hồ sơ CV của tôi đạt độ tương thích AI Matching ${matching_score}% với mô tả công việc.`;
  }
  document.getElementById('apply-modal')?.classList.remove('hidden');
}

// =========================================================================
// TAB 3: PHÂN TÍCH HỒ SƠ AI (AI CV ANALYSIS & IMPROVEMENT SUGGESTIONS)
// =========================================================================
async function loadAiAnalysis(showNotification = false) {
  try {
    const data = await apiGet(`/candidates/${currentCandidateId}/ai-analysis/`);
    renderAiAnalysis(data);
    if (showNotification) {
      showToast('Đã cập nhật kết quả Phân tích hồ sơ AI!', 'info');
    }
  } catch (err) {
    console.warn('AI Analysis error:', err);
  }
}

function renderAiAnalysis(data) {
  if (!data) return;

  const comp = data.completeness || {};
  const exp = data.experience_analysis || {};
  const matchOv = data.matching_overview || {};
  const skillAn = data.skill_analysis || {};
  const suggestions = Array.isArray(data.improvement_suggestions) ? data.improvement_suggestions : [];

  const compScore = Math.round(Number(comp.score ?? 0));
  safeSetText('analysis-completeness-score', `${compScore}%`);
  safeSetText('analysis-completeness-level', comp.level || 'Khá');
  safeSetText('badge-tab-analysis', `${compScore}%`);

  const compBar = document.getElementById('analysis-completeness-bar');
  if (compBar) compBar.style.width = `${Math.min(100, compScore)}%`;

  safeSetText('analysis-exp-years', `${exp.years_of_experience ?? 0} năm`);
  safeSetText('analysis-seniority', `${exp.seniority_level || 'Junior'} · ${exp.current_position || 'Ứng viên'}`);
  safeSetText('analysis-exp-compare', `Trung bình thị trường yêu cầu: ${exp.market_avg_required_years ?? 2} năm kinh nghiệm.`);

  safeSetText('analysis-best-match', `${Math.round(Number(matchOv.best_matching_score ?? 0))}%`);
  safeSetText('analysis-high-match-count', `${matchOv.high_match_jobs_count ?? 0}/${matchOv.total_active_jobs ?? 0} công việc tương thích cao (≥70%)`);
  safeSetText('analysis-avg-match', `Điểm tương thích trung bình trên toàn thị trường: ${Math.round(Number(matchOv.average_matching_score ?? 0))}%`);

  // Checklist mức độ hoàn thiện hồ sơ
  const checklistEl = document.getElementById('analysis-checklist');
  if (checklistEl && Array.isArray(comp.checklist)) {
    checklistEl.innerHTML = comp.checklist.map(item => `
      <div class="flex items-center justify-between p-3 rounded-xl border ${item.done ? 'bg-emerald-50/50 border-emerald-200' : 'bg-amber-50/50 border-amber-200'}">
        <div class="flex items-center gap-2.5">
          <span class="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${item.done ? 'bg-emerald-600 text-white' : 'bg-amber-500 text-white'}">
            ${item.done ? '✓' : '!'}
          </span>
          <span class="text-xs font-semibold ${item.done ? 'text-gray-800' : 'text-amber-900'}">${escapeHtml(item.label)}</span>
        </div>
        <span class="text-[11px] font-bold ${item.done ? 'text-emerald-700' : 'text-amber-700'}">
          ${item.done ? `+${item.weight}%` : `Thiếu (+${item.weight}%)`}
        </span>
      </div>
    `).join('');
  }

  // Kỹ năng theo nhóm chuyên môn
  const catEl = document.getElementById('analysis-skills-by-cat');
  if (catEl) {
    const byCat = skillAn.by_category || {};
    const entries = Object.entries(byCat);
    if (!entries.length) {
      catEl.innerHTML = `<p class="text-xs text-gray-400 italic">Chưa có dữ liệu nhóm kỹ năng.</p>`;
    } else {
      catEl.innerHTML = entries.map(([cat, names]) => `
        <div class="p-3 rounded-xl bg-slate-50 border border-gray-100">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs font-bold text-gray-700">${escapeHtml(cat)}</span>
            <span class="text-[11px] font-semibold text-blue-600">${names.length} kỹ năng</span>
          </div>
          <div class="flex flex-wrap gap-1.5">
            ${names.map(n => `<span class="px-2.5 py-0.5 rounded-lg text-[11px] font-semibold bg-white border border-gray-200 text-gray-800">${escapeHtml(n)}</span>`).join('')}
          </div>
        </div>
      `).join('');
    }
  }

  // Kỹ năng thị trường cần nhưng CV còn thiếu
  const missingMarketEl = document.getElementById('analysis-missing-market-skills');
  if (missingMarketEl) {
    const missingList = Array.isArray(skillAn.missing_market_skills) ? skillAn.missing_market_skills : [];
    if (!missingList.length) {
      missingMarketEl.innerHTML = `<span class="text-xs font-semibold text-emerald-700">🎉 Hồ sơ của bạn đã bao phủ hầu hết các kỹ năng trọng tâm trên thị trường!</span>`;
    } else {
      missingMarketEl.innerHTML = missingList.map(m => `
        <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-amber-50 text-amber-900 border border-amber-200">
          <span>+ ${escapeHtml(m.skill_name)}</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded-md bg-amber-200/70 text-amber-900">${m.job_demand_count} tin cần</span>
        </span>
      `).join('');
    }
  }

  // Đề xuất cải thiện hồ sơ từ AI
  const sugEl = document.getElementById('analysis-suggestions-list');
  if (sugEl) {
    const priorityStyles = {
      high: { badge: 'bg-rose-100 text-rose-800', border: 'border-rose-200 bg-rose-50/30', label: 'Ưu tiên cao' },
      medium: { badge: 'bg-amber-100 text-amber-800', border: 'border-amber-200 bg-amber-50/30', label: 'Khuyến nghị' },
      low: { badge: 'bg-emerald-100 text-emerald-800', border: 'border-emerald-200 bg-emerald-50/30', label: 'Tối ưu thêm' },
    };
    sugEl.innerHTML = suggestions.map(s => {
      const st = priorityStyles[s.priority] || priorityStyles.medium;
      return `
        <div class="p-4 rounded-2xl border ${st.border} space-y-2">
          <div class="flex items-center justify-between gap-2">
            <span class="text-xs font-extrabold text-gray-900">${escapeHtml(s.title)}</span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${st.badge}">${st.label}</span>
          </div>
          <p class="text-xs text-gray-600 leading-relaxed">${escapeHtml(s.detail)}</p>
          ${s.impact ? `<p class="text-[11px] font-bold text-blue-700">🚀 Tác động: ${escapeHtml(s.impact)}</p>` : ''}
        </div>
      `;
    }).join('');
  }
}

// =========================================================================
// TAB 4: ỨNG TUYỂN CỦA TÔI (ĐỒNG BỘ TRẠNG THÁI VỚI NHÀ TUYỂN DỤNG)
// =========================================================================
const APPLICATION_STATUS_META = {
  pending: {
    label: 'Đã tiếp nhận',
    badge: 'bg-amber-100 text-amber-800 border-amber-200',
    step: 1,
  },
  reviewing: {
    label: 'Đang xem xét',
    badge: 'bg-blue-100 text-blue-800 border-blue-200',
    step: 2,
  },
  shortlisted: {
    label: 'Đang xem xét',
    badge: 'bg-blue-100 text-blue-800 border-blue-200',
    step: 2,
  },
  interviewed: {
    label: 'Mời phỏng vấn',
    badge: 'bg-purple-100 text-purple-800 border-purple-200',
    step: 3,
  },
  offered: {
    label: 'Trúng tuyển',
    badge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    step: 4,
  },
  rejected: {
    label: 'Từ chối',
    badge: 'bg-rose-100 text-rose-800 border-rose-200',
    step: -1,
  },
};

async function loadApplications(showNotification = false) {
  const listEl = document.getElementById('applications-list');
  const badgeEl = document.getElementById('badge-tab-apps');
  if (!listEl) return;

  try {
    const data = await apiGet(`/applications/?candidate_id=${currentCandidateId}`);
    const apps = Array.isArray(data) ? data : (data.results || []);

    // Lưu vào appliedJobMap để đồng bộ trạng thái nút "Ứng tuyển" ở Tab 2
    appliedJobMap = {};
    const counts = { pending: 0, reviewing: 0, interviewed: 0, offered: 0, rejected: 0 };

    apps.forEach(a => {
      if (a.job_id) appliedJobMap[a.job_id] = a;
      const st = (a.status || 'pending').toLowerCase();
      if (st === 'pending') counts.pending++;
      else if (st === 'reviewing' || st === 'shortlisted') counts.reviewing++;
      else if (st === 'interviewed') counts.interviewed++;
      else if (st === 'offered') counts.offered++;
      else if (st === 'rejected') counts.rejected++;
    });

    safeSetText('badge-tab-apps', apps.length);
    safeSetText('app-stat-pending', counts.pending);
    safeSetText('app-stat-reviewing', counts.reviewing);
    safeSetText('app-stat-interviewed', counts.interviewed);
    safeSetText('app-stat-offered', counts.offered);
    safeSetText('app-stat-rejected', counts.rejected);

    if (!apps.length) {
      listEl.innerHTML = `
        <div class="bg-white rounded-2xl p-10 text-center border border-gray-100 space-y-3">
          <p class="text-base font-bold text-gray-800">Bạn chưa ứng tuyển công việc nào</p>
          <p class="text-xs text-gray-500">Hãy chuyển sang tab <strong>Gợi ý việc làm</strong> để xem các công việc phù hợp với CV và nhấn <strong>Ứng tuyển ngay</strong>.</p>
          <button type="button" onclick="switchCandidateTab('recommendations')" class="px-5 py-2.5 gradient-primary text-white rounded-xl text-xs font-bold">
            Khám phá việc làm gợi ý &rarr;
          </button>
        </div>
      `;
      return;
    }

    listEl.innerHTML = apps.map(a => renderApplicationItem(a)).join('');
    if (showNotification) {
      showToast('Đã đồng bộ trạng thái hồ sơ ứng tuyển mới nhất từ Nhà tuyển dụng!', 'info');
    }
  } catch (err) {
    listEl.innerHTML = `
      <div class="bg-white rounded-2xl p-6 text-center border border-red-100 text-red-600 text-xs font-semibold">
        Không thể tải danh sách đơn ứng tuyển: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

function renderApplicationItem(app) {
  const st = (app.status || 'pending').toLowerCase();
  const meta = APPLICATION_STATUS_META[st] || APPLICATION_STATUS_META.pending;
  const statusLabel = app.status_label || meta.label;
  const appliedDate = app.applied_at ? new Date(app.applied_at).toLocaleDateString('vi-VN') : '';
  const updatedDate = app.updated_at ? new Date(app.updated_at).toLocaleDateString('vi-VN') : '';
  const aiScore = app.ai_match?.matching_score != null ? Math.round(app.ai_match.matching_score) : null;

  // Thanh tiến trình 4 bước (hoặc hiển thị trạng thái Từ chối)
  const steps = [
    { idx: 1, name: 'Đã tiếp nhận' },
    { idx: 2, name: 'Đang xem xét' },
    { idx: 3, name: 'Mời phỏng vấn' },
    { idx: 4, name: 'Trúng tuyển' },
  ];

  let pipelineHtml = '';
  if (st === 'rejected') {
    pipelineHtml = `
      <div class="mt-3 p-3 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-between text-xs text-rose-800">
        <span class="font-bold">⚠️ Trạng thái quy trình: Nhà tuyển dụng đã từ chối hồ sơ</span>
        <span>Cập nhật: ${escapeHtml(updatedDate || appliedDate)}</span>
      </div>
    `;
  } else {
    pipelineHtml = `
      <div class="mt-4 pt-3 border-t border-gray-100 grid grid-cols-4 gap-2">
        ${steps.map(s => {
          const active = meta.step >= s.idx;
          const current = meta.step === s.idx;
          return `
            <div class="flex flex-col items-center text-center">
              <div class="w-full h-1.5 rounded-full mb-1.5 ${active ? 'bg-blue-600' : 'bg-gray-200'}"></div>
              <span class="text-[11px] font-bold ${current ? 'text-blue-700' : active ? 'text-gray-800' : 'text-gray-400'}">
                ${active ? '✓ ' : ''}${s.name}
              </span>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  return `
    <div class="bg-white rounded-2xl p-6 shadow-xs border border-gray-100 hover:border-blue-200 transition">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <h3 class="text-base font-extrabold text-gray-900">
              <a href="job-detail.html?id=${app.job_id}" class="hover:text-blue-600 transition">${escapeHtml(app.job_title || `Công việc #${app.job_id}`)}</a>
            </h3>
            ${aiScore != null ? `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200">AI Match: ${aiScore}%</span>` : ''}
          </div>
          <p class="text-xs font-semibold text-gray-500 mt-0.5">
            🏢 ${escapeHtml(app.company_name || 'Doanh nghiệp')}
            ${app.job_location ? ` · 📍 ${escapeHtml(app.job_location)}` : ''}
            · 📅 Ngày nộp: ${escapeHtml(appliedDate)}
          </p>
        </div>

        <div class="flex items-center gap-2 self-start sm:self-center">
          <span class="px-3.5 py-1.5 rounded-full text-xs font-extrabold border ${meta.badge}">
            ${escapeHtml(statusLabel)}
          </span>
        </div>
      </div>

      ${app.notes ? `
        <div class="mt-3 p-3 rounded-xl bg-blue-50/60 border border-blue-100 text-xs text-blue-900">
          <span class="font-bold">💬 Phản hồi từ Nhà tuyển dụng:</span> ${escapeHtml(app.notes)}
        </div>
      ` : ''}

      ${pipelineHtml}
    </div>
  `;
}
