let isloadPaymentUpload = false;

let emptyTable = '';
for (let i = 0; i < 10; i++) {
    emptyTable += '<tr><td class="text-center placeholder-glow" colspan="9"><span class="placeholder col-12 rounded-4"></span></td></tr>';
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
    const invoicesTableBody = document.getElementById('invoicesTableBody');
    invoicesTableBody.innerHTML = '';

    data.invoices.forEach(invoice => {
        const row = document.createElement('tr');
        
        // Format dates
        const createdDate = new Date(invoice.date_created).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "2-digit"
        });
        
        const dueDate = invoice.due_date ? new Date(invoice.due_date).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "2-digit"
        }) : '';

        // Format currency
        const formatCurrency = (amount) => {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(amount);
        };

        // Create status select options
        const statusOptions = {
            'sent': 'Sent',
            'pending': 'Pending',
            'paid': 'Paid',
            'overdue': 'Overdue',
            'cancelled': 'Cancelled'
        };

        const statusSelect = Object.entries(statusOptions)
            .map(([value, label]) => `
                <option value="${value}" ${invoice.status === value ? 'selected' : ''}>
                    ${label}
                </option>
            `).join('');

        // Create payment button based on payment status
        let paymentButton = '';
        if (invoice.total_paid === 0) {
            paymentButton = `
                <button class="btn btn-success btn-sm" onclick="openPaymentModal('${invoice.id},${invoice.customer_name},${invoice.project_name}', '${invoice.total_invoice}', '${invoice.total_paid}', '${invoice.project_id}')" 
                        title="Attach Payment" data-bs-toggle="tooltip" data-bs-placement="bottom" 
                        data-bs-custom-class="custom-tooltip" data-bs-title="Attach payment">
                    <i class="bi bi-wallet"></i>
                </button>`;
        } else if (invoice.total_paid < invoice.total_invoice) {
            paymentButton = `
                <button class="btn btn-primary btn-sm" onclick="openPaymentModal('${invoice.id},${invoice.customer_name},${invoice.project_name}', '${invoice.total_invoice}', '${invoice.total_paid}', '${invoice.project_id}')" 
                        title="Edit Payment" data-bs-toggle="tooltip" data-bs-placement="bottom" 
                        data-bs-custom-class="custom-tooltip" data-bs-title="Edit payment">
                    <i class="bi bi-pencil"></i>
                </button>`;
        }

        row.innerHTML = `
            <td>${invoice.id}</td>
            <td><a href="/projects/${invoice.project_id}/view_budget/${invoice.budget_id}" target="_blank" class="text-capitalize">${invoice.budget_id}</a></td>
            <td><a href="/projects/${invoice.project_id}" target="_blank" class="text-capitalize">${invoice.project_name}</a></td>
            <td>${createdDate}</td>
            <td>${dueDate}</td>
            <td>${invoice.sales_advisor || ''}</td>
            <td>
                <select name="status" class="status status-empty status_${invoice.status}" onchange="updateInvoiceStatus(${invoice.id}, this)">
                    ${statusSelect}
                </select>
                <span class="spinner-border spinner-border-sm d-none" id="spinner-status-${invoice.id}"  role="status" aria-hidden="true" ></span>
            </td>
            <td class='text-truncate'>${formatCurrency(invoice.total_invoice)} (${invoice.percentage_paid}%)</td>
            <td class='text-truncate'>
                ${formatCurrency(invoice.total_paid)} (${invoice.percentage_paid}%) ${paymentButton}
            </td>
            <td>
                <div class="d-inline-flex gap-2 ">
                <a class="btn bg-light border border-2 btn-sm rounded-2 p-1" 
                    href="/pdf_invoice/${invoice.project_id}/${invoice.id}" 
                    role="button" title="View Invoice" data-bs-toggle="tooltip" 
                    data-bs-placement="bottom" data-bs-custom-class="custom-tooltip" 
                    data-bs-title="View">
                    <i class="bi bi-eye-fill" style="font-size: 15px;"></i>
                </a>
            </td>`;
        
        invoicesTableBody.appendChild(row);
    });

    // Update the count
    document.getElementById('invoices-count').innerHTML = data.total_invoices;
}

async function loadInvoices(page, filters = '', sort = '') {
    let viewQuery = document.querySelector('[data-view]');
    let view = viewQuery ? viewQuery.getAttribute('data-view') : 'view=view_project';
    document.getElementById('invoicesTableBody').innerHTML = emptyTable;
    document.getElementById('invoices-count').innerHTML = '0';
    document.getElementById('paginationInvoices').innerHTML = '';
    const all = document.getElementById('view-all-invoices').checked
    const url = `/get_invoices/${page}/?${filters}&${filters ? '&' : ''}${view}&all=${all}&sort=${sort}`;
    const data = await fetchData(url);
    if (data) {
        renderTable(data);
        document.getElementById('invoices-count').innerHTML = data.total_invoices;
        updatePaginationControls(page, data.has_more, data.total_pages, 'invoices');
    }
}


