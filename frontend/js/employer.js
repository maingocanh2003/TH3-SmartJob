// =========================================================================
// SmartJob - Employer Portal & BI Dashboard Logic (frontend/js/employer.js)
// Hỗ trợ 4 Tab thanh menu bên trái của Nhà tuyển dụng:
//   1. Dashboard BI (4 KPIs + Biểu đồ thống kê theo thời gian + Nhúng Apache Superset)
//   2. Quản lý tin tuyển dụng (Tạo, đăng, chỉnh sửa, gia hạn và xóa tin tuyển dụng)
//   3. Quản lý hồ sơ ứng viên (Xem danh sách & thông tin chi tiết ứng viên đã ứng tuyển)
//   4. Quản lý quy trình tuyển dụng (Cập nhật: Đã tiếp nhận, Đang xem xét, Mời phỏng vấn,
//      Trúng tuyển, Từ chối — đồng bộ tức thì sang trang Ứng viên)
// =========================================================================

let currentCompanyId = null;
let allCompanyJobs = [];
let allApplications = [];

const PIPELINE_STAGES = [
  { code: 'pending',     label: 'Đã tiếp nhận',  badge: 'bg-amber-100 text-amber-800 border-amber-200',   btn: 'hover:bg-amber-50 hover:border-amber-300 text-amber-800' },
  { code: 'reviewing',   label: 'Đang xem xét',  badge: 'bg-blue-100 text-blue-800 border-blue-200',      btn: 'hover:bg-blue-50 hover:border-blue-300 text-blue-800' },
  { code: 'interviewed', label: 'Mời phỏng vấn', badge: 'bg-purple-100 text-purple-800 border-purple-200', btn: 'hover:bg-purple-50 hover:border-purple-300 text-purple-800' },
  { code: 'offered',     label: 'Trúng tuyển',   badge: 'bg-emerald-100 text-emerald-800 border-emerald-200', btn: 'hover:bg-emerald-50 hover:border-emerald-300 text-emerald-800' },
  { code: 'rejected',    label: 'Từ chối',       badge: 'bg-rose-100 text-rose-800 border-rose-200',      btn: 'hover:bg-rose-50 hover:border-rose-300 text-rose-800' },
];

function getStageMeta(status) {
  const norm = (status || 'pending').toLowerCase();
  if (norm === 'shortlisted') return PIPELINE_STAGES[1];
  return PIPELINE_STAGES.find(s => s.code === norm) || PIPELINE_STAGES[0];
}

function escapeHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function safeSetText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function formatViSalary(minVal, maxVal) {
  const fmt = v => v >= 1_000_000 ? `${Math.round(v / 1_000_000)} triệu` : Number(v).toLocaleString('vi-VN');
  if (minVal && maxVal) return `${fmt(minVal)} – ${fmt(maxVal)} VNĐ`;
  if (minVal) return `Từ ${fmt(minVal)} VNĐ`;
  if (maxVal) return `Đến ${fmt(maxVal)} VNĐ`;
  return 'Thỏa thuận';
}

// =========================================================================
// CHUYỂN TAB TRÊN THANH MENU BÊN TRÁI
// =========================================================================
function switchEmployerTab(tabName) {
  document.querySelectorAll('.emp-tab-btn').forEach(btn => {
    const isTarget = btn.dataset.empTab === tabName;
    if (isTarget) {
      btn.className = 'emp-tab-btn w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-bold transition bg-blue-600 text-white shadow-sm';
    } else {
      btn.className = 'emp-tab-btn w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-semibold text-gray-600 hover:bg-gray-100 transition';
    }
  });

  document.querySelectorAll('.emp-tab-panel').forEach(panel => {
    if (panel.id === `emp-panel-${tabName}`) {
      panel.classList.remove('hidden');
    } else {
      panel.classList.add('hidden');
    }
  });

  if (tabName === 'bi') {
    loadBiDashboard();
  } else if (tabName === 'jobs') {
    loadCompanyJobs();
  } else if (tabName === 'candidates' || tabName === 'pipeline') {
    loadCompanyApplications();
  }
}
window.switchEmployerTab = switchEmployerTab;

// =========================================================================
// KHỞI TẠO TRANG NHÀ TUYỂN DỤNG
// =========================================================================
document.addEventListener('DOMContentLoaded', async () => {
  if (typeof requireUserType === 'function') {
    if (!requireUserType(['company', 'admin'])) return;
  } else if (!isLoggedIn()) {
    window.location.href = 'login.html';
    return;
  }

  const user = getUser();
  currentCompanyId = user?.company_id || user?.profile_id || 1;
  const companyName = user?.full_name || 'FPT Software';

  safeSetText('emp-sidebar-name', companyName);
  safeSetText('emp-avatar-letter', companyName.charAt(0).toUpperCase());

  // Gắn sự kiện click cho các tab ở thanh menu bên trái
  document.querySelectorAll('.emp-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchEmployerTab(btn.dataset.empTab));
  });

  // Gắn sự kiện làm mới BI & Superset iframe
  document.getElementById('btn-refresh-bi')?.addEventListener('click', () => loadBiDashboard(true));
  document.getElementById('btn-reload-superset')?.addEventListener('click', () => {
    const iframe = document.getElementById('superset-iframe');
    if (iframe) {
      iframe.src = iframe.src;
      showToast('Đang tải lại bảng điều khiển Apache Superset...', 'info');
    }
  });

  // Bộ lọc tin tuyển dụng
  document.getElementById('job-filter-search')?.addEventListener('input', renderCompanyJobs);
  document.getElementById('job-filter-status')?.addEventListener('change', renderCompanyJobs);

  // Bộ lọc ứng viên & quy trình
  document.getElementById('cand-filter-job')?.addEventListener('change', renderCandidateProfiles);
  document.getElementById('pipeline-filter-status')?.addEventListener('change', renderRecruitmentPipeline);

  initJobModal();
  initExtendJobModal();
  initCandidateDetailModal();

  // Tải đồng thời dữ liệu cho cả 4 tab
  await Promise.all([
    loadBiDashboard(),
    loadCompanyJobs(),
    loadCompanyApplications(),
  ]);

  const urlParams = new URLSearchParams(window.location.search);
  const initialTab = urlParams.get('tab');
  if (['bi', 'jobs', 'candidates', 'pipeline'].includes(initialTab)) {
    switchEmployerTab(initialTab);
  }
});

