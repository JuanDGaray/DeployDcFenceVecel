let emptyTable = '';
for (let i = 0; i < 10; i++) {
    emptyTable += '<tr><td class="text-center placeholder-glow" colspan="9"><span class="placeholder col-12 rounded-2"></span></td></tr>';
}

const PROJECT_STATUS_LABELS = {
    new: 'New',
    sent: 'Sent',
    pending: 'Pending',
    approved: 'Approved',
    rejected: 'Rejected',
    cancelled: 'Cancelled',
    planning_and_documentation: 'Planning & Doc.',
    in_production: 'In production',
    pending_payment: 'Pending payment',
    completed: 'Completed',
};

async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching data:', error);
        return null;
    }
}

function formatStatusLabel(status) {
    if (!status) return '—';
    return PROJECT_STATUS_LABELS[status] || String(status).replace(/_/g, ' ');
}

function realCostTone(estimated, actual) {
    if (!actual || actual <= 0) {
        return { className: 'title_budgetNeutral', icon: 'bi-dash' };
    }
    if (!estimated || estimated <= 0 || actual >= estimated) {
        return { className: 'title_budgetDown', icon: 'bi-graph-down-arrow' };
    }
    return { className: 'title_budgetUp', icon: 'bi-graph-up-arrow' };
}