document.getElementById('paginationInvoices').addEventListener('click', async function (event) {
    const target = event.target.closest('a.page-link');
    console.log(target)
    if (!target) return;

    event.preventDefault();
    const page = target.getAttribute('data-page');
    if (page) {
        await loadInvoices(page);
    }
});




document.getElementById('applyFiltersInvoice').addEventListener('click', async function () {
    let filters = [
        'searchInputInvoiceId',
        'searchInputStatus',
        'searchInputDueDate',
    ]
        .map(id => `${id}=${document.getElementById(id).value}`).join('&');

    await loadInvoices(1, filters);
});

document.getElementById('view-all-invoices').addEventListener('click', async function () {
    await loadInvoices(1);
});



const clearFiltersButton = document.getElementById('clearFiltersInvoice');
if (clearFiltersButton) {
    clearFiltersButton.addEventListener('click', async function () {
        [
            'searchInputInvoiceId',
            'searchInputStatus',
            'searchInputDueDate',
        ]
            .forEach(id => document.getElementById(id).value = '');

        await loadInvoices(1);
    });
}

document.querySelectorAll('[data-sort]').forEach(element => {
    element.addEventListener('click', function () {
        const sortField = this.getAttribute('data-sort');
        let view = document.querySelector('[data-view]');
        let viewValue = view ? view.getAttribute('data-view') : 'view=view_project';
        loadInvoices(1, '', sortField);
    });
});

function updatePaginationControls(currentPage, hasMore, totalPages, type = 'invoices') {
    const pagination = document.getElementById('paginationInvoices');
    if (type == 'invoices') {
        pagination.innerHTML = `
    <li class="page-item ${currentPage == 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${currentPage - 1}"><i class="bi bi-chevron-left"></i></a>
    </li>
    <li class="page-item mx-2"><span>Page ${currentPage} of ${totalPages}</span></li>
    <li class="page-item ${!hasMore ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${+currentPage + 1}"><i class="bi bi-chevron-right"></i></a>
    </li>`;
    } else {
        const pagination = document.getElementById('paginationInvoices');
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

function loadPaymentsReceived() {
    if (!isloadPaymentUpload) {
        isloadPaymentUpload = true;
        loadInvoices(1);
        console.log('loadPaymentsReceived');
    }
}


function updateInvoiceStatus(invoiceId, selectStatus) {
    const status = selectStatus.value;
    const url = `/update_invoice_status/${invoiceId}/`;
    const formData = new FormData();
    const csrfToken = document.getElementById('csrf-token').getAttribute('data-csrf');
    formData.append('status', status);
    document.getElementById(`spinner-status-${invoiceId}`).classList.remove('d-none');
    ajaxPostRequest(url, formData, csrfToken, function(response) {
        console.log(response);
        showAlert('Status updated successfully', 'success');
        document.getElementById(`spinner-status-${invoiceId}`).classList.add('d-none');
    }, function(error) {
        console.log(error);
        showAlert('Error updating status', 'error');
        document.getElementById(`spinner-status-${invoiceId}`).classList.add('d-none');
    });
}


document.addEventListener('DOMContentLoaded', function() {
    const attachReceiptCheck = document.getElementById('attachReceiptCheck');
    const receiptDropArea = document.getElementById('receiptDropArea');
    const receiptFile = document.getElementById('receiptFile');
    const browseReceiptBtn = document.getElementById('browseReceiptBtn');
    const receiptPreview = document.getElementById('receiptPreview');
    const receiptFileName = document.getElementById('receiptFileName');
    const removeReceiptBtn = document.getElementById('removeReceiptBtn');

    // Mostrar/ocultar área de drop
    attachReceiptCheck.addEventListener('change', function() {
        receiptDropArea.classList.toggle('d-none', !this.checked);
        if (!this.checked) {
            receiptPreview.classList.add('d-none');
            receiptFile.value = '';
        }
    });

    // Manejar el botón de búsqueda de archivos
    browseReceiptBtn.addEventListener('click', function() {
        receiptFile.click();
    });

    // Manejar la selección de archivo
    receiptFile.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFileSelection(this.files[0]);
        }
    });

    // Manejar el drag & drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        receiptDropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        receiptDropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        receiptDropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        receiptDropArea.classList.add('bg-light');
    }

    function unhighlight(e) {
        receiptDropArea.classList.remove('bg-light');
    }

    receiptDropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    }

    function handleFileSelection(file) {
        // Validar tipo de archivo
        const validTypes = ['application/pdf', 'image/jpeg', 'image/png'];
        if (!validTypes.includes(file.type)) {
            showAlert('Please upload a valid file type (PDF, JPG, or PNG)', 'error');
            return;
        }

        // Validar tamaño (máximo 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showAlert('File size must be less than 5MB', 'error');
            return;
        }

        // Mostrar preview
        receiptFileName.textContent = file.name;
        receiptPreview.classList.remove('d-none');
    }

    // Manejar eliminación del archivo
    removeReceiptBtn.addEventListener('click', function() {
        receiptFile.value = '';
        receiptPreview.classList.add('d-none');
    });
});
    