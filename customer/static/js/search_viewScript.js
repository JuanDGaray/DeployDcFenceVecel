document.addEventListener('DOMContentLoaded', function () {
    // Form Scripts
    const customerType = document.getElementById('id_customer_type');
    const companyName = document.getElementById('id_company_name');

    // Función para activar/desactivar el campo 'Company Name'
    function toggleCompanyNameField() {
    if (customerType.value === 'company' || customerType.value === 'contractor') {
        companyName.disabled = false;
    } else {
        companyName.disabled = true;
        companyName.value = '';
    }
    }

    const requiredFields = document.querySelectorAll('#id_first_name, #id_last_name, #id_email, #id_phone');
    const submitBtn = document.getElementById('submit-btn');

    function checkFormCompletion() {
    let allFieldsFilled = true;

    requiredFields.forEach(function(field) {
        if (field.value.trim() === '') {
        allFieldsFilled = false; 
        }
    });

    submitBtn.disabled = !allFieldsFilled;
    document.getElementById('id_email').addEventListener('input', function() {
        const emailInput = this.value;
        const emailError = document.getElementById('email-error');
    
        if (emailInput.trim() !== '') {
        fetch(`/check-email/?email=${emailInput}`)
            .then(response => response.json())
            .then(data => {
            if (data.exists) { 
                emailError.style.display = 'inline';
                submitBtn.disabled = true
            } else {
                emailError.style.display = 'none'; 
                submitBtn.disabled = !allFieldsFilled;
            }
            })
            .catch(error => {
            console.error('Error checking email:', error);
            });
        } else {
        emailError.style.display = 'none';
        }
    });

    }

    // Escuchar cambios en los campos requeridos
    requiredFields.forEach(function(field) {
    field.addEventListener('input', checkFormCompletion);
    });


    customerType.addEventListener('change', toggleCompanyNameField);



    // Restaurar la posición de desplazamiento
    const savedScrollTop = localStorage.getItem('scrollTop');
    if (savedScrollTop) {
        window.scrollTo(0, savedScrollTop);
        localStorage.removeItem('scrollTop');
    }

    // Guardar la posición de desplazamiento antes de cambiar de página
    const saveScrollPosition = () => {
        localStorage.setItem('scrollTop', window.scrollY);
    };

    // Guardar la posición de desplazamiento cuando se hace clic en enlaces de paginación
    document.querySelectorAll('.page-link').forEach(link => {
        link.addEventListener('click', saveScrollPosition);
    });
    const addButton = document.getElementById("add-customer-btn");
    const closeForm = document.getElementById("close-form");
    const customerForm = document.getElementById("customer-form");

    function toggleFormVisibility() {
        if (customerForm) {
            customerForm.classList.toggle("visible");
        }
    }

    addButton.addEventListener("click", toggleFormVisibility);
    closeForm.addEventListener("click", toggleFormVisibility);

    function searchCustomers() {
    const nameInput = document.getElementById('searchInputName');
    const companyInput = document.getElementById('searchInputCompany');
    const emailInput = document.getElementById('searchInputEmail');
    const sellerInput = document.getElementById('searchInputSeller');
    const dateInput = document.getElementById('searchInputDate');
    const statusInput = document.getElementById('searchInputStatus');

    if (!nameInput || !companyInput || !emailInput || !sellerInput || !dateInput || !statusInput) {
        console.error("One or more search input elements are missing.");
        return;
    }

    const name = encodeURIComponent(nameInput.value);
    const company = encodeURIComponent(companyInput.value);
    const email = encodeURIComponent(emailInput.value);
    const seller = encodeURIComponent(sellerInput.value);
    const date = encodeURIComponent(dateInput.value);
    const status = encodeURIComponent(statusInput.value);

    // Reemplaza con la URL correcta de tu vista
    const url = `/search_customers/?name=${name}&company=${company}&email=${email}&seller=${seller}&date=${date}&status=${status}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('resultsTableBody');
            if (tableBody) {
                tableBody.innerHTML = '';

                // Solo muestra los primeros 20 resultados
                const resultsToShow = data.customers.slice(0, 20);

                if (resultsToShow.length === 0) {
                    tableBody.innerHTML = '<tr><td colspan="8">No results found</td></tr>';
                    
                } else {
                    const pagination = document.getElementById('pagination')
                    resultsToShow.forEach(client => {
                        const logo = client.customer_type === 'individual'
                            ? ''
                            : `<span class="btn-info rounded p-1"> <i class="bi bi-buildings-fill"></i> ${client.company_name}</span> |`; // Icono para 'company'
                        
                        let rowContent;
                        if (client.customer_type === "individual") {
                            rowContent = `
                                <td>
                                    <a href="/customers/${client.id}/">
                                        <span class="status title_${client.customer_type} fs-6">
                                            ${client.first_name} ${client.last_name} <i class="bi bi-person-arms-up"></i>
                                        </span>
                                    </a>
                                </td>
                            `;
                        } else {
                            rowContent = `
                                <td>
                                    <a href="/customers/${client.id}/">
                                        <span class="status title_${client.customer_type} fs-6">
                                            ${client.company_name} <i class="bi bi-buildings-fill"></i>
                                        </span>
                                    </a>
                                    ${client.first_name} ${client.last_name}
                                </td>
                            `;
                        }
                        const row = `
                            <tr>
                                <td>${client.id}</td>
                                ${rowContent}
                                <td>
                                    <span class="status status_${client.customer_type} m-0">${client.customer_type}</span>
                                </td>
                                <td>
                                    <span class="status-empty status_${client.status} m-0">
                                        <strong>•</strong> ${client.status}
                                    </span>
                                </td>
                                <td>${client.email}</td>
                                <td>${client.phone}</td>
                                <td>${client.date_created}</td>
                                <td>${client.sales_advisor}</td>
                            </tr>
                        `;
                        tableBody.insertAdjacentHTML('beforeend', row);
                    });
                    
                }
                if (pagination) {
                    const shouldHidePagination = data.customers.length < 20;
                    pagination.classList.toggle('d-none', shouldHidePagination);
                }
            } else {
                console.error("El elemento 'resultsTableBody' no existe.");
            }
        })
        .catch(error => console.error('Error en la búsqueda:', error));
}


    // Agregar eventos para realizar la búsqueda cuando cambie el input
    document.querySelectorAll('.form-control-search').forEach(input => {
        input.addEventListener('input', searchCustomers);  // Buscar resultados en tiempo real
    });
});



const ctx = document.getElementById('historyChart').getContext('2d');
const historyChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], // Puedes poner fechas aquí
        datasets: [{
            label: 'Customer Registrations',
            data: [12, 19, 8, 25, 17, 21, 15], // Datos de ejemplo, ajusta según tu histórico diario
            borderColor: 'rgba(75, 192, 192, 1)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            tension: 0.4, // Para darle el efecto de onda
            fill: true
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        },
        responsive: true,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                enabled: true
            }
        }
    }
});
