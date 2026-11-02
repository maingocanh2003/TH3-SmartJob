// =============================================
// SmartJob - Main Page Logic (index.html)
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

let currentPage = 1;
let totalJobs = 0;
const PAGE_SIZE = 6;

function formatSalary(min, max) {
  const numMin = min !== null && min !== undefined ? Number(min) : null;
  const numMax = max !== null && max !== undefined ? Number(max) : null;
  if (!numMin && !numMax) return 'Thỏa thuận';
  const fmt = v => v >= 1e6 ? (v / 1e6).toFixed(0) + ' triệu' : v.toLocaleString('vi-VN');
  if (numMin && numMax) return `${fmt(numMin)} - ${fmt(numMax)} VNĐ`;
  if (numMin) return `Từ ${fmt(numMin)} VNĐ`;
  return `Đến ${fmt(numMax)} VNĐ`;
}

function getJobBadgeClass(type) {
  const norm = (type || '').replace('-', '_');
  const map = { full_time: 'bg-blue-100 text-blue-700', part_time: 'bg-green-100 text-green-700', contract: 'bg-orange-100 text-orange-700', internship: 'bg-purple-100 text-purple-700' };
  return map[norm] || 'bg-gray-100 text-gray-700';
}

function buildJobCard(job) {
  const id = job.id ?? job.job_id;
  const title = job.title ?? job.job_title ?? 'Việc làm';
  const company = job.company_detail || {};
  const companyName = company.name || job.company_name || 'Công ty';
  const logoLetter = (companyName || 'J')[0].toUpperCase();
  const colors = ['bg-blue-500', 'bg-purple-500', 'bg-green-500', 'bg-orange-500', 'bg-pink-500', 'bg-teal-500'];
  const color = colors[(id || 0) % colors.length];
  const rawType = job.job_type ?? job.employment_type ?? '';
  const typeLabel = JOB_TYPES[rawType] || JOB_TYPES[rawType.replace('-', '_')] || rawType;
  const skills = job.skills_required ?? job.skills ?? [];
  const deadline = job.deadline ?? job.application_deadline;

  return `
  <div class="job-card bg-white rounded-2xl p-6 border border-gray-100 shadow-sm flex flex-col gap-4">
    <div class="flex items-start justify-between">
      <div class="flex items-center gap-3">
        <div class="w-12 h-12 ${color} rounded-xl flex items-center justify-center text-white font-bold text-lg flex-shrink-0">${logoLetter}</div>
        <div>
          <h3 class="font-semibold text-gray-800 text-sm leading-tight line-clamp-2">${title}</h3>
          <p class="text-gray-500 text-xs mt-0.5">${companyName}</p>
        </div>
      </div>
      <span class="text-xs px-2.5 py-1 rounded-full font-medium flex-shrink-0 ${getJobBadgeClass(rawType)}">${typeLabel}</span>
    </div>
    <div class="flex flex-wrap gap-2 text-xs text-gray-500">
      <span class="flex items-center gap-1">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
        ${job.location || 'Không xác định'}
      </span>
      <span class="flex items-center gap-1">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        ${formatSalary(job.salary_min, job.salary_max)}
      </span>
    </div>
    ${skills && skills.length ? `
    <div class="flex flex-wrap gap-1.5">
      ${skills.slice(0, 3).map(s => `<span class="skill-badge">${typeof s === 'string' ? s : (s.skill_name || s.name || '')}</span>`).join('')}
      ${skills.length > 3 ? `<span class="text-xs text-gray-400">+${skills.length - 3}</span>` : ''}
    </div>` : ''}
    <div class="flex items-center justify-between mt-auto pt-2 border-t border-gray-50">
      <span class="text-xs text-gray-400">${deadline ? 'HSD: ' + new Date(deadline).toLocaleDateString('vi-VN') : ''}</span>
      <a href="job-detail.html?id=${id}" class="text-sm font-semibold text-blue-600 hover:text-blue-700 transition flex items-center gap-1">
        Xem chi tiết
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
      </a>
    </div>
  </div>`;
}

async function loadStats() {
  try {
    const data = await apiGet('/bi/overview/', false);
    document.getElementById('stat-jobs').textContent = (data.total_jobs ?? '--').toLocaleString('vi-VN');
    document.getElementById('stat-companies').textContent = (data.total_companies ?? '--').toLocaleString('vi-VN');
    document.getElementById('stat-candidates').textContent = (data.total_candidates ?? '--').toLocaleString('vi-VN');
    document.getElementById('stat-applications').textContent = (data.total_applications ?? '--').toLocaleString('vi-VN');
  } catch {
    ['stat-jobs','stat-companies','stat-candidates','stat-applications'].forEach(id => {
      document.getElementById(id).textContent = '—';
    });
  }
}