// =========================================================================
// TAB 1: DASHBOARD BI (4 CHỈ SỐ KPI + BIỂU ĐỒ THỜI GIAN + APACHE SUPERSET)
// =========================================================================
async function loadBiDashboard(showNotification = false) {
  try {
    const data = await apiGet('/bi/overview/');

    safeSetText('bi-kpi-active-jobs', data.active_jobs ?? 0);
    safeSetText('bi-kpi-total-apps', data.total_applications ?? 0);
    safeSetText('bi-kpi-pending-apps', data.pending_applications ?? 0);
    safeSetText('bi-kpi-hiring-rate', `${data.hiring_success_rate ?? 0}%`);
    safeSetText('bi-kpi-hiring-sub', `${data.accepted_applications ?? 0} ứng viên trúng tuyển / ${data.total_applications ?? 0} hồ sơ`);

    renderTimeSeriesChart(data.applications_over_time || []);
    renderStatusBreakdown(data.status_breakdown || [], data.total_applications || 0);

    if (showNotification) {
      showToast('Đã cập nhật số liệu Dashboard BI mới nhất!', 'info');
    }
  } catch (err) {
    console.warn('BI Overview load error:', err);
  }
}

function renderTimeSeriesChart(series) {
  const container = document.getElementById('bi-timeseries-chart');
  const summaryEl = document.getElementById('bi-timeseries-summary');
  if (!container) return;

  if (!series.length) {
    container.innerHTML = `<p class="text-xs text-gray-400 m-auto">Chưa có dữ liệu chuỗi thời gian.</p>`;
    return;
  }

  const maxCount = Math.max(...series.map(d => Number(d.applications_count || 0)), 1);
  const totalInPeriod = series.reduce((acc, d) => acc + Number(d.applications_count || 0), 0);

  if (summaryEl) {
    summaryEl.textContent = `Tổng ${totalInPeriod} hồ sơ trong ${series.length} mốc thời gian gần nhất`;
  }

  container.innerHTML = series.map(item => {
    const count = Number(item.applications_count || 0);
    const hired = Number(item.hired_count || 0);
    const heightPct = Math.max(14, Math.round((count / maxCount) * 100));
    const hiredPct = count > 0 ? Math.max(8, Math.round((hired / maxCount) * 100)) : 0;

    return `
      <div class="flex-1 flex flex-col items-center justify-end h-full group">
        <div class="text-[11px] font-extrabold text-blue-700 mb-1">${count}</div>
        <div class="w-full max-w-[44px] flex items-end justify-center gap-1 h-40">
          <div class="flex-1 bg-gradient-to-t from-blue-600 to-indigo-500 rounded-t-lg transition-all duration-300 group-hover:opacity-90"
               style="height: ${heightPct}%"
               title="Ngày ${escapeHtml(item.label)}: ${count} hồ sơ ứng tuyển"></div>
          ${hired > 0 ? `
            <div class="w-2.5 bg-emerald-500 rounded-t-md"
                 style="height: ${hiredPct}%"
                 title="Trúng tuyển: ${hired} hồ sơ"></div>
          ` : ''}
        </div>
        <span class="text-[11px] font-bold text-gray-600 mt-2">${escapeHtml(item.label || item.date)}</span>
      </div>
    `;
  }).join('');
}

function renderStatusBreakdown(breakdown, totalApps) {
  const container = document.getElementById('bi-status-breakdown');
  if (!container) return;

  const colorMap = {
    pending: 'bg-amber-500',
    reviewing: 'bg-blue-500',
    shortlisted: 'bg-indigo-500',
    interviewed: 'bg-purple-500',
    offered: 'bg-emerald-500',
    rejected: 'bg-rose-500',
  };

  if (!breakdown.length) {
    container.innerHTML = `<p class="text-xs text-gray-400">Chưa có dữ liệu trạng thái hồ sơ.</p>`;
    return;
  }

  container.innerHTML = breakdown.map(item => {
    const count = Number(item.count || 0);
    const pct = totalApps > 0 ? Math.round((count / totalApps) * 100) : 0;
    const barCls = colorMap[item.status] || 'bg-blue-500';
    return `
      <div>
        <div class="flex items-center justify-between text-xs mb-1">
          <span class="font-bold text-gray-700">${escapeHtml(item.label)}</span>
          <span class="font-extrabold text-gray-900">${count} hồ sơ (${pct}%)</span>
        </div>
        <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <div class="h-full ${barCls} rounded-full transition-all duration-500" style="width: ${Math.max(4, pct)}%"></div>
        </div>
      </div>
    `;
  }).join('');
}

