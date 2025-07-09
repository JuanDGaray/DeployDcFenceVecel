document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('[data-delete-action]');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const deleteUrl = button.getAttribute('href');
            // Mostrar el modal de confirmación
            const modal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'));
            modal.show();
            const confirmDeleteButton = document.getElementById('confirmDeleteBtn');
            confirmDeleteButton.onclick = function() {
                console.log('click')
                window.location.href = deleteUrl;
            };
        });
    });
  });
  
  document.addEventListener('DOMContentLoaded', function() {
    window.openPaymentModal = function(invoiceId, paidTotal, invoiceTotal) {
        const modal = new bootstrap.Modal(document.getElementById('attachPaymentModal'));
        const loadingOverlay = document.getElementById('loadingOverlay');
        const csrfToken = document.getElementById('csrf-token').dataset.csrf;
        
        // Set today's date as default
        const today = new Date();
        const todayString = today.toISOString().split('T')[0];
        document.getElementById('paymentDate').value = todayString;
        
        modal.show();
        const amount = document.getElementById('paymentAmount');
        amount.value = paidTotal
        amount.setAttribute('max', invoiceTotal);
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
            
            loadingOverlay.classList.remove('d-none');
            
            fetch(`/projects/{{project.id}}/changePaidInvoice/${invoiceId}`, {
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
            .then(jsonData => {
                console.log('Respuesta del servidor:', jsonData);
                window.location.href = `/projects/{{project.id}}/`;  // Redirigir al proyecto
                loadingOverlay.classList.add('d-none');
            })
            .catch(error => {
                console.error('Error al enviar los datos:', error);
                loadingOverlay.classList.add('d-none');
            });
        };
    };
  });
  
  function showSelectProject() {
    const selectProject = document.getElementById('selectProject');
    selectProject.classList.toggle('d-none');
    ajaxGetRequest(`/get_projects/`, function (data) {
      console.log(data);
  
      const projectSelect = document.getElementById('projectSelect');
      if (typeof data === 'object' && data !== null) {
        let projectOptions = '';
  
        // Iterar sobre los estados y proyectos
        for (const [status, projects] of Object.entries(data)) {
          // Crear un grupo de opciones para cada estado
          const groupOptions = projects.map(project => {
            const sanitizedProjectName = project.project_name.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            return `<option value="${project.id}">${sanitizedProjectName}</option>`;
          }).join('');
  
          // Agregar el grupo al select
          projectOptions += `<optgroup label="${status}">${groupOptions}</optgroup>`;
        }
  
        // Poblar el elemento select, incluyendo un placeholder
        projectSelect.innerHTML = `<option value="" disabled selected>Select a project</option>${projectOptions}`;
      } else {
        // Manejar el caso cuando no hay proyectos disponibles
        projectSelect.innerHTML = `<option value="" disabled>No projects available</option>`;
      }
  
      const spinner_project = document.getElementById('spinner_project');
      spinner_project.classList.add('d-none');
    });
  }
  
  
  function showSelectCustomerProject() {
    const selectCustomerProject = document.getElementById('selectCustomerProject');
    selectCustomerProject.classList.toggle('d-none');
  }
  
  function sendBudgetDuplicate(budgetId ) {
    const selectProject = document.getElementById('projectSelect');
    const projectId = selectProject.value;
    if (projectId === null || projectId === '') {
      showAlert('Please select a project before duplicating the budget.', 'danger');
      return;
    }
    const container = document.getElementById('selectProject');
    const duplicateProjectButton = document.getElementById('duplicateBudgetButton');
    const cancelBudgetDuplicate = document.getElementById('cancelBudgetDuplicateButton');
    duplicateProjectButton.disabled = true;
    duplicateProjectButton.classList.add('bg-secondary');
    duplicateProjectButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Duplicating... ';
    cancelBudgetDuplicate.disabled = true;
    ajaxPostRequest(`/create_copy_budget/${budgetId}/${projectId}/`, {
    }, '{{ csrf_token }}', function(data) {
      if (data.status === 'success') {
        duplicateProjectButton.disabled = false;
        duplicateProjectButton.classList.remove('bg-secondary');
        duplicateProjectButton.innerHTML = 'Duplicate';
        cancelBudgetDuplicate.disabled = false;
        selectProject.value = '';
        container.classList.add('d-none');
        showAlert('Budget duplicated successfully.', 'success');
        window.open(data.redirect, '_blank');
      } else {
        showAlert('Error duplicating budget.', 'danger');
        duplicateProjectButton.disabled = false;
        cancelBudgetDuplicate.disabled = false;
        duplicateProjectButton.classList.remove('bg-secondary');
        duplicateProjectButton.innerHTML = 'Duplicate';
      }
    }, function(error) {
      console.log(error)
      container.classList.add('d-none');
      showAlert('Error duplicating budget.', 'danger');
      duplicateProjectButton.disabled = false;
      duplicateProjectButton.classList.remove('bg-secondary');
      duplicateProjectButton.innerHTML = 'Duplicate';
    });
  }
  
  function sendProjectDuplicate() {
    console.log('sendProjectDuplicate')
    const selectCustomerProject = document.getElementById('selectCustomerProject');
    selectCustomerProject.classList.toggle('d-none');
    const customerId = document.getElementById('id_customer').value;
    const duplicateProjectButton = document.getElementById('duplicateProjectButton');
    duplicateProjectButton.disabled = true;
    duplicateProjectButton.classList.add('bg-secondary');
    if (customerId) {
      duplicateProjectButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Duplicating... ';
      ajaxPostRequest(`/duplicate_project/{{project.id}}/${customerId}/`, {
      }, '{{ csrf_token }}', function(data) {
        console.log(data)
        duplicateProjectButton.disabled = false;
        duplicateProjectButton.classList.remove('bg-secondary');
        duplicateProjectButton.innerHTML = 'Duplicate';
        window.open(data.redirect, '_blank');
  
      });
    } else {
      alert('Please select a customer before duplicating the project.');
    }
  }
  
  function cancelBudgetDuplicate() {
    const container = document.getElementById('selectProject');
    container.classList.add('d-none');
  }