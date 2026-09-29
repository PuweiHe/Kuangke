const yearSelect = document.querySelector('#year');
const branchSelect = document.querySelector('#branch');
const status = document.querySelector('#status');
const output = {
  total: document.querySelector('#total'),
  count: document.querySelector('#count'),
  share: document.querySelector('#share'),
  growth: document.querySelector('#growth'),
  rows: document.querySelector('#rows'),
  year: document.querySelector('#year-label'),
};

function percent(value) {
  return value === null ? 'No baseline' : `${(value * 100).toFixed(1)}%`;
}

async function jsonResponse(url) {
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}

function render(report) {
  output.total.textContent = report.total_revenue_million.toFixed(1);
  output.count.textContent = String(report.branches.length);
  output.share.textContent = report.selected_branch ? (report.selected_branch.share === null ? 'Undefined' : percent(report.selected_branch.share)) : 'Choose a branch';
  output.growth.textContent = report.selected_branch ? percent(report.selected_branch.growth) : 'Choose a branch';
  output.year.textContent = `${report.year} · synthetic observations`;
  output.rows.replaceChildren();
  report.branches.forEach((branch, index) => {
    const row = document.createElement('tr');
    if (branch.branch_id === branchSelect.value) row.className = 'selected';
    const values = [String(index + 1), branch.branch_id, branch.revenue_million.toFixed(1), branch.share === null ? 'Undefined' : percent(branch.share), percent(branch.growth)];
    values.forEach(value => {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.append(cell);
    });
    output.rows.append(row);
  });
}

async function loadReport(resetBranch = false) {
  status.textContent = 'Loading metrics…';
  yearSelect.disabled = true;
  branchSelect.disabled = true;
  try {
    if (resetBranch) branchSelect.value = '';
    const params = new URLSearchParams({ year: yearSelect.value });
    if (branchSelect.value) params.set('branch_id', branchSelect.value);
    const report = await jsonResponse(`/api/metrics?${params}`);
    if (resetBranch || branchSelect.options.length <= 1) {
      branchSelect.replaceChildren(new Option('All branches', ''));
      report.branches.forEach(branch => branchSelect.add(new Option(branch.branch_id, branch.branch_id)));
    }
    render(report);
    status.textContent = 'Showing local sample data';
  } catch (error) {
    status.textContent = `Unable to load: ${error.message}`;
  } finally {
    yearSelect.disabled = false;
    branchSelect.disabled = false;
  }
}

yearSelect.addEventListener('change', () => loadReport(true));
branchSelect.addEventListener('change', () => loadReport());

(async () => {
  try {
    const data = await jsonResponse('/api/years');
    data.years.forEach(year => yearSelect.add(new Option(String(year), String(year))));
    if (data.years.length) await loadReport(true);
    else status.textContent = 'No sample years available';
  } catch (error) {
    status.textContent = `Unable to load: ${error.message}`;
  }
})();