// =========================================================================
// TAB 2: QUẢN LÝ TIN TUYỂN DỤNG (TẠO, ĐĂNG, CHỈNH SỬA, GIA HẠN, XÓA)
// =========================================================================
async function loadCompanyJobs() {
  try {
    const data = await apiGet(`/jobs/?company_id=${currentCompanyId}`);
    let jobs = Array.isArray(data) ? data : (data.results || []);
    // Nếu company hiện tại chưa có tin riêng, hiển thị toàn bộ tin trên hệ thống để dễ quản trị demo
    if (!jobs.length) {
      const allData = await apiGet('/jobs/');
      jobs = Array.isArray(allData) ? allData : (allData.results || []);
    }
    allCompanyJobs = jobs;
    safeSetText('emp-badge-jobs', allCompanyJobs.length);
    populateJobFilterSelect();
    renderCompanyJobs();
  } catch (err) {
    showToast('Không thể tải danh sách tin tuyển dụng: ' + err.message, 'error');
  }
}

function populateJobFilterSelect() {
  const selectEl = document.getElementById('cand-filter-job');
  if (!selectEl) return;
  const currentVal = selectEl.value;
  selectEl.innerHTML = `<option value="">Tất cả vị trí tuyển dụng (${allCompanyJobs.length})</option>` +
    allCompanyJobs.map(j => `<option value="${j.job_id}">${escapeHtml(j.job_title)}</option>`).join('');
  selectEl.value = currentVal;
}