function renderTable(data) {
    const projectsTableBody = document.getElementById('projectsTableBody');
    projectsTableBody.innerHTML = '';

    data.projects.forEach(project => {
        const row = document.createElement('tr');
        row.className = 'projects-row';

        const dateVal = project.created_at ? new Date(project.created_at) : null;
        const formattedDate = dateVal && !isNaN(dateVal.getTime())
            ? dateVal.toLocaleDateString('en-US', { day: 'numeric', month: 'numeric', year: 'numeric' })
            : '';

        const blurClass = project.sales_advisor__username == data.current_user.username || data.current_user.is_admin ? '' : 'blur-costs';
        const canViewCosts = project.sales_advisor__username == data.current_user.username || data.current_user.is_admin;

        const num = (v) => (v != null && v !== '') ? Number(v) : 0;
        const estimated = num(project.estimated_cost);
        const actual = num(project.actual_cost);
        const estimatedCostDisplay = canViewCosts
            ? (estimated || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' })
            : '$0000';
        const actualCostDisplay = canViewCosts
            ? (actual || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' })
            : '$0000';
        const realTone = realCostTone(estimated, actual);

        const truncateText = (text, maxLength = 30) => {
            const s = (text == null) ? '' : String(text);
            if (s.length <= maxLength) return s;
            return s.substring(0, maxLength) + '...';
        };

        const safeStr = (v) => (v != null && v !== '') ? String(v) : '';
        const first = safeStr(project.sales_advisor__first_name);
        const last = safeStr(project.sales_advisor__last_name);
        const hasAdvisor = !!(first || last || project.sales_advisor__id);
        const advisorInitials = hasAdvisor ? ((first[0] || '') + (last[0] || '') || '?') : '—';

        const customerName = project.customer__customer_type === 'individual'
            ? `${safeStr(project.customer__first_name)} ${safeStr(project.customer__last_name)}`.trim() || project.customer__company_name
            : (project.customer__company_name != null ? project.customer__company_name : '');
        const truncatedCustomerName = truncateText(customerName);
        const customerIcon = project.customer__customer_type === 'individual' ? 'bi-person' : 'bi-buildings';
        const projectName = safeStr(project.project_name);
        const statusLabel = formatStatusLabel(project.status);

        row.innerHTML = `
        <td class="text-center projects-id-cell">
            <a href="/projects/${project.id}" class="projects-id-link" target="_blank">${project.id}</a>
        </td>
        <td class="text-muted projects-date-cell">${formattedDate}</td>
        <td class="text-truncate projects-name-cell" style="max-width: 220px;" title="${projectName}">
            <a href="/projects/${project.id}" target="_blank" class="projects-name-link fw-semibold text-decoration-none">
                ${projectName}
            </a>
        </td>
        <td class="text-truncate" style="max-width: 140px;">
            <span class="status-empty status_${project.status}">
                ${statusLabel}
            </span>
        </td>
        <td>
            <a href="/customers/${project.customer}" class="text-decoration-none">
                <span class="status title_${project.customer__customer_type} projects-customer-chip text-truncate" title="${customerName}">
                    <i class="bi ${customerIcon} me-1"></i>${truncatedCustomerName}
                </span>
            </a>
        </td>
        <td class="text-truncate ${!hasAdvisor ? 'text-secondary' : ''}">
            <div class="d-inline-flex align-items-center gap-1 flex-nowrap">
                <span
                    class="customer-avatar text-light rounded-circle m-0 ${hasAdvisor ? 'bg-primary' : 'bg-secondary'}"
                    style="font-size: 0.7rem; font-weight: bold; width: 22px; height: 22px; display:inline-flex; align-items:center; justify-content:center;">
                    ${advisorInitials}
                </span>
                ${hasAdvisor && project.sales_advisor__id
                    ? `<a href="/users/${project.sales_advisor__id}" target="_blank" class="text-decoration-none text-dark projects-advisor-name">${first ? first.split(' ')[0] : ''} ${last ? last.split(' ')[0] : ''}</a>`
                    : `<span class="fst-italic projects-advisor-name">${first || last ? ((first ? first.split(' ')[0] : '') + ' ' + (last ? last.split(' ')[0] : '')).trim() : '—'}</span>`}
            </div>
        </td>
        <td class="text-end text-truncate ${blurClass}">${estimatedCostDisplay}</td>
        <td class="text-end ${blurClass}">
            <span class="status ${realTone.className} text-truncate projects-real-chip">
                <i class="bi ${realTone.icon}"></i> ${actualCostDisplay}
            </span>
        </td>
        <td class="text-center">
            <button class="btn btn-outline-secondary btn-sm rounded-1 p-1 modal-open button-show_project"
                    type="button"
                    onclick="openModal(event, project_id='${project.id}',proposal_id='None', object='project')"
                    ${!canViewCosts ? 'disabled' : ''}
                    ${!canViewCosts ? 'style="opacity: 0.45; cursor: not-allowed;"' : ''}
                    title="Quick view">
                <i class="bi bi-eye"></i>
            </button>
        </td>`;
        projectsTableBody.appendChild(row);
    });
}

const PROJECT_FILTER_IDS = [
    'searchInputProjectId',
    'searchInputProjectName',
    'searchInputStatus',
    'searchInputDueDate',
];
const PROJECTS_FILTER_STORAGE_KEY = 'projectsListFilters';
let currentProjectsSort = '';

function readProjectFiltersFromDom() {
    const filters = {};
    PROJECT_FILTER_IDS.forEach((id) => {
        const el = document.getElementById(id);
        filters[id] = el ? (el.value || '').trim() : '';
    });
    return filters;
}

function writeProjectFiltersToDom(filters) {
    if (!filters) return;
    PROJECT_FILTER_IDS.forEach((id) => {
        const el = document.getElementById(id);
        if (el && filters[id] != null) {
            el.value = filters[id];
        }
    });
    const allEl = document.getElementById('view-all-projects');
    const onlyMeEl = document.getElementById('view-only-me');
    if (allEl) allEl.checked = !!filters.all;
    if (onlyMeEl) onlyMeEl.checked = !!filters.onlyMe;
    if (filters.sort) currentProjectsSort = filters.sort;
}

function persistProjectFilters(page, sort) {
    const filters = readProjectFiltersFromDom();
    const state = {
        ...filters,
        all: document.getElementById('view-all-projects')?.checked || false,
        onlyMe: document.getElementById('view-only-me')?.checked || false,
        sort: sort || currentProjectsSort || '',
        page: page || 1,
    };
    try {
        sessionStorage.setItem(PROJECTS_FILTER_STORAGE_KEY, JSON.stringify(state));
    } catch (e) {}

    const url = new URL(window.location.href);
    PROJECT_FILTER_IDS.forEach((id) => {
        if (state[id]) url.searchParams.set(id, state[id]);
        else url.searchParams.delete(id);
    });
    if (state.all) url.searchParams.set('all', '1');
    else url.searchParams.delete('all');
    if (state.onlyMe) url.searchParams.set('only-me', '1');
    else url.searchParams.delete('only-me');
    if (state.sort) url.searchParams.set('sort', state.sort);
    else url.searchParams.delete('sort');
    if (state.page && Number(state.page) > 1) url.searchParams.set('page', String(state.page));
    else url.searchParams.delete('page');
    window.history.replaceState({}, '', url);
}

function restoreProjectFilters() {
    const url = new URL(window.location.href);
    const fromUrl = {};
    let hasUrl = false;
    PROJECT_FILTER_IDS.forEach((id) => {
        if (url.searchParams.has(id)) {
            fromUrl[id] = url.searchParams.get(id) || '';
            hasUrl = true;
        }
    });
    if (url.searchParams.get('all') === '1' || url.searchParams.get('all') === 'true') {
        fromUrl.all = true;
        hasUrl = true;
    }
    if (url.searchParams.get('only-me') === '1' || url.searchParams.get('only-me') === 'true') {
        fromUrl.onlyMe = true;
        hasUrl = true;
    }
    if (url.searchParams.get('sort')) {
        fromUrl.sort = url.searchParams.get('sort');
        hasUrl = true;
    }
    if (url.searchParams.get('page')) {
        fromUrl.page = parseInt(url.searchParams.get('page'), 10) || 1;
        hasUrl = true;
    }
    if (hasUrl) {
        writeProjectFiltersToDom(fromUrl);
        return fromUrl;
    }

    try {
        const raw = sessionStorage.getItem(PROJECTS_FILTER_STORAGE_KEY);
        if (!raw) return { page: 1 };
        const saved = JSON.parse(raw);
        writeProjectFiltersToDom(saved);
        return saved;
    } catch (e) {
        return { page: 1 };
    }
}

async function loadProjects(page, sort) {
    let viewQuery = document.querySelector('[data-view]');
    let view = viewQuery ? viewQuery.getAttribute('data-view') : 'view=view_project';
    document.getElementById('projectsTableBody').innerHTML = emptyTable;
    document.getElementById('projects-count').innerHTML = '0';
    document.getElementById('paginationProjects').innerHTML = '';

    const filters = readProjectFiltersFromDom();
    const all = document.getElementById('view-all-projects').checked;
    const onlyMe = document.getElementById('view-only-me').checked;
    if (typeof sort === 'string') {
        currentProjectsSort = sort;
    }
    const activeSort = currentProjectsSort || '';

    const params = new URLSearchParams();
    const viewVal = (view && view.includes('=')) ? view.split('=')[1] : (view || 'view_project');
    params.set('view', viewVal);
    params.set('all', all);
    params.set('only-me', onlyMe);
    if (activeSort) params.set('sort', activeSort);
    PROJECT_FILTER_IDS.forEach((id) => {
        if (filters[id]) params.set(id, filters[id]);
    });

    persistProjectFilters(page, activeSort);

    const url = `/get_projects/${page}/?${params.toString()}`;
    const data = await fetchData(url);
    if (data) {
        renderTable(data);
        document.getElementById('projects-count').innerHTML = data.total_projects;
        updatePaginationControls(page, data.has_more, data.total_pages, 'projects');
    }
}


document.getElementById('paginationProjects').addEventListener('click', async function (event) {
    const target = event.target.closest('a.page-link');
    if (!target) return;
    if (target.closest('li.page-item.disabled')) return;

    event.preventDefault();
    const page = target.getAttribute('data-page');
    if (page && parseInt(page, 10) >= 1) {
        await loadProjects(page);
    }
});

document.getElementById('applyFiltersProject').addEventListener('click', async function () {
    await loadProjects(1);
});

PROJECT_FILTER_IDS.forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            loadProjects(1);
        }
    });
});

