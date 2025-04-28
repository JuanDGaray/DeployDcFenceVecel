document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('checkbox_start_date').addEventListener('change', function () {
        var startDateInput = document.getElementById('id_start_date');
        startDateInput.disabled = !this.checked;
    });

    document.getElementById('checkbox_end_date').addEventListener('change', function () {
        var endDateInput = document.getElementById('id_end_date');
        endDateInput.disabled = !this.checked;
    });

    const requiredFields = document.querySelectorAll(
        '#id_project_name, #id_customer, #id_description'
    );
    const submitBtn = document.getElementById('submit-btn');

    function checkFormCompletion() {
        let allFieldsFilled = true;

        requiredFields.forEach(function (field) {
            if (field.tagName === 'SELECT') {
                if (field.value === '') {
                    allFieldsFilled = false;
                }
            } else {
                if (field.value.trim() === '') {
                    allFieldsFilled = false;
                }
            }
        });

        submitBtn.disabled = !allFieldsFilled;
    }

    requiredFields.forEach(function (field) {
        field.addEventListener('input', checkFormCompletion);
    });




    const savedScrollTop = localStorage.getItem('scrollTop');
    if (savedScrollTop) {
        window.scrollTo(0, savedScrollTop);
        localStorage.removeItem('scrollTop');
    }

    const saveScrollPosition = () => {
        localStorage.setItem('scrollTop', window.scrollY);
    };

    document.querySelectorAll('.page-link').forEach(link => {
        link.addEventListener('click', saveScrollPosition);
    });
    const addButton = document.getElementById("add-customer-btn");
    const closeForm = document.getElementById("close-form");
    const customerForm = document.getElementById("customer-form");

    function toggleFormVisibility() {
        if (customerForm) {
            customerForm.classList.toggle("visible");
            getCustomer()
        }
    }

    addButton.addEventListener("click", toggleFormVisibility);
    closeForm.addEventListener("click", toggleFormVisibility);


    function searchProjects() {
        const idInput = document.getElementById('searchInputID');
        const nameProjectInput = document.getElementById('searchInputName');
        const statusInput = document.getElementById('searchInputStatus');
        const customerInput = document.getElementById('searchInputCustomer');
        const sellerInput = document.getElementById('searchInputSeller');
        const dateInput = document.getElementById('searchInputDate');
        const tableBody = document.getElementById('resultsTableBody');
        const pagination = document.getElementById('pagination');
        const loader = document.getElementById('loader'); // Indicador de carga

        // Verificar si los inputs existen
        if (!idInput || !nameProjectInput || !statusInput || !customerInput || !sellerInput || !dateInput || !tableBody || !pagination || !loader) {
            console.error("One or more required elements are missing.");
            return;
        }

        // Mostrar el indicador de carga
        loader.classList.remove('d-none');

        // Recuperar valores de los inputs
        const id = encodeURIComponent(idInput.value);
        const projectName = encodeURIComponent(nameProjectInput.value);
        const status = encodeURIComponent(statusInput.value);
        const customer = encodeURIComponent(customerInput.value);
        const seller = encodeURIComponent(sellerInput.value);
        const date = encodeURIComponent(dateInput.value);

        // URL para la búsqueda
        const url = `/search_projects/?id=${id}&project_name=${projectName}&status=${status}&customer=${customer}&seller=${seller}&date=${date}`;

        // Realizar la solicitud
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                tableBody.innerHTML = ''; // Limpiar resultados previos

                if (data.projects.length === 0) {
                    tableBody.innerHTML = '<tr><td colspan="8">No results found</td></tr>';
                } else {
                    // Mostrar solo los primeros 20 resultados
                    data.projects.slice(0, 20).forEach(project => {
                        const rowContent = `
                        <tr>
                            <td>${project.id}</td>
                            <td>${project.created_at}</td>
                            <td><a href="/projects/${project.id}/">${project.project_name}</a></td>
                            <td>
                                <span class="status-empty status_${project.status} m-0">
                                    <strong>•</strong> ${project.status}
                                </span>
                            </td>
                            <td>
                                ${project.customer_type === 'individual'
                                ? `<a href="/customers/${project.customer_id}/">${project.customer_first_name} ${project.customer_last_name} <i class="bi bi-person-arms-up"></i></a>`
                                : `<a href="/customers/${project.customer_id}/">${project.customer_company_name} <i class="bi bi-buildings-fill"></i></a>`
                            }
                            </td>
                            <td>${project.estimated_budget}</td>
                            <td>${project.actual_budget}</td>
                            <td>${project.sales_advisor}</td>
                        </tr>
                    `;
                        tableBody.insertAdjacentHTML('beforeend', rowContent);
                    });
                }

                if (pagination) {
                    const shouldHidePagination = data.projects.length < 20;
                    pagination.classList.toggle('d-none', shouldHidePagination);
                }
            })
            .catch(error => {
                console.error('Error in search:', error);
                alert('There was an error loading the search results. Please try again later.');
            })
            .finally(() => {
                loader.classList.add('d-none');
            });
    }

    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
    document.querySelectorAll('.form-control-search').forEach(input => {
        input.addEventListener('input', debounce(searchProjects, 300));  // 300ms debounce
    });

});

