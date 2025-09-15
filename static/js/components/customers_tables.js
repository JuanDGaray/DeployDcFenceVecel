let emptyTable = '';
for (let i = 0; i < 15; i++) {
    emptyTable += '<tr><td class="text-center placeholder-glow py-2" colspan="8"><span class="placeholder col-12 rounded-4 my-1"></span></td></tr>';
}


document.addEventListener('DOMContentLoaded', function () {
    loadCustomers(1);
});


let lastCustomerFilters = '';
let lastCustomerSort = 'false';

async function loadCustomers(page, filters = '', sort = 'false') {
    document.getElementById('customersTableBody').innerHTML = emptyTable;
    document.getElementById('customers-count').innerHTML = '0';
    document.getElementById('paginationCustomers').innerHTML = '';
    const all = document.getElementById('view-all-customers').checked
    // Persist last used filters and sort so pagination keeps them
    if (typeof filters === 'string') {
        lastCustomerFilters = filters;
    }
    if (typeof sort === 'string') {
        lastCustomerSort = sort;
    }

    // Build URL with filters as real query params (not nested under a single "filters" key)
    const queryFilters = lastCustomerFilters ? `&${lastCustomerFilters}` : '';
    const url = `/get_customers_primary_info/?page=${page}${queryFilters}&sort=${lastCustomerSort}&all=${all}`;
    const data = await fetchData(url);
    if (data) {
        renderTable(data);
        document.getElementById('customers-count').innerHTML = data.total_customers;
        updatePaginationControls(page, data.has_more, data.total_pages, 'customers');
    }
}

function renderTable(data) {
    const tableBody = document.getElementById('customersTableBody');
    tableBody.innerHTML = '';
    data.customers.forEach(customer => {
        tableBody.innerHTML += `
            <tr>
                <td class="text-center">${customer.id}</td>
                 <td class="text-truncate" style="max-width: 300px;">
                    <a href="/customers/${customer.id}">
                        ${customer.customer_type == "individual" ? `
                    <span class="status title_${customer.customer_type} fs-6">
                    ${customer.first_name} ${customer.last_name} <i class="bi bi-person-arms-up"></i>
                    </span>
                    </a> ` : `
                    <a href="/customers/${customer.id}" class="d-flex flex-row justify-content-start">
                        <span class="status title_${customer.customer_type} fs-6 text-truncate" style="width: 200px; min-width: 200px;"><i class="bi bi-buildings-fill"></i> ${customer.company_name} 
                    </span> 
                    <span class="text-truncate" style="width: 100px; min-width: 100px;">
                    ${customer.first_name} ${customer.last_name}
                    </span>
                    </a>
                    `}
                    </td>
                <td>
                    <span class="status status_${customer.customer_type} m-0 text-center">
                      ${customer.customer_type}
                    <span>
                  </td>
                <td class="">
                    <span class="status-empty status_${customer.status} m-0 text-center">
                      <strong>•</strong> ${customer.status}
                    <span>
                </td>
                <td>
                    <a href="https://wa.me/+${customer.phone}" target="_blank" class='btn btn-sm border border-2 border-success font-light p-1'>
                        <i class="bi bi-whatsapp text-success"></i>
                    </a> 
                    ${customer.phone}
                </td>
                <td>
                    <a  href="https://mail.google.com/mail/?view=cm&fs=1&to=${customer.email}"  target="_blank"   class='btn btn-sm btn-primary p-1'><i class="bi bi-envelope-arrow-down"></i></a> ${customer.email}
                </td>
                <td class="text-center d-flex flex-row justify-content-center align-items-center gap-1 flex-nowrap">
                <span
                    class="customer-avatar text-light rounded-circle m-0 bg-primary"
                    style="font-size: 0.8rem; font-weight: bold; width: 25px; height: 25px;">
                    ${customer.sales_advisor__first_name[0] + customer.sales_advisor__last_name[0]}
                </span> 
                ${customer.sales_advisor__first_name} ${customer.sales_advisor__last_name}
                </td>
            </tr>
        `;
    });
}

function updatePaginationControls(currentPage, hasMore, totalPages, type = 'customers') {
    const pagination = document.getElementById('paginationCustomers');
    if (type == 'customers') {
        pagination.innerHTML = `
    <li class="page-item ${currentPage == 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${currentPage - 1}"><i class="bi bi-chevron-left"></i></a>
    </li>
    <li class="page-item mx-2"><span>Page ${currentPage} of ${totalPages}</span></li>
    <li class="page-item ${!hasMore ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${+currentPage + 1}"><i class="bi bi-chevron-right"></i></a>
    </li>`;
    } else {
        const pagination = document.getElementById('paginationCustomers');
        pagination.innerHTML = `
    <li class="page-item ${currentPage == 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${currentPage - 1}"><i class="bi bi-chevron-left"></i></a>
    </li>
    <li class="page-item mx-2"><span>Page ${currentPage} of ${totalPages}</span></li>
    <li class="page-item ${!hasMore ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${+currentPage + 1}"><i class="bi bi-chevron-right"></i></a>
    </li>`;
    }
}

document.getElementById('paginationCustomers').addEventListener('click', async function (event) {

    const target = event.target.closest('a.page-link');
    if (!target) return;

    event.preventDefault();
    const page = target.getAttribute('data-page');
    if (page) {
        await loadCustomers(page, lastCustomerFilters, lastCustomerSort);
    }
});

document.getElementById('applyFiltersCustomer').addEventListener('click', async function () {
    let filters = [
        'searchInputCustomerName',
        'searchInputCustomerCompanyOrContractor',
        'searchInputCustomerType',
        'searchInputCustomerStatus',
        'searchInputCustomerEmail',
        'searchInputSeller',
    ]
        .map(id => `${id}=${encodeURIComponent(document.getElementById(id).value)}`).join('&');
    console.log(filters);
    await loadCustomers(1, filters, 'false');
});

document.getElementById('clearFilters').addEventListener('click', async function () {       
    lastCustomerFilters = '';
    await loadCustomers(1, '', lastCustomerSort);
});

document.querySelectorAll('[data-sort]').forEach(element => {
    element.addEventListener('click', async function () {
        let sort = element.dataset.sort;
        if (element.classList.contains('bi-sort-down')) {
            element.classList.remove('bi-sort-down');
            element.classList.add('bi-sort-up');
            sort = '-' + sort;
        } else {
            element.classList.remove('bi-sort-up');
            element.classList.add('bi-sort-down');
            sort = sort;
        }
        await loadCustomers(1, lastCustomerFilters, sort);
    });
}); 

document.getElementById('view-all-customers').addEventListener('click', async function () {
    await loadCustomers(1);
});



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
