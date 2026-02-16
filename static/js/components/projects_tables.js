let emptyTable = '';
for (let i = 0; i < 10; i++) {
    emptyTable += '<tr><td class="text-center placeholder-glow" colspan="8"><span class="placeholder col-12 rounded-4"></span></td></tr>';
}

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

function renderTable(data) {
    const projectsTableBody = document.getElementById('projectsTableBody');
    projectsTableBody.innerHTML = '';

    data.projects.forEach(project => {
        const row = document.createElement('tr');

        // Asegúrate de convertir `created_at` en un objeto `Date`
        const dateVal = project.created_at ? new Date(project.created_at) : null;
        const formattedDate = dateVal && !isNaN(dateVal.getTime())
            ? dateVal.toLocaleDateString("en-US", { day: "numeric", month: "numeric", year: "numeric" })
            : '';

        // Determinar si aplicar blur a los costos
        const blurClass = project.sales_advisor__username == data.current_user.username || data.current_user.is_admin ? '' : 'blur-costs';
        const canViewCosts = project.sales_advisor__username == data.current_user.username || data.current_user.is_admin;

        // Mostrar valores reales o "$0" según permisos (evitar NaN si cost es null)
        const num = (v) => (v != null && v !== '') ? parseInt(v, 10) : 0;
        const estimatedCostDisplay = canViewCosts
            ? (num(project.estimated_cost) || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' })
            : '$0000';
        const actualCostDisplay = canViewCosts
            ? (num(project.actual_cost) || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' })
            : '$0000';

        // Función para truncar texto a 30 caracteres
        const truncateText = (text, maxLength = 30) => {
            const s = (text == null) ? '' : String(text);
            if (s.length <= maxLength) return s;
            return s.substring(0, maxLength) + '...';
        };

        // Valores seguros para nombres (evitar null/undefined al usar [0])
        const safeStr = (v) => (v != null && v !== '') ? String(v) : '';
        const first = safeStr(project.sales_advisor__first_name);
        const last = safeStr(project.sales_advisor__last_name);
        const hasAdvisor = !!(first || last || project.sales_advisor__id);
        const advisorInitials = hasAdvisor ? ((first[0] || '') + (last[0] || '') || '?') : '—';

        // Obtener el nombre del cliente y truncarlo
        const customerName = project.customer__customer_type === 'individual'
            ? `${safeStr(project.customer__first_name)} ${safeStr(project.customer__last_name)}`.trim() || project.customer__company_name
            : (project.customer__company_name != null ? project.customer__company_name : '');
        const truncatedCustomerName = truncateText(customerName);

        row.innerHTML = `
        <td class="position-relative text-center">
            <a href="/projects/${project.id}" class="mt-2" target="_blank">${project.id}</a>
        </td>
        <td class="">${formattedDate}</td>
        <td class="text-truncate" style="max-width: 200px;" title="${project.project_name}" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="${project.project_name}">
            <a href="/projects/${project.id}" target="_blank">
                ${project.project_name}
            </a>
        </td>
        <td class="text-truncate" style="max-width: 120px;">
            <span class="status-empty status_${project.status} ">
                <strong>•</strong> ${project.status === 'planning_and_documentation' ? 'Planning & Doc.' : project.status}
            </span>
        </td>
        <td>
            <a href="/customers/${project.customer}">
                <span class="status title_${project.customer__customer_type} fs-6 text-truncate" title="${customerName}">
                    ${project.customer__customer_type === 'individual' ?
                `${truncatedCustomerName}<i class="bi bi-person-arms-up"></i>` :
                `${truncatedCustomerName}<i class="bi bi-buildings-fill"></i>`}
                </span>
            </a>
        </td>
        <td class="text-center text-truncate d-flex flex-row align-items-center gap-1 flex-nowrap ${!hasAdvisor ? 'text-secondary' : ''}">
            <span
                class="customer-avatar text-light rounded-circle m-0 ${hasAdvisor ? 'bg-primary' : 'bg-secondary'}"
                style="font-size: 0.8rem; font-weight: bold; width: 25px; height: 25px;">
                ${advisorInitials}
            </span>
            ${hasAdvisor && project.sales_advisor__id
                ? `<a href="/users/${project.sales_advisor__id}" target="_blank" class="text-decoration-none text-dark">${first ? first.split(' ')[0] : ''} ${last ? last.split(' ')[0] : ''}</a>`
                : `<span class="fst-italic">${first || last ? ((first ? first.split(' ')[0] : '') + ' ' + (last ? last.split(' ')[0] : '')).trim() : '—'}</span>`}
        </td>
        <td class="text-truncate ${blurClass}"> ${estimatedCostDisplay}</td>
        ${project.estimated_cost > project.actual_cost || project.actual_cost === 0
                ? `<td class="${blurClass}"><span class="status title_budgetUp text-truncate"><i class="bi bi-graph-up-arrow fs-6"></i> ${actualCostDisplay}</span></td>`
                : `<td class="${blurClass}"><span class="status title_budgetDown text-truncate"><i class="bi bi-graph-down-arrow fs-6"></i> ${actualCostDisplay}</span></td>`}           
        <td class="text-center">
            <button class="btn btn-primary btn-sm rounded-2 p-1 modal-open button-show_project" 
                    id='button-show_project' 
                    onclick="openModal(event, project_id='${project.id}',proposal_id='None', object='project')"
                    ${!canViewCosts ? 'disabled' : ''}
                    ${!canViewCosts ? 'style="opacity: 0.5; cursor: not-allowed;"' : ''}>
                <i class="bi bi-eye-fill"></i>
            </button>
        </td>`;
        projectsTableBody.appendChild(row);
    });
}

async function loadProjects(page, filters = '', sort = '') {
    let viewQuery = document.querySelector('[data-view]');
    let view = viewQuery ? viewQuery.getAttribute('data-view') : 'view=view_project';
    document.getElementById('projectsTableBody').innerHTML = emptyTable;
    document.getElementById('projects-count').innerHTML = '0';
    document.getElementById('paginationProjects').innerHTML = '';
    const all = document.getElementById('view-all-projects').checked
    const onlyMe = document.getElementById('view-only-me').checked
    const params = new URLSearchParams();
    const viewVal = (view && view.includes('=')) ? view.split('=')[1] : (view || 'view_project');
    params.set('view', viewVal);
    params.set('all', all);
    params.set('only-me', onlyMe);
    if (sort) params.set('sort', sort);
    if (filters) {
        filters.split('&').forEach(pair => {
            const eq = pair.indexOf('=');
            if (eq > 0) {
                const k = pair.slice(0, eq);
                const v = pair.slice(eq + 1);
                if (v) params.set(k, decodeURIComponent(v));
            }
        });
    }
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
        const filters = [
            'searchInputProjectId',
            'searchInputProjectName',
            'searchInputStatus',
            'searchInputDueDate',
        ].map(id => `${id}=${encodeURIComponent(document.getElementById(id).value || '')}`).join('&');
        await loadProjects(page, filters, '');
    }
});




document.getElementById('applyFiltersProject').addEventListener('click', async function () {
    let filters = [
        'searchInputProjectId',
        'searchInputProjectName',
        'searchInputStatus',
        'searchInputDueDate',
    ]
        .map(id => `${id}=${document.getElementById(id).value}`).join('&');

    await loadProjects(1, filters);
});

document.getElementById('view-all-projects').addEventListener('click', async function () {
    await loadProjects(1);
});



document.getElementById('clearFilters').addEventListener('click', async function () {
    [
        'searchInputProjectId',
        'searchInputProjectName',
        'searchInputStatus',
        'searchInputDueDate',
    ]
        .forEach(id => document.getElementById(id).value = '');

    await loadProjects(1);
});

document.querySelectorAll('[data-sort]').forEach(element => {
    element.addEventListener('click', function () {
        const sortField = this.getAttribute('data-sort');
        let view = document.querySelector('[data-view]');
        let viewValue = view ? view.getAttribute('data-view') : 'view=view_project';
        loadProjects(1, '', sortField);
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
    loadProjects(1);
    
    // Event listeners para checkboxes mutuamente excluyentes
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