async function loadJobs(params = {}) {
  const grid = document.getElementById('jobs-grid');
  try {
    const query = new URLSearchParams({ status: 'active', page_size: PAGE_SIZE, page: currentPage, ...params }).toString();
    const data = await apiGet(`/jobs/?${query}`, false);
    const jobs = data.results ?? data;
    totalJobs = data.count ?? jobs.length;

    if (currentPage === 1) grid.innerHTML = '';
    if (jobs.length === 0 && currentPage === 1) {
      grid.innerHTML = '<div class="col-span-3 text-center py-16 text-gray-400"><svg class="w-16 h-16 mx-auto mb-4 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg><p>Không tìm thấy việc làm phù hợp</p></div>';
    } else {
      jobs.forEach(job => grid.insertAdjacentHTML('beforeend', buildJobCard(job)));
    }

    const btn = document.getElementById('btn-load-more');
    if (totalJobs > currentPage * PAGE_SIZE) btn.classList.remove('hidden');
    else btn.classList.add('hidden');
  } catch (err) {
    grid.innerHTML = `<div class="col-span-3 text-center py-16 text-red-400"><p>Lỗi tải dữ liệu: ${err.message}</p></div>`;
  }
}

async function loadTopSkills() {
  try {
    const data = await apiGet('/bi/skills_demand/', false);
    const grid = document.getElementById('skills-grid');
    const skills = (data.results ?? data).slice(0, 10);
    const maxCount = Math.max(...skills.map(s => s.count ?? s.job_count ?? 1));
    grid.innerHTML = skills.map((s, i) => {
      const pct = Math.round(((s.count ?? s.job_count ?? 1) / maxCount) * 100);
      const gradients = ['from-blue-500 to-blue-600', 'from-purple-500 to-purple-600', 'from-green-500 to-green-600', 'from-orange-500 to-orange-600', 'from-pink-500 to-pink-600'];
      const g = gradients[i % gradients.length];
      return `
      <div class="bg-white border border-gray-100 rounded-xl p-4 hover:shadow-md transition cursor-pointer">
        <div class="flex items-center justify-between mb-2">
          <span class="font-medium text-gray-800 text-sm">${s.skill_name ?? s.name ?? s.skill}</span>
          <span class="text-xs text-gray-400">${s.count ?? s.job_count ?? 0}</span>
        </div>
        <div class="w-full bg-gray-100 rounded-full h-1.5">
          <div class="h-1.5 rounded-full bg-gradient-to-r ${g}" style="width:${pct}%"></div>
        </div>
      </div>`;
    }).join('');
  } catch { /* ignore */ }
}

function getSearchParams() {
  return {
    search: document.getElementById('search-keyword').value.trim(),
    location: document.getElementById('search-location').value.trim(),
    industry: document.getElementById('filter-industry').value,
  };
}

document.addEventListener('DOMContentLoaded', () => {
  // Update nav links based on user type
  const user = getUser();
  if (user) {
    const profileLink = document.getElementById('nav-profile-link');
    const dashLink = document.getElementById('nav-dashboard-link');
    if (user.user_type === 'company') {
      if (profileLink) profileLink.classList.add('hidden');
      if (dashLink) dashLink.classList.remove('hidden');
    }
  }

  loadStats();
  loadJobs();
  loadTopSkills();

  document.getElementById('btn-search').addEventListener('click', () => {
    currentPage = 1;
    loadJobs(getSearchParams());
  });

  ['search-keyword', 'search-location'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', e => {
      if (e.key === 'Enter') { currentPage = 1; loadJobs(getSearchParams()); }
    });
  });

  document.querySelectorAll('.quick-tag').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('search-keyword').value = btn.textContent;
      currentPage = 1; loadJobs({ search: btn.textContent });
    });
  });

  document.getElementById('filter-industry').addEventListener('change', () => {
    currentPage = 1; loadJobs(getSearchParams());
  });

  document.getElementById('btn-load-more').addEventListener('click', () => {
    currentPage++;
    loadJobs(getSearchParams());
  });

  document.getElementById('mobile-menu-btn').addEventListener('click', () => {
    const m = document.getElementById('mobile-menu');
    m.classList.toggle('hidden');
  });
});