document.getElementById('clearFilters').addEventListener('click', async function () {
    PROJECT_FILTER_IDS.forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    currentProjectsSort = '';
    try {
        sessionStorage.removeItem(PROJECTS_FILTER_STORAGE_KEY);
    } catch (e) {}
    await loadProjects(1);
});

document.querySelectorAll('[data-sort]').forEach(element => {
    element.addEventListener('click', function () {
        const sortField = this.getAttribute('data-sort');
        loadProjects(1, sortField);
    });
});

function updatePaginationControls(currentPage, hasMore, totalPages, type = 'proposals') {
    const pagination = document.getElementById('pagination');
    if (type == 'proposals') {
        pagination.innerHTML = `
    <li class="page-item ${currentPage == 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${currentPage - 1}"><i class="bi bi-chevron-left"></i></a>
    </li>
    <li class="page-item mx-2"><span>Page ${currentPage} of ${totalPages}</span></li>
    <li class="page-item ${!hasMore ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${+currentPage + 1}"><i class="bi bi-chevron-right"></i></a>
    </li>`;
    } else {
        const pagination = document.getElementById('paginationProjects');
        pagination.innerHTML = `
    <ul class="pagination mb-0 paginationProjects">
    <li class="page-item ${currentPage == 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${currentPage - 1}"><i class="bi bi-chevron-left"></i></a>
    </li>
    <li class="page-item mx-2"><span class="page-link border-0 bg-transparent">Page ${currentPage} of ${totalPages}</span></li>
    <li class="page-item ${!hasMore ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${+currentPage + 1}"><i class="bi bi-chevron-right"></i></a>
    </li>
    </ul>`;
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const restored = restoreProjectFilters();
    const startPage = restored && restored.page ? restored.page : 1;
    loadProjects(startPage);

    document.getElementById('view-all-projects').addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('view-only-me').checked = false;
        }
        loadProjects(1);
    });

    document.getElementById('view-only-me').addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('view-all-projects').checked = false;
        }
        loadProjects(1);
    });
});