function renderCompanyJobs() {
  const listEl = document.getElementById('emp-jobs-list');
  const summaryEl = document.getElementById('jobs-count-summary');
  if (!listEl) return;

  const q = (document.getElementById('job-filter-search')?.value || '').trim().toLowerCase();
  const statusFilter = document.getElementById('job-filter-status')?.value || '';

  const filtered = allCompanyJobs.filter(j => {
    const matchText = !q ||
      (j.job_title || '').toLowerCase().includes(q) ||
      (j.location || '').toLowerCase().includes(q);
    const matchStatus = !statusFilter || (j.status || 'active') === statusFilter;
    return matchText && matchStatus;
  });

  if (summaryEl) summaryEl.textContent = `Hiển thị ${filtered.length} / ${allCompanyJobs.length} tin tuyển dụng`;

  if (!filtered.length) {
    listEl.innerHTML = `
      <div class="bg-white rounded-2xl p-10 text-center border border-gray-100">
        <p class="text-base font-bold text-gray-800">Chưa có tin tuyển dụng nào khớp bộ lọc</p>
        <p class="text-xs text-gray-500 mt-1">Nhấn nút "Tạo & Đăng Tin Tuyển Dụng Mới" để đăng tin tuyển dụng đầu tiên.</p>
      </div>
    `;
    return;
  }

  const statusBadgeMap = {
    active: { label: 'Đang hoạt động', cls: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
    closed: { label: 'Đã đóng',        cls: 'bg-gray-100 text-gray-700 border-gray-200' },
    draft:  { label: 'Bản nháp',       cls: 'bg-amber-100 text-amber-800 border-amber-200' },
  };

  listEl.innerHTML = filtered.map(job => {
    const st = statusBadgeMap[job.status || 'active'] || statusBadgeMap.active;
    const deadline = job.application_deadline || 'Chưa đặt hạn';
    const skills = Array.isArray(job.skills) ? job.skills : [];
    const appCount = allApplications.filter(a => Number(a.job_id) === Number(job.job_id)).length;

    return `
      <div class="bg-white rounded-2xl p-6 shadow-xs border border-gray-100 hover:border-blue-200 transition space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <span class="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold border ${st.cls}">${st.label}</span>
              <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700">${escapeHtml(job.employment_type || 'full-time')}</span>
              <span class="text-xs font-semibold text-gray-500">📍 ${escapeHtml(job.location || 'Việt Nam')}</span>
              <span class="text-xs font-bold text-emerald-700">💰 ${formatViSalary(job.salary_min, job.salary_max)}</span>
            </div>
            <h3 class="text-lg font-extrabold text-gray-900 mt-1">${escapeHtml(job.job_title)}</h3>
            <p class="text-xs text-gray-500 mt-0.5">
              ⏳ Hạn nộp hồ sơ: <strong class="text-gray-800">${escapeHtml(deadline)}</strong>
              · 👥 Đã nhận: <strong class="text-blue-600">${appCount} hồ sơ ứng tuyển</strong>
              · Kinh nghiệm yêu cầu: <strong>${job.required_experience ?? 0} năm</strong>
            </p>
          </div>

          <!-- Cụm nút Tạo/Đăng, Chỉnh sửa, Gia hạn, Xóa -->
          <div class="flex flex-wrap items-center gap-2 self-start">
            <button type="button" class="btn-edit-job px-3 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 text-xs font-bold transition"
              data-job-id="${job.job_id}">
              ✏️ Chỉnh sửa
            </button>
            <button type="button" class="btn-extend-job px-3 py-2 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs font-bold transition"
              data-job-id="${job.job_id}" data-job-title="${escapeHtml(job.job_title)}" data-deadline="${escapeHtml(job.application_deadline || '')}">
              ⏳ Gia hạn
            </button>
            <button type="button" class="btn-toggle-job-status px-3 py-2 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 text-xs font-bold transition"
              data-job-id="${job.job_id}" data-status="${job.status || 'active'}">
              ${(job.status || 'active') === 'active' ? '⏸ Đóng tin' : '▶ Đăng lại'}
            </button>
            <button type="button" class="btn-delete-job px-3 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-bold transition"
              data-job-id="${job.job_id}" data-job-title="${escapeHtml(job.job_title)}">
              🗑 Xóa
            </button>
          </div>
        </div>

        <p class="text-xs text-gray-600 line-clamp-2 bg-slate-50 p-3 rounded-xl border border-gray-100">
          ${escapeHtml(job.job_description || 'Chưa có mô tả chi tiết.')}
        </p>

        ${skills.length ? `
          <div class="flex flex-wrap items-center gap-1.5">
            <span class="text-[11px] font-bold text-gray-400 mr-1">Kỹ năng yêu cầu:</span>
            ${skills.map(s => `<span class="px-2.5 py-0.5 rounded-lg text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">${escapeHtml(s.skill_name || s)}</span>`).join('')}
          </div>
        ` : ''}
      </div>
    `;
  }).join('');

  // Sự kiện Chỉnh sửa tin
  listEl.querySelectorAll('.btn-edit-job').forEach(btn => {
    btn.addEventListener('click', () => {
      const job = allCompanyJobs.find(j => Number(j.job_id) === Number(btn.dataset.jobId));
      if (job) openJobModal(job);
    });
  });

  // Sự kiện Gia hạn tin
  listEl.querySelectorAll('.btn-extend-job').forEach(btn => {
    btn.addEventListener('click', () => {
      openExtendJobModal({
        job_id: Number(btn.dataset.jobId),
        job_title: btn.dataset.jobTitle,
        deadline: btn.dataset.deadline,
      });
    });
  });

  // Sự kiện Đóng / Đăng lại tin
  listEl.querySelectorAll('.btn-toggle-job-status').forEach(btn => {
    btn.addEventListener('click', async () => {
      const jobId = Number(btn.dataset.jobId);
      const nextStatus = btn.dataset.status === 'active' ? 'closed' : 'active';
      try {
        await apiPatch(`/jobs/${jobId}/`, { status: nextStatus });
        showToast(nextStatus === 'active' ? 'Đã đăng kích hoạt lại tin tuyển dụng!' : 'Đã đóng tin tuyển dụng!', 'success');
        await Promise.all([loadCompanyJobs(), loadBiDashboard()]);
      } catch (err) {
        showToast('Lỗi cập nhật trạng thái tin: ' + err.message, 'error');
      }
    });
  });

  // Sự kiện Xóa tin tuyển dụng
  listEl.querySelectorAll('.btn-delete-job').forEach(btn => {
    btn.addEventListener('click', async () => {
      const jobId = Number(btn.dataset.jobId);
      const title = btn.dataset.jobTitle;
      if (!confirm(`Bạn có chắc chắn muốn xóa tin tuyển dụng "${title}" không?`)) return;
      try {
        await apiDelete(`/jobs/${jobId}/`);
        showToast(`Đã xóa tin tuyển dụng "${title}"!`, 'success');
        await Promise.all([loadCompanyJobs(), loadBiDashboard()]);
      } catch (err) {
        showToast('Không thể xóa tin tuyển dụng: ' + err.message, 'error');
      }
    });
  });
}

// ---- Modal Tạo / Chỉnh sửa Tin tuyển dụng ----
function initJobModal() {
  const modal = document.getElementById('job-modal');
  const openCreateBtn = document.getElementById('btn-open-create-job');
  const closeBtn = document.getElementById('btn-close-job-modal');
  const cancelBtn = document.getElementById('btn-cancel-job-modal');
  const form = document.getElementById('job-form');
  const aiExtractBtn = document.getElementById('btn-ai-extract-jd-skills');

  const closeModal = () => modal?.classList.add('hidden');

  openCreateBtn?.addEventListener('click', () => openJobModal(null));
  closeBtn?.addEventListener('click', closeModal);
  cancelBtn?.addEventListener('click', closeModal);

  aiExtractBtn?.addEventListener('click', async () => {
    const jdText = document.getElementById('form-job-description')?.value?.trim() || '';
    if (!jdText) {
      showToast('Vui lòng nhập mô tả công việc (JD) trước khi trích xuất kỹ năng', 'warning');
      return;
    }
    try {
      const res = await apiPost('/ai/extract-skills/', { text: jdText });
      const skills = (res.skills || []).map(s => s.skill_name || s.name || s);
      if (skills.length) {
        document.getElementById('form-job-skills').value = skills.join(', ');
        showToast(`AI đã phát hiện ${skills.length} kỹ năng từ JD!`, 'success');
      } else {
        showToast('AI chưa phát hiện thêm kỹ năng mới trong văn bản JD', 'info');
      }
    } catch (err) {
      showToast('Lỗi trích xuất kỹ năng AI: ' + err.message, 'error');
    }
  });

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const jobId = document.getElementById('form-job-id')?.value;
    const skillInput = document.getElementById('form-job-skills')?.value || '';
    const skillNames = skillInput.split(',').map(s => s.trim()).filter(Boolean);

    const payload = {
      company_id: currentCompanyId,
      job_title: document.getElementById('form-job-title').value.trim(),
      employment_type: document.getElementById('form-job-type').value,
      status: document.getElementById('form-job-status').value,
      location: document.getElementById('form-job-location').value.trim(),
      required_experience: Number(document.getElementById('form-job-exp').value || 0),
      salary_min: document.getElementById('form-job-salary-min').value ? Number(document.getElementById('form-job-salary-min').value) : null,
      salary_max: document.getElementById('form-job-salary-max').value ? Number(document.getElementById('form-job-salary-max').value) : null,
      application_deadline: document.getElementById('form-job-deadline').value || null,
      job_description: document.getElementById('form-job-description').value.trim(),
      skill_names: skillNames,
    };

    try {
      if (jobId) {
        await apiPatch(`/jobs/${jobId}/`, payload);
        showToast('Đã cập nhật tin tuyển dụng thành công!', 'success');
      } else {
        await apiPost('/jobs/', payload);
        showToast('Đã tạo và đăng tin tuyển dụng mới thành công!', 'success');
      }
      closeModal();
      await Promise.all([loadCompanyJobs(), loadBiDashboard()]);
    } catch (err) {
      showToast('Lỗi lưu tin tuyển dụng: ' + err.message, 'error');
    }
  });
}

