window.openPaymentModal = function(invoiceId, customerName, projectName, totalInvoice, projectId) {

    const modal = new bootstrap.Modal(document.getElementById('attachPaymentModal'));
    const csrfToken = document.getElementById('csrf-token').dataset.csrf;
    console.log(invoiceId, customerName, projectName, totalInvoice, projectId);
    document.getElementById('invoiceId').value = invoiceId;
    document.getElementById('customerName').value = customerName;
    document.getElementById('projectName').value = projectName;
    modal.show();
    loadAccounts();
    const amount = document.getElementById('paymentAmount');
    amount.value = totalInvoice;
    amount.setAttribute('max', totalInvoice);
    amount.addEventListener('input', function() {
      const maxAmount = parseFloat(amount.getAttribute('max'));
      if (parseFloat(amount.value) > maxAmount) {
        amount.value = maxAmount; 
      }
    });
    const confirmPaymentButton = document.getElementById('confirmPaymentBtn');

    confirmPaymentButton.onclick = function() {
        const amount = document.getElementById('paymentAmount').value;
        const date = document.getElementById('paymentDate').value;
        fetch(`/projects/${projectId}/changePaidInvoice/${invoiceId}` , {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,  // Asegúrate de definir csrfToken en tu plantilla
            },
            body: JSON.stringify({
                amount: amount,
                date: date,
            }),
        })
        .then(response => {
            if (response.ok) {
                showAlert('Payment attached successfully', 'success');
                modal.hide();
                loadInvoices(1);
            } else {
                showAlert('Error attaching payment', 'error');
            }
        })
        .catch(error => {
            showAlert('Error attaching payment', 'error');
        });
    };
};

function loadAccounts() {
    const selectAccount = document.getElementById('selectAccount');
    const loadingAccount = document.getElementById('loadingAccount');
    selectAccount.disabled = true;
    ajaxGetRequest(`/accounting/get_accounts_payment/`, function(response) {
        selectAccount.innerHTML = '';
        for (const [parentName, accounts] of Object.entries(response)) {
            const optgroup = document.createElement('optgroup');
            optgroup.label = parentName;
            accounts.forEach(account => {
                const option = document.createElement('option');
                option.value = account.id;
                option.textContent = `${account.code}${account.subcode}${account.subsubcode}${account.groupcode}${account.itemgroupcode}-${account.name} `;
                optgroup.appendChild(option);
                });
            selectAccount.appendChild(optgroup);
        } 
        selectAccount.disabled = false;
        if (!loadingAccount.classList.contains('d-none')) {
            loadingAccount.classList.add('d-none');
        }
    });
}