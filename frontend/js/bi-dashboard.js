// SmartJob - BI dashboard rendering

const numberFormatter = new Intl.NumberFormat('vi-VN');
const salaryFormatter = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 });

function setDashboardText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function renderEmpty(containerId, message) {
  const container = document.getElementById(containerId);
  container.replaceChildren(makeElement('p', 'dashboard-empty', message));
}

function renderError(containerId, message) {
  const container = document.getElementById(containerId);
  container.replaceChildren(makeElement('p', 'dashboard-chart-error', message));
}

function renderOverview(data) {
  const metrics = {
    'kpi-total-jobs': data.total_jobs,
    'kpi-active-jobs': data.active_jobs,
    'kpi-candidates': data.total_candidates,
    'kpi-companies': data.total_companies,
    'kpi-applications': data.total_applications,
    'kpi-views': data.total_views,
  };
  Object.entries(metrics).forEach(([id, value]) => {
    setDashboardText(id, Number.isFinite(Number(value)) ? numberFormatter.format(value) : '—');
  });
}

function renderSkillsDemand(skills) {
  const container = document.getElementById('skills-chart');
  if (!Array.isArray(skills) || skills.length === 0) {
    renderEmpty('skills-chart', 'Chưa có dữ liệu kỹ năng tuyển dụng.');
    return;
  }

  const maxDemand = Math.max(...skills.map(skill => Number(skill.demand_count) || 0), 1);
  const rows = skills.map((skill, index) => {
    const row = makeElement('div', 'chart-row');
    const label = makeElement('div', 'chart-row-label');
    const name = makeElement('span', 'chart-row-name', skill.skill_name || 'Kỹ năng khác');
    const category = makeElement('span', 'chart-row-detail', skill.category || 'Khác');
    label.append(name, category);

    const value = Number(skill.demand_count) || 0;
    const track = makeElement('div', 'chart-track');
    const fill = makeElement('div', `chart-fill chart-fill-${index % 5}`);
    fill.style.width = `${Math.max(value / maxDemand * 100, value > 0 ? 2 : 0)}%`;
    fill.setAttribute('role', 'progressbar');
    fill.setAttribute('aria-label', `${skill.skill_name || 'Kỹ năng'}: ${numberFormatter.format(value)} tin tuyển dụng`);
    fill.setAttribute('aria-valuemin', '0');
    fill.setAttribute('aria-valuemax', String(maxDemand));
    fill.setAttribute('aria-valuenow', String(value));
    track.append(fill);

    row.append(label, track, makeElement('span', 'chart-row-value', numberFormatter.format(value)));
    return row;
  });
  container.replaceChildren(...rows);
}

function formatSalaryRange(item) {
  const minimum = Number(item.avg_min) || 0;
  const maximum = Number(item.avg_max) || 0;
  const minText = minimum > 0 ? `${salaryFormatter.format(minimum / 1000000)} tr` : 'Chưa có mức thấp';
  const maxText = maximum > 0 ? `${salaryFormatter.format(maximum / 1000000)} tr` : 'Chưa có mức cao';
  return { minimum, maximum, label: `${minText} – ${maxText} VNĐ` };
}

function renderSalaryChart(containerId, entries, labelKey, emptyMessage) {
  const container = document.getElementById(containerId);
  if (!Array.isArray(entries) || entries.length === 0) {
    renderEmpty(containerId, emptyMessage);
    return;
  }

  const maxSalary = Math.max(...entries.map(item => Number(item.avg_max) || 0), 1);
  const rows = entries.slice(0, 8).map((item, index) => {
    const row = makeElement('div', 'salary-row');
    const heading = makeElement('div', 'salary-row-heading');
    heading.append(
      makeElement('span', 'chart-row-name', item[labelKey] || 'Khác'),
      makeElement('span', 'salary-count', `${numberFormatter.format(item.job_count || 0)} tin`)
    );

    const range = formatSalaryRange(item);
    const track = makeElement('div', 'salary-track');
    const fill = makeElement('div', `salary-range salary-range-${index % 5}`);
    const left = Math.min(range.minimum / maxSalary * 100, 99);
    const width = Math.max((range.maximum - range.minimum) / maxSalary * 100, range.maximum > 0 ? 1 : 0);
    fill.style.left = `${left}%`;
    fill.style.width = `${Math.min(width, 100 - left)}%`;
    fill.setAttribute('role', 'img');
    fill.setAttribute('aria-label', `${item[labelKey] || 'Khác'}: ${range.label}`);
    track.append(fill);

    row.append(heading, track, makeElement('p', 'salary-row-value', range.label));
    return row;
  });
  container.replaceChildren(...rows);
}