function openJobModal(job = null) {
  const isEdit = !!job;
  safeSetText('job-modal-badge', isEdit ? `Chỉnh sửa tin #${job.job_id}` : 'Đăng tin tuyển dụng mới');
  safeSetText('job-modal-title', isEdit ? 'Chỉnh Sửa Tin Tuyển Dụng' : 'Tạo & Đăng Tin Tuyển Dụng Mới');

  document.getElementById('form-job-id').value = isEdit ? job.job_id : '';
  document.getElementById('form-job-title').value = isEdit ? (job.job_title || '') : '';
  document.getElementById('form-job-type').value = isEdit ? (job.employment_type || 'full-time') : 'full-time';
  document.getElementById('form-job-status').value = isEdit ? (job.status || 'active') : 'active';
  document.getElementById('form-job-location').value = isEdit ? (job.location || '') : 'Hà Nội';
  document.getElementById('form-job-exp').value = isEdit ? (job.required_experience ?? 2) : 2;
  document.getElementById('form-job-salary-min').value = isEdit && job.salary_min ? Math.round(job.salary_min) : '';
  document.getElementById('form-job-salary-max').value = isEdit && job.salary_max ? Math.round(job.salary_max) : '';

  const defaultDeadline = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
  document.getElementById('form-job-deadline').value = isEdit ? (job.application_deadline || defaultDeadline) : defaultDeadline;
  document.getElementById('form-job-description').value = isEdit ? (job.job_description || '') : '';

  const skillList = isEdit && Array.isArray(job.skills)
    ? job.skills.map(s => s.skill_name || s).join(', ')
    : '';
  document.getElementById('form-job-skills').value = skillList;

  document.getElementById('job-modal')?.classList.remove('hidden');
}

// ---- Modal Gia hạn Tin tuyển dụng ----
function initExtendJobModal() {
  const modal = document.getElementById('extend-job-modal');
  const closeBtn = document.getElementById('btn-close-extend-modal');
  const cancelBtn = document.getElementById('btn-cancel-extend');
  const confirmBtn = document.getElementById('btn-confirm-extend');
  const dateInput = document.getElementById('extend-deadline-input');

  const closeModal = () => modal?.classList.add('hidden');
  closeBtn?.addEventListener('click', closeModal);
  cancelBtn?.addEventListener('click', closeModal);

  document.querySelectorAll('.btn-quick-extend').forEach(btn => {
    btn.addEventListener('click', () => {
      const days = Number(btn.dataset.extendDays || 30);
      const targetDate = new Date(Date.now() + days * 86400000).toISOString().slice(0, 10);
      if (dateInput) dateInput.value = targetDate;
    });
  });

  confirmBtn?.addEventListener('click', async () => {
    const jobId = document.getElementById('extend-job-id')?.value;
    const newDeadline = dateInput?.value;
    if (!jobId) return;

    try {
      await apiPost(`/jobs/${jobId}/extend/`, {
        application_deadline: newDeadline,
        days: 30,
      });
      closeModal();
      showToast('Đã gia hạn thời hạn nhận hồ sơ và kích hoạt tin tuyển dụng!', 'success');
      await Promise.all([loadCompanyJobs(), loadBiDashboard()]);
    } catch (err) {
      showToast('Lỗi gia hạn tin tuyển dụng: ' + err.message, 'error');
    }
  });
}

function openExtendJobModal({ job_id, job_title, deadline }) {
  document.getElementById('extend-job-id').value = job_id;
  safeSetText('extend-modal-job-title', job_title);
  const next30 = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
  document.getElementById('extend-deadline-input').value = next30 || deadline;
  document.getElementById('extend-job-modal')?.classList.remove('hidden');
}

// =========================================================================
// TAB 3 & TAB 4: TẢI DANH SÁCH ỨNG VIÊN ĐÃ ỨNG TUYỂN & QUY TRÌNH TUYỂN DỤNG
// =========================================================================
async function loadCompanyApplications() {
  try {
    const data = await apiGet('/applications/');
    const apps = Array.isArray(data) ? data : (data.results || []);
    allApplications = apps;

    safeSetText('emp-badge-candidates', allApplications.length);
    safeSetText('emp-badge-pipeline', allApplications.filter(a => (a.status || 'pending') === 'pending').length);

    renderCompanyJobs();
    renderCandidateProfiles();
    renderRecruitmentPipeline();
  } catch (err) {
    showToast('Không thể tải danh sách hồ sơ ứng tuyển: ' + err.message, 'error');
  }
}

// ---- TAB 3: Quản lý hồ sơ ứng viên ----
function renderCandidateProfiles() {
  const listEl = document.getElementById('emp-candidates-list');
  if (!listEl) return;

  const jobFilter = document.getElementById('cand-filter-job')?.value || '';
  const filtered = allApplications.filter(a => !jobFilter || String(a.job_id) === String(jobFilter));

  if (!filtered.length) {
    listEl.innerHTML = `
      <div class="bg-white rounded-2xl p-10 text-center border border-gray-100">
        <p class="text-base font-bold text-gray-800">Chưa có ứng viên nào ứng tuyển</p>
        <p class="text-xs text-gray-500 mt-1">Khi ứng viên nộp hồ sơ CV, thông tin trích xuất và điểm AI Matching sẽ hiển thị tại đây.</p>
      </div>
    `;
    return;
  }

  listEl.innerHTML = filtered.map(app => {
    const stage = getStageMeta(app.status);
    const aiScore = app.ai_match?.matching_score != null ? Math.round(app.ai_match.matching_score) : null;
    const skills = Array.isArray(app.candidate_skills) ? app.candidate_skills : [];
    const matchedSkills = app.ai_match?.matched_skills || [];
    const missingSkills = app.ai_match?.missing_skills || [];
    const cvUrl = app.candidate_cv
      ? (app.candidate_cv.startsWith('http') ? app.candidate_cv : `http://localhost:8000${app.candidate_cv}`)
      : null;

    return `
      <div class="bg-white rounded-2xl p-6 shadow-xs border border-gray-100 hover:border-purple-200 transition space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div class="flex items-start gap-3.5">
            <div class="w-12 h-12 rounded-2xl gradient-primary text-white font-black text-lg flex items-center justify-center flex-shrink-0">
              ${escapeHtml((app.candidate_name || 'U').charAt(0).toUpperCase())}
            </div>
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="text-base font-extrabold text-gray-900">${escapeHtml(app.candidate_name || `Ứng viên #${app.candidate_id}`)}</h3>
                <span class="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold border ${stage.badge}">${escapeHtml(app.status_label || stage.label)}</span>
                ${aiScore != null ? `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-black bg-indigo-50 text-indigo-700 border border-indigo-200">🤖 AI Match: ${aiScore}%</span>` : ''}
              </div>
              <p class="text-xs font-bold text-blue-600 mt-0.5">${escapeHtml(app.candidate_position || 'Ứng viên công nghệ')}</p>
              <p class="text-xs text-gray-500 mt-1">
                📌 Ứng tuyển vị trí: <strong class="text-gray-800">${escapeHtml(app.job_title)}</strong>
                · 📅 Ngày nộp: ${app.applied_at ? new Date(app.applied_at).toLocaleDateString('vi-VN') : '---'}
              </p>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-2 self-start">
            ${cvUrl ? `
              <a href="${cvUrl}" target="_blank" class="px-3.5 py-2 rounded-xl bg-blue-50 text-blue-700 border border-blue-200 text-xs font-bold hover:bg-blue-100 transition">
                📄 Xem tệp CV gốc
              </a>
            ` : ''}
            <button type="button" class="btn-view-cand-detail px-3.5 py-2 rounded-xl bg-purple-50 text-purple-700 border border-purple-200 text-xs font-bold hover:bg-purple-100 transition"
              data-app-id="${app.application_id}">
              🔍 Xem chi tiết hồ sơ
            </button>
            <button type="button" onclick="switchEmployerTab('pipeline')" class="px-3.5 py-2 rounded-xl gradient-primary text-white text-xs font-bold hover:opacity-95 transition">
              Xử lý quy trình &rarr;
            </button>
          </div>
        </div>

        <!-- Thông tin cá nhân trích xuất từ CV -->
        <div class="grid grid-cols-1 sm:grid-cols-4 gap-3 p-3.5 rounded-xl bg-slate-50 border border-gray-100 text-xs">
          <div>
            <span class="text-[10px] font-bold text-gray-400 uppercase block">Email liên hệ</span>
            <span class="font-semibold text-gray-800">${escapeHtml(app.candidate_email || 'Chưa cập nhật')}</span>
          </div>
          <div>
            <span class="text-[10px] font-bold text-gray-400 uppercase block">Số điện thoại</span>
            <span class="font-semibold text-gray-800">${escapeHtml(app.candidate_phone || 'Chưa cập nhật')}</span>
          </div>
          <div>
            <span class="text-[10px] font-bold text-gray-400 uppercase block">Kinh nghiệm</span>
            <span class="font-semibold text-gray-800">${app.candidate_experience ?? 0} năm kinh nghiệm</span>
          </div>
          <div>
            <span class="text-[10px] font-bold text-gray-400 uppercase block">Khu vực</span>
            <span class="font-semibold text-gray-800">${escapeHtml(app.candidate_address || 'Việt Nam')}</span>
          </div>
        </div>

        <!-- Kỹ năng phù hợp & còn thiếu -->
        <div class="flex flex-wrap items-center gap-1.5">
          <span class="text-[11px] font-bold text-gray-400 mr-1">Kỹ năng trích xuất từ CV:</span>
          ${skills.length
            ? skills.map(s => `<span class="px-2.5 py-0.5 rounded-lg text-[11px] font-semibold bg-gray-100 text-gray-800">${escapeHtml(s.skill_name || s)}</span>`).join('')
            : `<span class="text-xs text-gray-400 italic">Chưa có kỹ năng</span>`
          }
          ${matchedSkills.length ? `<span class="ml-2 text-[11px] font-bold text-emerald-700">✓ Khớp ${matchedSkills.length} kỹ năng JD</span>` : ''}
          ${missingSkills.length ? `<span class="ml-2 text-[11px] font-bold text-amber-700">⚠ Thiếu: ${escapeHtml(missingSkills.slice(0, 3).join(', '))}</span>` : ''}
        </div>
      </div>
    `;
  }).join('');

  listEl.querySelectorAll('.btn-view-cand-detail').forEach(btn => {
    btn.addEventListener('click', () => {
      const app = allApplications.find(a => Number(a.application_id) === Number(btn.dataset.appId));
      if (app) openCandidateDetailModal(app);
    });
  });
}

function initCandidateDetailModal() {
  const modal = document.getElementById('candidate-detail-modal');
  const close1 = document.getElementById('btn-close-cand-modal');
  const close2 = document.getElementById('btn-close-cand-modal-bottom');
  const closeModal = () => modal?.classList.add('hidden');
  close1?.addEventListener('click', closeModal);
  close2?.addEventListener('click', closeModal);
}

function openCandidateDetailModal(app) {
  safeSetText('cand-modal-name', app.candidate_name || 'Ứng viên');
  safeSetText('cand-modal-position', app.candidate_position || 'Ứng viên');

  const body = document.getElementById('cand-modal-body');
  const skills = Array.isArray(app.candidate_skills) ? app.candidate_skills : [];
  const edu = Array.isArray(app.candidate_education) ? app.candidate_education : [];
  const matched = app.ai_match?.matched_skills || [];
  const missing = app.ai_match?.missing_skills || [];
  const score = app.ai_match?.matching_score != null ? Math.round(app.ai_match.matching_score) : 0;

  if (body) {
    body.innerHTML = `
      <div class="grid grid-cols-2 gap-3 p-4 rounded-2xl bg-slate-50 border border-gray-100">
        <div><span class="text-gray-400 font-bold block">Email:</span><span class="font-bold text-gray-900">${escapeHtml(app.candidate_email || '---')}</span></div>
        <div><span class="text-gray-400 font-bold block">Điện thoại:</span><span class="font-bold text-gray-900">${escapeHtml(app.candidate_phone || '---')}</span></div>
        <div><span class="text-gray-400 font-bold block">Địa chỉ:</span><span class="font-bold text-gray-900">${escapeHtml(app.candidate_address || '---')}</span></div>
        <div><span class="text-gray-400 font-bold block">Kinh nghiệm:</span><span class="font-bold text-gray-900">${app.candidate_experience ?? 0} năm</span></div>
      </div>

      <div class="p-4 rounded-2xl bg-blue-50/70 border border-blue-100 flex items-center justify-between">
        <div>
          <p class="font-extrabold text-blue-950">Ứng tuyển: ${escapeHtml(app.job_title)}</p>
          <p class="text-[11px] text-blue-700">Điểm tương thích AI/ML giữa CV và Mô tả công việc (JD)</p>
        </div>
        <span class="text-2xl font-black text-blue-600 bg-white px-4 py-1.5 rounded-xl border border-blue-200">${score}%</span>
      </div>

      <div>
        <p class="font-bold text-gray-700 mb-1">Tóm tắt chuyên môn trích xuất từ CV:</p>
        <p class="p-3 rounded-xl bg-gray-50 border border-gray-100 text-gray-700 leading-relaxed">${escapeHtml(app.candidate_summary || 'Chưa có tóm tắt.')}</p>
      </div>

      ${edu.length ? `
        <div>
          <p class="font-bold text-gray-700 mb-1">Học vấn & Đào tạo:</p>
          ${edu.map(e => `<p class="p-2.5 rounded-xl bg-gray-50 border border-gray-100 font-semibold">${escapeHtml(e.degree)} · ${escapeHtml(e.major)} — ${escapeHtml(e.school_name)}</p>`).join('')}
        </div>
      ` : ''}

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div class="p-3 rounded-xl bg-emerald-50 border border-emerald-200">
          <p class="font-bold text-emerald-900 mb-1.5">✓ Kỹ năng đáp ứng JD (${matched.length})</p>
          <div class="flex flex-wrap gap-1">
            ${matched.map(s => `<span class="px-2 py-0.5 rounded-md bg-white text-emerald-800 border border-emerald-200 font-bold">${escapeHtml(s)}</span>`).join('') || '---'}
          </div>
        </div>
        <div class="p-3 rounded-xl bg-amber-50 border border-amber-200">
          <p class="font-bold text-amber-900 mb-1.5">⚠ Kỹ năng còn thiếu (${missing.length})</p>
          <div class="flex flex-wrap gap-1">
            ${missing.map(s => `<span class="px-2 py-0.5 rounded-md bg-white text-amber-800 border border-amber-200 font-bold">${escapeHtml(s)}</span>`).join('') || 'Không thiếu kỹ năng nào'}
          </div>
        </div>
      </div>

      <div>
        <p class="font-bold text-gray-700 mb-1">Toàn bộ kỹ năng trong CV (${skills.length}):</p>
        <div class="flex flex-wrap gap-1.5">
          ${skills.map(s => `<span class="px-2.5 py-1 rounded-lg bg-gray-100 text-gray-800 font-semibold">${escapeHtml(s.skill_name)} (${escapeHtml(s.proficiency_level || 'intermediate')})</span>`).join('')}
        </div>
      </div>
    `;
  }

  document.getElementById('candidate-detail-modal')?.classList.remove('hidden');
}

// =========================================================================
// TAB 4: QUẢN LÝ QUY TRÌNH TUYỂN DỤNG (CẬP NHẬT 5 TRẠNG THÁI & ĐỒNG BỘ ỨNG VIÊN)
// =========================================================================
function renderRecruitmentPipeline() {
  const listEl = document.getElementById('emp-pipeline-list');
  if (!listEl) return;

  // Đếm số lượng từng bước quy trình
  const counts = { pending: 0, reviewing: 0, interviewed: 0, offered: 0, rejected: 0 };
  allApplications.forEach(a => {
    const st = (a.status || 'pending').toLowerCase();
    if (st === 'pending') counts.pending++;
    else if (st === 'reviewing' || st === 'shortlisted') counts.reviewing++;
    else if (st === 'interviewed') counts.interviewed++;
    else if (st === 'offered') counts.offered++;
    else if (st === 'rejected') counts.rejected++;
  });

  safeSetText('pipe-count-pending', counts.pending);
  safeSetText('pipe-count-reviewing', counts.reviewing);
  safeSetText('pipe-count-interviewed', counts.interviewed);
  safeSetText('pipe-count-offered', counts.offered);
  safeSetText('pipe-count-rejected', counts.rejected);

  const filterSt = document.getElementById('pipeline-filter-status')?.value || '';
  const filtered = allApplications.filter(a => {
    if (!filterSt) return true;
    const st = (a.status || 'pending').toLowerCase();
    if (filterSt === 'reviewing' && st === 'shortlisted') return true;
    return st === filterSt;
  });

  if (!filtered.length) {
    listEl.innerHTML = `
      <div class="bg-white rounded-2xl p-10 text-center border border-gray-100">
        <p class="text-base font-bold text-gray-800">Không có hồ sơ ứng tuyển nào ở trạng thái này</p>
      </div>
    `;
    return;
  }

  listEl.innerHTML = filtered.map(app => {
    const currentStage = getStageMeta(app.status);
    const aiScore = app.ai_match?.matching_score != null ? Math.round(app.ai_match.matching_score) : null;

    return `
      <div class="bg-white rounded-2xl p-6 shadow-xs border border-gray-100 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-base font-extrabold text-gray-900">${escapeHtml(app.candidate_name || `Ứng viên #${app.candidate_id}`)}</span>
              <span class="text-xs text-gray-400">ứng tuyển</span>
              <span class="text-sm font-extrabold text-blue-600">${escapeHtml(app.job_title)}</span>
              ${aiScore != null ? `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200">AI Match: ${aiScore}%</span>` : ''}
            </div>
            <p class="text-xs text-gray-500 mt-0.5">
              📧 ${escapeHtml(app.candidate_email || '---')} · 📞 ${escapeHtml(app.candidate_phone || '---')}
              · Cập nhật lần cuối: ${app.updated_at ? new Date(app.updated_at).toLocaleString('vi-VN') : '---'}
            </p>
          </div>

          <div class="flex items-center gap-2">
            <span class="text-[11px] font-bold text-gray-400 uppercase">Trạng thái hiện tại:</span>
            <span class="px-3.5 py-1.5 rounded-full text-xs font-extrabold border ${currentStage.badge}">
              ${escapeHtml(app.status_label || currentStage.label)}
            </span>
          </div>
        </div>

        <!-- 5 Nút Chuyển Trạng Thái Quy Trình Tuyển Dụng Trực Tiếp -->
        <div class="p-3.5 rounded-2xl bg-slate-50 border border-gray-100 space-y-3">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <span class="text-xs font-bold text-gray-700">🔄 Chọn bước quy trình tuyển dụng mới (Đồng bộ sang trang Ứng viên):</span>
            <div class="flex flex-wrap items-center gap-2">
              ${PIPELINE_STAGES.map(st => {
                const isCurrent = currentStage.code === st.code;
                return `
                  <button type="button"
                    class="btn-pipeline-stage px-3 py-1.5 rounded-xl text-xs font-bold border transition ${
                      isCurrent
                        ? `${st.badge} ring-2 ring-offset-1 ring-blue-500`
                        : `bg-white border-gray-200 text-gray-700 ${st.btn}`
                    }"
                    data-app-id="${app.application_id}"
                    data-target-status="${st.code}">
                    ${isCurrent ? '✓ ' : ''}${st.label}
                  </button>
                `;
              }).join('')}
            </div>
          </div>

          <!-- Ghi chú phản hồi cho ứng viên -->
          <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 pt-2 border-t border-gray-200/60">
            <input type="text" id="pipe-note-${app.application_id}"
              value="${escapeHtml(app.notes || '')}"
              placeholder="Nhập ghi chú / lịch phỏng vấn / phản hồi gửi tới ứng viên..."
              class="flex-1 px-3 py-2 bg-white border border-gray-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            <button type="button" class="btn-save-pipe-note px-4 py-2 bg-gray-800 hover:bg-gray-900 text-white rounded-xl text-xs font-bold transition"
              data-app-id="${app.application_id}"
              data-current-status="${currentStage.code}">
              Lưu ghi chú
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  // Sự kiện bấm chuyển trạng thái quy trình
  listEl.querySelectorAll('.btn-pipeline-stage').forEach(btn => {
    btn.addEventListener('click', async () => {
      const appId = Number(btn.dataset.appId);
      const targetStatus = btn.dataset.targetStatus;
      const noteEl = document.getElementById(`pipe-note-${appId}`);
      const notes = noteEl ? noteEl.value.trim() : '';
      await updateApplicationPipelineStatus(appId, targetStatus, notes);
    });
  });

  // Sự kiện lưu ghi chú kèm trạng thái hiện tại
  listEl.querySelectorAll('.btn-save-pipe-note').forEach(btn => {
    btn.addEventListener('click', async () => {
      const appId = Number(btn.dataset.appId);
      const currentStatus = btn.dataset.currentStatus;
      const noteEl = document.getElementById(`pipe-note-${appId}`);
      const notes = noteEl ? noteEl.value.trim() : '';
      await updateApplicationPipelineStatus(appId, currentStatus, notes);
    });
  });
}

async function updateApplicationPipelineStatus(appId, status, notes = '') {
  try {
    const res = await apiPatch(`/applications/${appId}/update_status/`, { status, notes });
    const stage = getStageMeta(res.status || status);
    showToast(`Đã cập nhật trạng thái hồ sơ sang "${res.status_label || stage.label}"! (Đã đồng bộ sang trang Ứng viên)`, 'success');
    await Promise.all([
      loadCompanyApplications(),
      loadBiDashboard(),
    ]);
  } catch (err) {
    showToast('Lỗi cập nhật trạng thái quy trình: ' + err.message, 'error');
  }
}