function renderFunnel(data) {
  const container = document.getElementById('funnel-chart');
  const funnel = Array.isArray(data.funnel) ? data.funnel : [];
  if (funnel.length === 0) {
    renderEmpty('funnel-chart', 'Chưa có dữ liệu phễu tuyển dụng.');
  } else {
    const maxCount = Math.max(...funnel.map(stage => Number(stage.count) || 0), 1);
    const rows = funnel.map((stage, index) => {
      const row = makeElement('div', 'funnel-row');
      const heading = makeElement('div', 'salary-row-heading');
      heading.append(
        makeElement('span', 'chart-row-name', stage.stage || 'Giai đoạn'),
        makeElement('span', 'chart-row-value', numberFormatter.format(stage.count || 0))
      );
      const track = makeElement('div', 'chart-track');
      const fill = makeElement('div', `funnel-fill funnel-fill-${index % 5}`);
      const count = Number(stage.count) || 0;
      fill.style.width = `${Math.max(count / maxCount * 100, count > 0 ? 2 : 0)}%`;
      track.append(fill);
      row.append(heading, track);
      return row;
    });
    container.replaceChildren(...rows);
  }

  const rates = data.conversion_rates || {};
  setDashboardText('conversion-view-application', `${Number(rates.view_to_application) || 0}%`);
  setDashboardText('conversion-application-offer', `${Number(rates.application_to_offer) || 0}%`);
}

async function loadDashboard() {
  const refreshButton = document.getElementById('dashboard-refresh');
  const errorBanner = document.getElementById('dashboard-error');
  refreshButton.disabled = true;
  errorBanner.classList.add('hidden');
  setDashboardText('dashboard-updated', 'Đang cập nhật…');

  const endpoints = [
    { path: '/bi/overview/', render: renderOverview, label: 'chỉ số tổng quan', container: null },
    { path: '/bi/skills_demand/?limit=8', render: renderSkillsDemand, label: 'nhu cầu kỹ năng', container: 'skills-chart' },
    { path: '/bi/salary_trends/', render: data => {
      renderSalaryChart('industry-salary-chart', data.by_industry, 'industry', 'Chưa có dữ liệu lương theo ngành.');
      renderSalaryChart('level-salary-chart', data.by_position_level, 'level', 'Chưa có dữ liệu lương theo cấp bậc.');
    }, label: 'xu hướng lương', container: 'industry-salary-chart' },
    { path: '/bi/conversion_funnel/', render: renderFunnel, label: 'phễu tuyển dụng', container: 'funnel-chart' },
  ];

  try {
    const results = await Promise.allSettled(endpoints.map(endpoint => apiGet(endpoint.path, false)));
    const failures = [];
    results.forEach((result, index) => {
      const endpoint = endpoints[index];
      if (result.status === 'fulfilled') {
        endpoint.render(result.value);
        return;
      }

      failures.push(endpoint.label);
      if (endpoint.container) renderError(endpoint.container, `Không thể tải ${endpoint.label}. Vui lòng thử làm mới.`);
      else Object.keys({
        'kpi-total-jobs': 0, 'kpi-active-jobs': 0, 'kpi-candidates': 0,
        'kpi-companies': 0, 'kpi-applications': 0, 'kpi-views': 0,
      }).forEach(id => setDashboardText(id, '—'));
      if (endpoint.path === '/bi/salary_trends/') {
        renderError('level-salary-chart', 'Không thể tải xu hướng lương. Vui lòng thử làm mới.');
      }
      if (endpoint.path === '/bi/conversion_funnel/') {
        setDashboardText('conversion-view-application', '—');
        setDashboardText('conversion-application-offer', '—');
      }
    });

    if (failures.length) {
      errorBanner.textContent = `Không tải được ${failures.join(', ')}. Hãy kiểm tra kết nối tới API rồi thử lại.`;
      errorBanner.classList.remove('hidden');
    }
    setDashboardText('dashboard-updated', `Cập nhật lúc ${new Date().toLocaleTimeString('vi-VN')}`);
  } finally {
    refreshButton.disabled = false;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  updateNavbar();
  document.querySelectorAll('[data-logout]').forEach(element => element.addEventListener('click', handleLogout));
  document.getElementById('dashboard-refresh').addEventListener('click', loadDashboard);
  loadDashboard();
});
