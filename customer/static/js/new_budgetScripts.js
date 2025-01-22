const $ = el => document.querySelector(el)
const $$ = el => document.querySelectorAll(el)
const $$$ = el => document.getElementById(el)


function createLaborRow(data = null) {
    const tbodyLabor = document.getElementById('labor-section');
    const rowCountLabor = tbodyLabor.querySelectorAll('tr').length; // Correct row count
    const newRowLabor = document.createElement('tr');
    
    // Si hay datos, completar con los valores proporcionados; si no, dejar en blanco
    newRowLabor.innerHTML = `
        <td class="text-center p-0"><strong>${rowCountLabor + 1}</strong></td> <!-- Asegurarse de mostrar la fila correcta -->
        <td colspan="2" class="p-0">
            <div class="d-flex align-items-center">
                <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                    <option value="${data ? data.item_value : 'GENERAL'}">${data ? data.item_value : 'GENERAL'}</option>
                </select>
                <input class="form-control-budget" type="text" id="laborDescInput" name="Labor_desc" value="${data ? data.labor_description : ''}">
            </div>
        </td>
        <td class="p-0">
            <div class="input-group p-0">
                <span class="money_simbol_input">$</span>
                <input class="form-control-budget text-end" type="number" name="Labor_hourly" step="1" value="${data ? data.cost_by_day : ''}">
            </div>
        </td>
        <td class="p-0"><input class="form-control-budget" type="number" name="Labor_hour" step="0" value="${data ? data.days : ''}"></td>
        <td class="p-0"><input class="form-control-budget" type="text" name="Labor_lead-time" value="${data ? data.lead_time : ''}"></td>
        <td class="p-0">
            <div class="input-group p-0">
                <span class="money_simbol_input">$</span>
                <input class="form-control-budget text-end" type="number" name="Labor_Cost" id="Labor_Cost" step="0.01" value="${data ? data.labor_cost : ''}" readonly disabled>
            </div>
        </td>
        <td class="p-0 text-center" style="width:0px">
            <button type="button" id="remove-labor-btn" class="btn btn-danger border-0 text-center remove_btn p-1" aria-label="Remove labor">
                <i class="bi bi-trash3"></i>
            </button>
        </td>
    `;

    // Insert the new row at the end of tbodyLabor
    tbodyLabor.appendChild(newRowLabor);
    updateSelectOptions();
}
document.getElementById('add-labor-btn').addEventListener('click', function () {
    createLaborRow();
    updateRowNumbers(laborSection)
});

function createMiscRow(data = null) {
    const tbodyMisc = document.getElementById('misc-section');
    const rowCountMisc = tbodyMisc.querySelectorAll('tr').length; // Correct row count

    const newRowMisc = document.createElement('tr');

    // Si hay datos, completar con los valores proporcionados; si no, dejar en blanco
    newRowMisc.innerHTML = `
        <td class="text-center p-0"><strong>${rowCountMisc}</strong></td>
        <td colspan="4" class="p-0">
            <div class="d-flex align-items-center">
                <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                    <option value="${data ? data.item_value : 'GENERAL'}">${data ? data.item_value : 'GENERAL'}</option>
                </select>
                <input class="form-control-budget" type="text" name="misc_desc" value="${data ? data.misc_description : ''}">
            </div>
        </td>            
        <td class="text-center p-0">
            <input class="form-control-budget" type="text" name="misc_lead-time" value="${data ? data.lead_time : ''}">
        </td>
        <td class="p-0">
            <div class="input-group p-0">
                <span class="money_simbol_input">$</span>
                <input class="form-control-budget text-end" type="number" name="misc_UnitCost" id="misc_UnitCost" step="0.01" value="${data ? data.misc_value : ''}">
            </div>
        </td>
        <td class="p-0" style="width:0px">
            <button type="button" id="remove-misc-btn" class="btn btn-danger border-0 text-center remove_btn p-1 remove_item" aria-label="Remove misc">
                <i class="bi bi-trash3"></i>
            </button>
        </td>
    `;

    // Insert the new row at the end of tbodyMisc
    tbodyMisc.appendChild(newRowMisc);

    // Update select options or any other necessary functionality
    updateSelectOptions();
}

// Event listener for adding a new misc row when the button is clicked
document.getElementById('add-misc-btn').addEventListener('click', function () {
    createMiscRow();
    updateRowNumbers(miscSection)
});


function createMaterialRow(data = null) {
    const tbodyMaterial = document.getElementById('materials-section');
    const rowCountMaterial = tbodyMaterial.querySelectorAll('tr').length;
    const newRowMaterial = document.createElement('tr');
    
    // Asigna el id único si se proporciona

    if (data && data.id_generated_by_checklist && data.id_generated_by_checklist != 'null') {
        newRowMaterial.id = data.id_generated_by_checklist
        newRowMaterial.classList.add('AutoCheckList')
    } else if (data && data.id) {
        newRowMaterial.id = data.id;
    }
    if (data && data.isCheckList){
        newRowMaterial.classList.add('AutoCheckList')
    }


    



    newRowMaterial.innerHTML = `
        <td class="text-center p-0"><strong>${rowCountMaterial}</strong></td>
        <td colspan="2" class="p-0">
            <div class="d-flex align-items-center">
                <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                    <option value="${data ? data.item_value : 'GENERAL'}">${data ? data.item_value : 'GENERAL'}</option>
                </select>
                <input class="form-control-budget" type="text" name="materials_desc" value="${data ? data.material_description : ''}">
            </div>
        </td>
        <td class="p-0"  style="max-width:40px;"><input class="form-control-budget" type="number" name="materials_qt" step="0" value="${data ? data.quantity : ''}"></td>
        <td class="p-0" style="max-width:60px;">
            <div class="input-group p-0">
                <span class="money_simbol_input">$</span>
                <input class="form-control-budget text-end" type="number" name="materials_UnitCost" id="materials_UnitCost" step="0.01" value="${data ? data.unit_cost : ''}">
            </div>
        </td>
        <td class="p-0  style="max-width:60px;"><input class="form-control-budget" type="text" name="materials_lead-time" value="${data ? data.lead_time : ''}"></td>
        <td class="p-0"  style="max-width:60px;">
            <div class="input-group p-0">
                <span class="money_simbol_input">$</span>
                <input class="form-control-budget text-end" type="number" name="materials_Cost" id="materials_Cost" step="0.01" value="${data ? data.cost : ''}" readonly disabled>
            </div>
        </td>
        <td class="p-0 text-center" style="width:0px">
                    ${
                        data 
                        ? ''
                        : `<button type="button" id="remove-materials-btn" class="btn btn-danger border-0 text-center remove_btn p-1" aria-label="Remove materials">
                            <i class="bi bi-trash3"></i>
                        </button>`
                    }
        </td>`;
    tbodyMaterial.appendChild(newRowMaterial);
    updateSelectOptions();
    updateRowNumbers(materialsSection)
}

// Event listener for adding a new materials row when the button is clicked
document.getElementById('add-materials-btn').addEventListener('click', function () {
    createMaterialRow();
    updateRowNumbers(materialsSection)
});


// Función para agregar una nueva fila de contratista con datos del diccionario
function createContractorRow(data = null) {
    const tbodyContractor = document.getElementById('contractor-section');
    const rowCountContractor = tbodyContractor.querySelectorAll('tr').length; // Correct row count
    const newRowContractor = document.createElement('tr');
    
    // Si hay datos, completar con los valores proporcionados; si no, dejar en blanco
    newRowContractor.innerHTML = `
        <td class="text-center p-0"><strong>${rowCountContractor + 1}</strong></td>
        <td colspan="4" class="p-0">
            <div class="d-flex align-items-center">
                <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                    <option value="${data ? data.item_value : 'GENERAL'}">${data ? data.item_value : 'GENERAL'}</option>
                </select>
                <input class="form-control-budget" type="text" name="contractor_desc" value="${data ? data.contractor_description : ''}">
            </div>
        </td>
        <td class="text-center p-0">
            <input class="form-control-budget" type="text" name="contractor_lead-time" value="${data ? data.lead_time : ''}">
        </td>
        <td class="p-0">
            <div class="input-group p-0">
                <span class="money_simbol_input">$</span>
                <input class="form-control-budget text-end" type="number" name="contractor_UnitCost" id="contractor_UnitCost" step="0.01" value="${data ? data.contractor_cost : ''}">
            </div>
        </td>   
        <td class="p-0" style="width:0px">
            <button type="button" id="remove-contractor-btn" class="btn btn-danger border-0 text-center remove_btn p-1 remove_item p-1" aria-label="Remove contractor">
                <i class="bi bi-trash3"></i>
            </button>
        </td>
    `;
    
    // Insert the new row at the end of tbodyContractor
    tbodyContractor.appendChild(newRowContractor);

    // Update select options or any other necessary functionality
    updateSelectOptions();
}

// Event listener for adding a new contractor row when the button is clicked
document.getElementById('add-contractor-btn').addEventListener('click', function () {
    createContractorRow();
    updateRowNumbers(contractorSection)
});


// Función para crear una nueva fila de deducción con datos del diccionario
function createDeductsRow(data = null) {
    const tbodyDeducts = document.getElementById('deducts-section');
    const rowCountDeducts = tbodyDeducts.querySelectorAll('tr').length; // Correct row count

    const newRowDeducts = document.createElement('tr');

    // Si hay datos, completar con los valores proporcionados; si no, dejar en blanco
    newRowDeducts.innerHTML = `
        <td class="text-center p-0"><strong>${rowCountDeducts + 1}</strong></td>
        <td colspan="4" class="p-0">
            <div class="d-flex align-items-center">
                <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                    <option value="${data ? data.item_value : 'GENERAL'}">${data ? data.item_value : 'GENERAL'}</option>
                </select>
                <input class="form-control-budget" type="text" name="deducts_desc" value="${data ? data.deduct_description : ''}">
            </div>
        </td>
        <td class="p-0"><input class="form-control-budget" type="text" name="deducts_lead-time" value="${data ? data.lead_time : ''}"></td>
        <td class="p-0">
            <div class="input-group p-0">
                <span class="money_simbol_input">$</span>
                <input class="form-control-budget text-end" type="number" name="deducts_UnitCost" id="deducts_UnitCost" step="0.01" value="${data ? data.deduct_value : ''}">
            </div>
        </td>
        <td class="p-0 text-center" style="width:0px">
            <button type="button" id="remove-deducts-btn" class="btn btn-danger border-0 text-center remove_btn p-1 remove_item" aria-label="Remove deducts">
                <i class="bi bi-trash3"></i>
            </button>
        </td>
    `;

    // Insert the new row at the end of tbodyDeducts
    tbodyDeducts.appendChild(newRowDeducts);

    // Update select options or any other necessary functionality
    updateSelectOptions();
}

// Event listener for adding a new deducts row when the button is clicked
document.getElementById('add-deducts-btn').addEventListener('click', function () {
    createDeductsRow();
    updateRowNumbers(deductsSection)
});

function createProfitRow(data = null) {
    const tbodyProfits = document.getElementById('profit-section');
    const rowCountProfits = tbodyProfits.querySelectorAll('tr').length; // Correct row count

    const newRowProfits = document.createElement('tr');

    // Si hay datos, completar con los valores proporcionados; si no, dejar en blanco
    newRowProfits.innerHTML = `
        <td class="text-center p-0"><strong>${rowCountProfits + 1}</strong></td>
        <td colspan="4" class="p-0">
            <div class="d-flex align-items-center">
                <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                    <option value="${data ? data.item_value : 'GENERAL'}">${data ? data.item_value : 'GENERAL'}</option>
                </select>
                <input class="form-control-budget" type="text" name="profit_desc" value="${data ? data.profit_description : ''}">
            </div>
        </td>
        <td class="p-0" style="width:200px"> 
            <input class="form-control-budget" type="text" name="profit_lead-time" value="${data ? data.lead_time : ''}">
        </td>  
        <td class="p-0">
            <input class="form-control-budget profit_item'" type="number" name="Profit_UnitCost" step="1"   id="profit_item" value="${data ? data.profit_value : ''}">
        </td>
        <td class="p-0 text-center" style="width:0px">
            <button type="button" id="remove-profit-btn" class="btn btn-danger border-0 text-center remove_btn p-1" aria-label="Remove profit">
                <i class="bi bi-trash3"></i>
            </button>
        </td>
    `;

    

    // Insert the new row at the end of tbodyProfits
    tbodyProfits.appendChild(newRowProfits);

    // Update select options or any other necessary functionality
    updateSelectOptions();
}
const profitSection = $$$("profit-section");
// Event listener for adding a new profit row when the button is clicked
document.getElementById('add-profit-btn').addEventListener('click', function () {
    createProfitRow();
    updateRowNumbers(profitSection)
});



// Labor section
const laborSection = $$$("labor-section");
const totalCostInput = document.querySelector('input[name="total_Cost"]');

// Update labor cost dynamically when the hourly rate or hours worked change
laborSection.addEventListener("input", function (event) {
    if (event.target.name === "Labor_hour" || event.target.name === "Labor_hourly") {
        const row = event.target.closest("tr");
        const hourlyRate = parseFloat(row.querySelector('input[name="Labor_hourly"]').value) || 0;
        const hours = parseFloat(row.querySelector('input[name="Labor_hour"]').value) || 0;
        const laborCostInput = row.querySelector('input[name="Labor_Cost"]');
        const laborCost = hourlyRate * hours;

        // Update the Labor Cost field in the row
        laborCostInput.value = laborCost.toFixed(2);
        updateTotalCost(); // Update the total cost
        calculateTotalByItem()
    }
    calculateTotalByItem()
});

    // Materials section
const materialsSection = $$$("materials-section");

materialsSection.addEventListener("input", function (event) {
    if (event.target.name === "materials_qt" || event.target.name === "materials_UnitCost") {
        const row = event.target.closest("tr");
        const quantity = parseFloat(row.querySelector('input[name="materials_qt"]').value) || 0;
        const unitCost = parseFloat(row.querySelector('input[name="materials_UnitCost"]').value) || 0;
        const materialCostInput = row.querySelector('input[name="materials_Cost"]');
            const materialCost = quantity * unitCost;
            // Update the materials Cost field in the row
        materialCostInput.value = materialCost.toFixed(2);
            updateTotalCost();
            updateRowNumbers(materialsSection)
    }
    calculateTotalByItem()
});


// contractor section
const contractorSection = $$$("contractor-section");
contractorSection.addEventListener("input", function (event) {
    if (event.target.name === "contractor_UnitCost") {
        updateTotalCost(); // Update the total cost
        updateRowNumbers(contractorSection)
    }
    calculateTotalByItem()
});

// misc section
const miscSection = $$$("misc-section");
miscSection.addEventListener("input", function (event) {
    if (event.target.name === "misc_UnitCost") {
        updateTotalCost(); // Update the total cost
        updateRowNumbers(miscSection)
    }
    calculateTotalByItem()
});

// deducts section
const deductsSection = $$$("deducts-section");

deductsSection.addEventListener("input", function (event) {
    if (event.target.name === "deducts_UnitCost") {
        updateTotalCost();
        updateRowNumbers(deductsSection)
    }
    calculateTotalByItem()
});

profitSection.addEventListener("input", function (event) {
    if (event.target.name === "Profit_UnitCost") {
        updateTotalCost();
        updateRowNumbers(profitSection)
    }
    calculateTotalByItem()
});

// Remove a labor row when the trash button is clicked
laborSection.addEventListener('click', function(event) {
    if (event.target.closest('#remove-labor-btn')) {
        const row = event.target.closest('tr');
        if (row) {
            row.remove();
            updateTotalCost(); // Update total after removal
            updateRowNumbers(laborSection)
        }
    }
    calculateTotalByItem()
});

// Remove a materials row when the trash button is clicked
materialsSection.addEventListener('click', function(event) {
    if (event.target.closest('#remove-materials-btn')) {
        const row = event.target.closest('tr');
        if (row) {
            row.remove();
            updateTotalCost(); // Update total after removal
            updateRowNumbers(materialsSection)
        }
    }
    calculateTotalByItem()
});

    // Remove a contractors row when the trash button is clicked
contractorSection.addEventListener('click', function(event) {
    if (event.target.closest('#remove-contractor-btn')) {
        const row = event.target.closest('tr');
        if (row) {
            row.remove();
            updateTotalCost(); // Update total after removal
            updateRowNumbers(contractorSection)
        }
    }
    calculateTotalByItem()
});

// Remove a misc row when the trash button is clicked
miscSection.addEventListener('click', function(event) {
if (event.target.closest('#remove-misc-btn')) {
    const row = event.target.closest('tr');
    if (row) {
        row.remove();
        updateTotalCost(); // Update total after removal
        updateRowNumbers(miscSection)
    }
}
calculateTotalByItem()
});

// Remove a deducts row when the trash button is clicked
deductsSection.addEventListener('click', function(event) {
    if (event.target.closest('#remove-deducts-btn')) {
        const row = event.target.closest('tr');
        if (row) {
            row.remove();
            updateTotalCost(); // Update total after removal
            updateRowNumbers(deductsSection)
        }
    }
    calculateTotalByItem()
    });

profitSection.addEventListener('click', function(event) {
    if (event.target.closest('#remove-profit-btn')) {
        const row = event.target.closest('tr');
        if (row) {
            row.remove();
            updateTotalCost(); // Update total after removal
            updateRowNumbers(profitSection)
        }
    }
    calculateTotalByItem()
    });

function updateRowNumbers(tableSection) {
    // Seleccionamos todas las filas <tr> en la tabla (excluyendo los encabezados si existen)
    const rows = tableSection.querySelectorAll('tr');
    rows.forEach((row, index) => {
        const numberCell = row.querySelector('td strong'); // Asumiendo que el número está dentro de <strong>
        if (numberCell) {
            numberCell.textContent = index + 1; // Actualiza el número basado en el índice (empezando en 1)
        }
    });
}

let total = 0
    
const profitPercentLabel = document.querySelector('input[name="profit_percent"]');
function updateProfit() {
    const TotalCostInput = document.querySelector('input[name="total_CostWithProfit"]');
    const profitPercentInput = profitPercentLabel.value;
    const profitInput = document.querySelector('input[name="profit_value"]');
    
    const profitPercent = Number(profitPercentInput); // Convertir el valor del input a número
    const profitTotal = total * (profitPercent / 100); // Calcular la ganancia total
    profitInput.value = profitTotal.toFixed(2); // Actualizar el input con el profit formateado a 2 decimales
    const granTotal = total + profitTotal
    TotalCostInput.value = granTotal.toFixed(2)
    formatTotalCost(profitInput);
}

  
function updateTotalCost() {
    validateInputs()
    let laborTotal = 0;
    let materialsTotal = 0;
    let contractorTotal = 0;
    let miscTotal = 0;
    let deductsTotal = 0;
    let profitTotal = 0;

    // Calculate labor subtotal
    const laborCostInputs = laborSection.querySelectorAll('input[name="Labor_Cost"]');
    const subtotalLaborCost = $$$('total_labor_cost');
    laborCostInputs.forEach(input => {
        laborTotal += parseFloat(input.value) || 0;
    });
    subtotalLaborCost.value = laborTotal
    formatTotalCost(subtotalLaborCost)

    // Calculate materials subtotal
    const materialCostInputs = materialsSection.querySelectorAll('input[name="materials_Cost"]');
    const subtotalMaterialsCost =  $$$('total_materials_cost');
    materialCostInputs.forEach(input => {
        materialsTotal += parseFloat(input.value) || 0;
    });
    subtotalMaterialsCost.value = materialsTotal.toFixed(2); 
    formatTotalCost(subtotalMaterialsCost)


    // Calculate contractor subtotal
    const contractorCostInputs = contractorSection.querySelectorAll('input[name="contractor_UnitCost"]');
    const subtotalContractorCost =  $$$('total_contractor_cost');
    contractorCostInputs.forEach(input => {
        contractorTotal += parseFloat(input.value) || 0;
    });
    subtotalContractorCost.value = contractorTotal.toFixed(2); 
    formatTotalCost(subtotalContractorCost)

    // Calculate misc subtotal
    const miscCostInputs = miscSection.querySelectorAll('input[name="misc_UnitCost"]');
    const subtotalMiscCost =  $$$('total_misc_cost');
    miscCostInputs.forEach(input => {
        miscTotal += parseFloat(input.value) || 0;
    });
    subtotalMiscCost.value = miscTotal.toFixed(2); 
    formatTotalCost(subtotalMiscCost)


    // Calculate deducts subtotal
    const deductsCostInputs = deductsSection.querySelectorAll('input[name="deducts_UnitCost"]');
    const subtotalDeductsCost =  $$$('total_deducts_cost');
    deductsCostInputs.forEach(input => {
        deductsTotal += parseFloat(input.value) || 0;
    });
    subtotalDeductsCost.value = deductsTotal.toFixed(2); 
    formatTotalCost(subtotalDeductsCost)

    // Calculate deducts profit 
    const profitInputs = $$('#profit_item');
    const subtotalprofit =  $$$('total_profit');
    const totalprofit =  $$$('total_profit_cost');
    if (profitInputs){
        profitInputs.forEach(input => {
            profitTotal += parseFloat(input.value) || 0;
        });
        subtotalprofit.value = profitTotal.toFixed(2); 
        totalprofit.value = profitTotal.toFixed(2); 
        formatTotalCost(subtotalprofit)
    }
   

    // Update the total cost by summing the subtotals
    total = laborTotal + materialsTotal + contractorTotal + miscTotal;
    totalCostInput.value = total.toFixed(2); 

    granTotalInput = $$$('grand_Cost');
    granTotalCosto =   total +  deductsTotal
    granTotalInput.value = granTotalCosto.toFixed(2);         
    formatTotalCost(granTotalCosto)

        // Actualizar el total de costos
    let labelTotalCostInput = $('#totalCostByItems');  // Elemento para el total de costos
    labelTotalCostInput.innerHTML = granTotalCosto.toLocaleString('en-US', { style: 'currency', currency: 'USD' });


    // Actualizar el total de ganancias
    let labelTotalProfitInput = $('#totalProfitByItems');  // Elemento para el total de ganancias
    labelTotalProfitInput.innerHTML = profitTotal.toLocaleString('en-US', { style: 'currency', currency: 'USD' });


    // Actualizar el total de costos y ganancias combinados
    let labelTotalCostProfitInput = $('#totalCostProfitByItems');  // Elemento para el total combinado
    let totalProfit = profitTotal + granTotalCosto;
    labelTotalCostProfitInput.innerHTML = totalProfit.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
    let Value_Project = $('#Value_Project'); 
    Value_Project.value = totalProfit;
    formatTotalCost(Value_Project)

    return total
}


// Format any input value passed to it
function formatTotalCost(inputElement) {
    const number = parseFloat(inputElement.value);
    inputElement.value = number ? number.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '';
}

function toggleAddHole() {
    // Retrieve the checkbox, table, and input values
    var checkbox = $$$("Add-hole-check"); // Checkbox for activating/deactivating loans
    var table = $$$("add-hole-to-item"); // The loans table element
    var totalQTElement = parseFloat($$$("QT").value) || 0; // Total cost of the project
    var percentCost = parseFloat($$$("cost-???").value) || 0; // Percentage of loans
    var costPorHole = parseFloat($$$("cost-per-hole").value) || 0;
    var totalPost = parseFloat($$$("total-posts").value) || 0; // Percentage of loans
    var tbodymaterial= $$$('materials-section'); // Deductions section (table body)
    const rowCountmaterial = tbodymaterial.querySelectorAll('tr').length; // Count of existing rows in the deductions section
    

    // If the checkbox is checked, display the loans table and calculate the deductions
    if (checkbox.checked) {
        table.style.display = "table"; // Show the loans table
        
        // Calculate the deduction amount based on the total cost and the loan percentage
        var holeAmount = (totalQTElement * percentCost + totalPost*costPorHole).toFixed(2);
        // Create a new row in the deductions section with the loan deduction details
        var newRow = document.createElement("tr");
        newRow.id = `holeItem`; // ID único para cada fila
        newRow.className = "align-middle generated-by-utils";
        newRow.innerHTML = `
            <td class="text-center p-0"><strong>${rowCountmaterial}</strong></td>
            <td class="p-0" colspan="2"> 
                <div class="d-flex align-items-center">
                    <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                        <option value="GENERAL">GENERAL</option> 
                    </select>
                    <input class="form-control-budget" type="text" id="materials_desc" name="materials_desc" value="Cost by hole">
                </div>
            </td>
            <td class="p-0">
                <input class="form-control-budget" type="number" name="materials_qt" step="0" value="${totalPost.toFixed(2)}">
            </td>
            <td class="p-0">
                <div class="input-group p-0">
                    <span class="money_simbol_input">$</span>
                    <input class="form-control-budget text-end" type="text" name="materials_UnitCost" step="0.01" value="Null">
                </div>
            </td>
            <td class="p-0"><input class="form-control-budget" type="text" name="materials_lead-time" value='8 days'></td>                             
            <td class="p-0">
            <div class="input-group p-0">
                <span class="money_simbol_input">$</span>
                <input class="form-control-budget text-end" type="number" name="materials_Cost" id="materials_Cost" step="0.01" value='${holeAmount}' readonly disabled>
            </div>
            </td>                            
        `;
        tbodymaterial.appendChild(newRow);
    } else {
        table.style.display = "none";  
        $$$("holeItem")?.remove();
    }
    updateTotalCost()
    calculateTotalByItem()
    updateSelectOptions()
    updateRowNumbers(materialsSection)
   
}

const element = $$$("Add-hole-check");
element.onclick = toggleAddHole;

const totalQTElement = $$$("QT")
const percentCost = $$$("cost-???")
const costPorHole = $$$("cost-per-hole")
const totalPost = $$$("total-posts") 

const table = $$$("add-hole-to-item");


totalQTElement?.addEventListener("input", updateHoleCost);
percentCost?.addEventListener("input", updateHoleCost);
costPorHole?.addEventListener("input", updateHoleCost);
totalPost?.addEventListener("input", updateHoleCost);

function updateHoleCost(){
    var totalQTElement = $$$("QT");
    var percentCost = $$$("cost-???");
    var costPorHole = $$$("cost-per-hole");
    var table = $$$("add-hole-to-item");
    var totalPost = $$$("total-posts") 
    // Verifica si alguno de los elementos es null o no existe
    if (totalQTElement || percentCost || costPorHole || totalPost) {
        if (table) { // Solo manipula table si existe
            table.style.display = "none";  
        }
        
        var postCount = parseInt(totalPost.value) || 0;
        var additionalMultiplier = Math.floor(postCount/ 50.01); // Calcula cuántos incrementos de 50 huecos han pasado desde los 45 iniciales
        if (additionalMultiplier > 0) {
            totalQTElement.value = additionalMultiplier + 1;  // Actualiza el costo
        } else {
            totalQTElement.value = 1;  // Si no se han superado los 45, el multiplicador es 0
        }
        $$$("holeItem")?.remove(); // Remueve solo si existe
        toggleAddHole(); // Asegúrate de que esta función esté definida
    }

    // Aquí puedes añadir la lógica para actualizar el costo del agujero
    
}

function toggleUtilitiesPerFT(){
    var checkbox = $$$("add-utilities-per-FT"); 
    var table = $$$("add-utilities-cost"); 
    var utilitiesCost = parseFloat($$$("utilities-cost").value) || 0;
    var totalFT = parseFloat($$$("total-ft").value) || 0; 
    var tbodymaterial= $$$('materials-section'); 
    const rowCountmaterial = tbodymaterial.querySelectorAll('tr').length;
    if (checkbox.checked) {
        table.style.display = "table"; // Show the loans table
        
        // Calculate the deduction amount based on the total cost and the loan percentage
        var utilitiesAmount = (totalFT * utilitiesCost).toFixed(2);
        // Create a new row in the deductions section with the loan deduction details
        var newRow = document.createElement("tr");
        newRow.id = `utilitiesItem`; // ID único para cada fila
        newRow.className = "align-middle generated-by-utils";
        newRow.innerHTML = `
            <td class="text-center p-0"><strong>${rowCountmaterial}</strong></td>
            <td class="p-0" colspan="2"> 
                <div class="d-flex align-items-center ">
                    <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                        <option value="GENERAL">GENERAL</option> 
                    </select>
                    <input class="form-control-budget" type="text" id="materials_desc" name="materials_desc" value="Utility cost per square foot">
                </div>
            </td>
            <td class="p-0">
                <input class="form-control-budget" type="number" name="materials_qt" step="0" value="${totalFT.toFixed(2)}" readonly>
            </td>
            <td class="p-0">
                <div class="input-group p-0">
                    <span class="money_simbol_input">$</span>
                    <input class="form-control-budget text-end" type="text" name="materials_UnitCost" step="0.01" value="${utilitiesCost.toFixed(2)}" readonly>
                </div>
            </td>
            <td class="p-0"><input class="form-control-budget" type="text" name="materials_lead-time" value='8 days'></td>                             
            <td class="p-0">
            <div class="input-group p-0">
                <span class="money_simbol_input">$</span>
                <input class="form-control-budget text-end" type="number" name="materials_Cost" id="materials_Cost" step="0.01" value='${utilitiesAmount}' readonly disabled>
            </div>
            </td>                            
            <td class="p-0 text-center" style="width:0px">
        </tr>        `;
        tbodymaterial.appendChild(newRow); // Append the new row to the deductions section
    } else {
        // If the checkbox is unchecked, hide the loans table and remove the deduction row
        table.style.display = "none";  
        $$$("utilitiesItem")?.remove(); // Remove the row for loan deductions
    }
    updateTotalCost()
    calculateTotalByItem()
    updateSelectOptions()
    updateRowNumbers(materialsSection)
}

const elementUtilities = $$$("add-utilities-per-FT");
elementUtilities.onclick = toggleUtilitiesPerFT;

var utilitiesCost = $$$("utilities-cost")
var totalFT = $$$("total-ft")

utilitiesCost?.addEventListener("input", updateUtilitiesPerFT);
totalFT?.addEventListener("input", updateUtilitiesPerFT);


function updateUtilitiesPerFT(){
    var utilitiesCost = parseFloat($$$("utilities-cost").value) || 0;
    var totalFT = parseFloat($$$("total-ft").value) || 0; 
    var table = $$$("add-utilities-cost"); 
    // Verifica si alguno de los elementos es null o no existe
    if (utilitiesCost || totalFT) {
        if (table) { // Solo manipula table si existe
            table.style.display = "none";  
        }
        $$$("utilitiesItem")?.remove(); // Remueve solo si existe
        toggleUtilitiesPerFT(); // Asegúrate de que esta función esté definida
    }

    // Aquí puedes añadir la lógica para actualizar el costo del agujero
    
}


function toggleRemmovalPerFT(){
    var checkbox = $$$("add-removal-per-FT"); 
    var table = $$$("add-removal-cost"); 
    var removalCost = parseFloat($$$("removal-cost").value) || 0;
    var totalFT = parseFloat($$$("total-ft").value) || 0; 
    var tbodymaterial= $$$('materials-section'); 
    const rowCountmaterial = tbodymaterial.querySelectorAll('tr').length;

    if (checkbox.checked) {
        table.style.display = "table"; // Show the loans table
        // Calculate the deduction amount based on the total cost and the loan percentage
        var removalAmount = (totalFT * removalCost).toFixed(2);
        // Create a new row in the deductions section with the loan deduction details
        var newRow = document.createElement("tr");
        newRow.id = `removalItem`; // ID único para cada fila
        newRow.className = "align-middle generated-by-utils";
        newRow.innerHTML = `
            <td class="text-center p-0"><strong>${rowCountmaterial}</strong></td>
            <td class="p-0" colspan="2"> 
                <div class="d-flex align-items-center ">
                    <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                        <option value="GENERAL">GENERAL</option> 
                    </select>
                    <input class="form-control-budget" type="text" id="materials_desc" name="materials_desc" value="Cost to remove objects">
                </div>
            </td>
            <td class="p-0">
                <input class="form-control-budget" type="number" name="materials_qt" step="0" value="${totalFT.toFixed(2)}" readonly>
            </td>
            <td class="p-0">
                <div class="input-group p-0">
                    <span class="money_simbol_input">$</span>
                    <input class="form-control-budget text-end" type="text" name="materials_UnitCost" step="0.01" value="${removalCost.toFixed(2)}" readonly>
                </div>
            </td>
            <td class="p-0"><input class="form-control-budget" type="text" name="materials_lead-time" value='8 days'></td>                             
            <td class="p-0">
            <div class="input-group p-0">
                <span class="money_simbol_input">$</span>
                <input class="form-control-budget text-end" type="number" name="materials_Cost" id="materials_Cost" step="0.01" value='${removalAmount}' readonly disabled>
            </div>
            </td>                            
        `;
        tbodymaterial.appendChild(newRow);// Append the new row to the deductions section
    } else {
        // If the checkbox is unchecked, hide the loans table and remove the deduction row
        table.style.display = "none";  
        $$$("removalItem")?.remove();
    }
    updateTotalCost()
    calculateTotalByItem()
    updateSelectOptions()
    updateRowNumbers(materialsSection)
}

const elementRemoval = $$$("add-removal-per-FT");
elementRemoval.onclick = toggleRemmovalPerFT;

var removalCost = $$$("removal-cost")
var totalFT = $$$("total-ft")

removalCost?.addEventListener("input", updateRemovalPerFT);
totalFT?.addEventListener("input", updateRemovalPerFT);


function updateRemovalPerFT(){
    var removalCost = parseFloat($$$("removal-cost").value) || 0;
    var totalFT = parseFloat($$$("total-ft").value) || 0; 
    var table = $$$("add-removal-cost"); 
    // Verifica si alguno de los elementos es null o no existe
    if (removalCost || totalFT) {
        if (table) { // Solo manipula table si existe
            table.style.display = "none";  
        }
        $$$("removalItem")?.remove(); // Remueve solo si existe
        toggleRemmovalPerFT(); // Asegúrate de que esta función esté definida
    }

    // Aquí puedes añadir la lógica para actualizar el costo del agujero
    
}



function toggleTable() {
    var checkbox = $$$("cbox1");
    var table = $$$("table_ftandPost");

    if (checkbox.checked) {
    table.style.display = "table";
    } else {
        table.style.display = "none";
        const addHoleCheckbox = document.getElementById("Add-hole-check");
        const addUtilitiesCheckbox = document.getElementById("add-utilities-per-FT");
        const addRemovalCheckbox = document.getElementById("add-removal-per-FT");

        if (addHoleCheckbox.checked) {
            addHoleCheckbox.checked = false
            toggleAddHole()
        }
        if (addUtilitiesCheckbox.checked) {
            addUtilitiesCheckbox.checked = false
            toggleUtilitiesPerFT()
        }
        if (addRemovalCheckbox.checked) {
            addRemovalCheckbox.checked = false
            toggleRemmovalPerFT()
        }
        
    }
}

function toggleUnitCostCLF() {
    var checkbox = $$$("cbox2");
    var table = $$$("table_UnitCostCLF");

    if (checkbox.checked) {
    table.style.display = "table"; // Muestra la tabla cuando el checkbox está activado
    } else {
    table.style.display = "none";  // Oculta la tabla cuando el checkbox está desactivado
    const tbody = document.getElementById('cost_per_manufacturing');
    const checkboxes = tbody.querySelectorAll('input[type="checkbox"]');

    checkboxes.forEach(checkbox => {
        checkbox.checked = false; // Desactivar el checkbox
        checkManufacturingCosts(checkbox)
        
    });

    }
}

function toggleProfitByDay() {
    var checkbox = $$$("cbox3");
    var table = $$$("table_ProfitByDay");


    if (checkbox.checked) {
        table.style.display = "table";
        var days = table.querySelector('#days-per-profit')
        var profitPerDay = table.querySelector('#profit-value')
        var totalProfit = days.value + profitPerDay.value
        const tbodyProfit = $$$('profit-section');
        const rowCountProfit = tbodyProfit.querySelectorAll('tr').length; // Correct row count

        var newRow = document.createElement("tr");
        newRow.id = `automaticProfitperDay`; // ID único para cada fila
        newRow.className = "align-middle generated-by-utils automaticProfit"
        newRow.innerHTML = `
        <tr id="automaticProfitperDay" class="generated-by-utils">
            <td class="text-center p-0"><strong>${rowCountProfit}</strong></td>
            <td colspan="4"  class="p-0">
                <div class="d-flex align-items-center ">
                    <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                        <option value="GENERAL">GENERAL</option> 
                    </select>
                    <input class="form-control-budget" type="text" name="profit_desc" value="Earnings calculated per day of work (${days.value} days)"  readonly disabled>
                </div>
            </td>
            </td>
            <td class="p-0">
                <input class="form-control-budget" type="text" name="profit_lead-time" value="Inmediate"  step="0.01" readonly disabled>
                
            </td>
            <td class="p-0"  style="width:200px"> 
                <input class="form-control-budget profit_item'" type="number" name="Profit_UnitCost" step="1"   id="profit_item" value="${totalProfit}" readonly disabled>
            </td>                                                                  
        </tr>
    `
    tbodyProfit.appendChild(newRow); 
    updateTotalCost()
    }else {
        var checkbox = $$$('use-day-in-itemsManufacturing');
        if (checkbox.checked){
            checkbox.checked = !checkbox.checked;
            useDaysInMF()
        }
        const fila = document.getElementById("automaticProfitperDay");
        if (fila) {
            fila.remove();
        } else {
            console.log("No se encontró el elemento con ID 'automaticProfitperDay'.");
        }
        table.style.display = "none";  // Oculta la tabla cuando el checkbox está desactivado
        updateTotalCost()
    }
}



// Function to toggle the visibility of the loans section
function toggleAddLoans() {
    // Retrieve the checkbox, table, and input values
    var checkbox = $$$("cbox4"); // Checkbox for activating/deactivating loans
    var table = $$$("loans-to-the-project"); // The loans table element
    var totalCostElement = updateTotalCost() // Total cost of the project
    var percentLabelLoans = parseFloat($$$("percentage-loans").value) || 0; // Percentage of loans
    var deductsSection = $$$("deducts-section"); // The section where deductions are displayed
    const tbodydeducts = $$$('deducts-section'); // Deductions section (table body)
    const rowCountdeducts = tbodydeducts.querySelectorAll('tr').length; // Count of existing rows in the deductions section

    // If the checkbox is checked, display the loans table and calculate the deductions
    if (checkbox.checked) {
        table.style.display = "table"; // Show the loans table
        
        // Calculate the deduction amount based on the total cost and the loan percentage
        var deductAmount = (totalCostElement * percentLabelLoans).toFixed(2);


        // Create a new row in the deductions section with the loan deduction details

        var newRow = document.createElement("tr");
            newRow.id = `deducts10`; // ID único para cada fila
            newRow.className = "align-middle generated-by-utils"
            newRow.innerHTML = `
                <td class="text-center p-0"><strong>${rowCountdeducts}</strong></td>
                <td colspan="4" class="p-0 text-wrap">
                    <div class="d-flex align-items-center text-wrap">
                        <select id="itemsSelect" class="innerSelect me-2" style="width: auto;"><option value="GENERAL">GENERAL</option><option value="af">af</option><option value="clf">clf</option></select>
                        <textarea class="form-control-budget text-start" name="deducts_desc" rows="2" readonly>Value for concepts of loans, interest and variable costs related to the financial management of the project (${percentLabelLoans * 100}%) readonly disabled.
                        </textarea>
                        <input class="form-control-budget d-none" type="text" name="deducts_desc" value="Value for concepts of loans, interest and variable costs related to the financial management of the project. (${percentLabelLoans * 100}%)">
                    </div>                     
                </td>
                <td class="p-0"><input class="form-control-budget" type="text" name="deducts_lead-time" value="Immediate" ></td>                           
                <td class="p-0">
                    <div class="input-group p-0">
                        <span class="money_simbol_input">$</span>
                        <input class="form-control-budget text-end" type="number" name="deducts_UnitCost" id="deducts_UnitCost" value="${deductAmount}" step="0.01" readonly disabled>
                    </div>
                </td>                         
        `;
        deductsSection.appendChild(newRow);// Append the new row to the deductions section

    } else {
        // If the checkbox is unchecked, hide the loans table and remove the deduction row
        table.style.display = "none";  
        $$$("deducts10")?.remove(); // Remove the row for loan deductions
    }
    calculateTotalByItem()
    calculateProfitAndCostByItem()
    updateTotalCost()
    updateRowNumbers(deductsSection)
}



function reoloadLoans() {
    var checkbox = $$$("cbox4"); 
    checkbox.checked = false
    toggleAddLoans()
    checkbox.checked = true
    toggleAddLoans()
}

//to change

//to change percentLabelLoan update the deductAmount
$$$("percentage-loans").addEventListener('input', function() {
    reoloadLoans();
});

function toggleUnitCostMW() {
    // Retrieve the checkbox, table, and input values
    var checkbox = $$$("cboxMW"); // Checkbox for activating/deactivating loans
    var table = $$$("table_UnitCostMW"); // The loans table element

    if (checkbox.checked) {
        table.style.display = "table"; // Show the loans table    
    } else {
        table.style.display = "none";  
        const tbody = document.getElementById('cost_per_manufacturingMW');
        const checkboxes = tbody.querySelectorAll('input[type="checkbox"]');
        const checkboxAddDaily = $$$('cboxMWadd');
        checkboxAddDaily.checked = false;
        activeRowProfitManufacturingMW(checkboxAddDaily)
    
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            checkManufacturingCostsMW(checkbox)
    })}
    calculateTotalByItem()
    calculateProfitAndCostByItem()
    
}



const items = ['GENERAL'];

function addItem(input=null) {
    let inputValue;
    if (input) {
        inputValue = input.trim().toUpperCase();
    } else {
        inputValue = $$$("itemInput").value.trim().toUpperCase();
    }
    const ItemsManufacturing = $$$("cost_per_manufacturing")
    const ItemsManufacturingMW = $$$("cost_per_manufacturingMW")

    if (inputValue === "") {
        alert("Please enter a valid item.");
        return;
    }

    if (/\d/.test(inputValue)) {
        alert("The item must not contain numbers.");
        return;
    }
    
    const itemsContainer = document.getElementById("items_container");

    const existingItems = Array.from(itemsContainer.querySelectorAll("input[name='items[]']"))
        .map(input => input.value.toLowerCase());

    if (existingItems.includes(inputValue.toLowerCase())) {
        alert("El ítem ya existe.");
        return;
    }

    // Agregar el nuevo item al array
    items.push(inputValue.trim().replace(/\s+/g, '-'));
    var idInput = inputValue.trim().replace(/\s+/g, '-')
    const projectsCountSpan = document.getElementById('projects-count');
    projectsCountSpan.textContent = items.length - 1;

    // Crear un nuevo span
    const newSpan = document.createElement("span");
    newSpan.className = "items_tag d-inline-flex align-items-center bg-light border rounded px-2 py-1";

    newSpan.innerHTML = `
        ${inputValue}
        <i class="bi bi-x-square-fill ms-2 text-danger" role="button" onclick="removeItem(this, '${idInput}')"></i>
        <input type="hidden" name="items[]" value="${inputValue}">
    `;
    
    newRowIMF = `
        <tr id="manufacturing-${idInput}">
            <td class="p-0 border text-center px-2 checkManufacturingCost">
                <input class="text-end align-middle pr-2" type="checkbox" name="check-manufacturing-${idInput}" id="check-manufacturing-${idInput}" onclick="checkManufacturingCosts(this)"> ${inputValue}
            </td>                      
            <td class="p-0 border text-center">
                <input class="form-control-budget text-end days-manufacturing" type="number" name="days-manufacturing-${idInput}" value="0" id="days-manufacturing-${idInput}" step="0.5" style="width:80px">
            </td>                          
        </tr>
    `

    newRowMW = `
        <tr id="manufacturingMW-${idInput}">
            <td class="p-0 border text-center checkManufacturingCostMW">
                <input class="text-end align-middle pr-2" type="checkbox" name="check-manufacturingMW-${idInput}" id="check-manufacturingMW-${idInput}" onclick="checkManufacturingCostsMW(this)"> ${inputValue}
            </td>     
            <td class="p-0 border text-center">
                <input class="form-control-budget text-end qtyWLD-manufacturingMW w-10" type="number" name="qtyWLD-manufacturingMW-${idInput}" value="0" id="qtyWLD-manufacturingMW-${idInput}" oninput="reloadDataManufacturingMW(this)" step="1" style="width:30px">
            </td>
            <td class="p-0 border text-center">
                <input class="form-control-budget text-end qtyASST-manufacturingMW w-10" type="number" name="qtyASST-manufacturingMW-${idInput}" value="0" id="qtyASST-manufacturingMW-${idInput}" oninput="reloadDataManufacturingMW(this)"step="1" style="width:30px">
            </td>                            
            <td class="p-0 border text-center">
                <input class="form-control-budget text-end days-manufacturingMW" type="number" name="days-manufacturingMW-${idInput}" value="0" id="days-manufacturingMW-${idInput}" oninput="reloadDataManufacturingMW(this); reloadRowProfitManufacturingMW()" step="1" style="width:80px">
            </td>                          
        </tr>
    `
    ItemsManufacturing.insertAdjacentHTML('beforeend', newRowIMF);
    ItemsManufacturingMW.insertAdjacentHTML('beforeend', newRowMW);
    // Agregar el nuevo span al contenedor
    const container = $$$("items_container");
    container.appendChild(newSpan);

    // Limpiar el input después de agregar el item
    $$$("itemInput").value = "";

    // Actualizar las opciones en todos los selects
    updateSelectOptions();    
}

function checkManufacturingCostsMW(checkbox) {
    const isChecked = checkbox.checked;
    const valueItem = checkbox.parentElement.textContent
    if (isChecked) {
        addRowCostManufacturingMW(valueItem);
        updateRowNumbers(profitSection)
    } else {
        removeRowCostManufacturingMW(valueItem);
    }
    updateRowNumbers(laborSection)
};

function addRowCostManufacturingMW(valueItem){
    console.log(valueItem)
    const tbodyLabor = $$$('labor-section');
    const rowCountLabor = tbodyLabor.querySelectorAll('tr').length; 
    const days = $$$('days-manufacturingMW-'+valueItem.trim().replace(/\s+/g, '-')).value
    const qtyWLD = $$$('qtyWLD-manufacturingMW-'+valueItem.trim().replace(/\s+/g, '-')).value
    const qtyASST = $$$('qtyASST-manufacturingMW-'+valueItem.trim().replace(/\s+/g, '-')).value
    const costWLD = $$$('welderCostByDay').value
    const costASST = $$$('assistantCostByDay').value
    // Create a new table row for labor input
    const newRowLabor = document.createElement('tr');
    newRowLabor.id = `${valueItem.trim().replace(/\s+/g, '-')}MW`
    newRowLabor.classList.add('generated-by-utils');
    
    newRowLabor.innerHTML = `
            <td class="text-center p-0"><strong>${rowCountLabor}</strong></td>
            <td colspan="2"  class="p-0 ">
                <div class="d-flex align-items-center ">
                    <select id="itemsSelect" class="innerSelect me-2" style="width: auto;" readonly disabled>
                        <option value="${valueItem.trim().replace(/\s+/g, '-')}">${valueItem.trim().replace(/\s+/g, '-')}</option>
                    </select>
                    <input class="form-control-budget" type="text" id="laborDescInput" name="Labor_desc" value="workshop manufacturing cost (Welder:${qtyWLD}, Asst:${qtyWLD})">
                </div>
            </td>
            <td class="p-0">
                <div class="input-group p-0">
                    <span class="money_simbol_input">$</span>
                    <input class="form-control-budget text-end" type="number" name="Labor_hourly" step="1" value="${qtyWLD*costWLD+qtyASST*costASST}" readonly disabled>
                </div>
            </td>
            <td class="p-0"><input class="form-control-budget" type="number" name="Labor_hour" step="0" value="${days}" readonly disabled></td>
            <td class="p-0"><input class="form-control-budget" type="text" name="Labor_lead-time" value="${days} days" readonly disabled></td>                           
            <td class="p-0"> 
                <div class="input-group p-0">
                    <span class="money_simbol_input">$</span>
                    <input class="form-control-budget text-end" type="number" name="Labor_Cost" id="Labor_Cost" step="0.01" value="${(qtyWLD*costWLD+qtyASST*costASST)*days}" readonly disabled>
                </div>
            </td>
            <td class="p-0 text-center" style="width:0px">
            </td>
    `;
    
    tbodyLabor.appendChild(newRowLabor);
    updateSelectOptions()
    updateTotalCost()
    
    }

function activeRowProfitManufacturingMW(checkboxAdd){
    const rows = document.querySelectorAll("#cost_per_manufacturingMW tr");
    if (!checkboxAdd.checked) { 
        removeRowProfitManufacturingMW();
    } else {
        rows.forEach(row => {
            const checkbox = row.querySelector("input[type='checkbox']");
            const daysInput = row.querySelector("input[type='number'].days-manufacturingMW");
            const textNode = checkbox?.parentElement;
            const text = textNode ? textNode.textContent.trim().replace(/\s+/g, '-') : "";
            if (checkbox.checked && daysInput && checkboxAdd.checked) {
                const days = parseInt(daysInput.value) || 0; 
                addRowProfitManufacturingMW(checkbox, days, text);
            }
        });
    }
    updateTotalCost()
    updateRowNumbers(profitSection)
}


function addRowProfitManufacturingMW(checkbox, days, title){
    const tbodyProfits = $$$('profit-section');
    const rowCountProfits = tbodyProfits.querySelectorAll('tr').length; // Correct row count
    const uniqueRowId = `profit-row-manufacturingMW`
    const profitByday =  $$$('profitByDay').value
    // Create a new table row for Profits input
    const newRowProfits = document.createElement('tr');
    newRowProfits.id = uniqueRowId;
    newRowProfits.classList.add('generated-by-utils');
    newRowProfits.innerHTML = `
        <td class="text-center p-0"><strong>${rowCountProfits}</strong></td>
        <td colspan="4"  class="p-0">
            <div class="d-flex align-items-center ">
                <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                    <option value="${title}"></option> 
                </select>
                <input class="form-control-budget" type="text" id="profit_desc" name="profit_desc" value="Profit by manufaturin workshop ${title}" readonly disabled>
            </div>
        </td>
        <td class="p-0">
            <input class="form-control-budget" type="text" name="Profit_lead-time"    value="${days} days" readonly disabled>
        </td>
        <td class="p-0"  style="width:200px"> 
            <input class="form-control-budget profit_item'" type="number" name="Profit_UnitCost" step="1"   id="profit_item" value="${days*profitByday}" readonly disabled>
        </td>                                            
`;
    tbodyProfits.appendChild(newRowProfits);
    updateSelectOptions()
};

function removeRowProfitManufacturingMW() {
    const rows = document.querySelectorAll('[id^="profit-row-manufacturingMW"]');
    console.log(rows)
    rows.forEach(row => row.remove());
}

function reloadRowProfitManufacturingMW(){
    removeRowProfitManufacturingMW();
    const rows = document.querySelectorAll("#cost_per_manufacturingMW tr");
    const checkboxProfit = $$$('cboxMWadd')
    rows.forEach(row => {
        const checkbox = row.querySelector("input[type='checkbox']");
        const daysInput = row.querySelector("input[type='number'].days-manufacturingMW");
        const textNode = checkbox?.parentElement;
        const text = textNode ? textNode.textContent.trim().replace(/\s+/g, '-') : "";
        if (checkbox.checked && daysInput && checkboxProfit.checked) {
            const days = parseInt(daysInput.value) || 0; 
            addRowProfitManufacturingMW(checkbox, days, text);
        }
    });
    updateRowNumbers(laborSection)
    updateTotalCost()
}


function reloadDataManufacturingMW(input){
    const row = input.closest("tr");
    const checkbox = row.querySelector("input[type='checkbox']");
    checkbox.checked = false;
    checkManufacturingCostsMW(checkbox)
    checkbox.checked = true;
    checkManufacturingCostsMW(checkbox)
}

function reloadDataManufacturingMWAll() {
    const tbody = document.getElementById("cost_per_manufacturingMW");
    const rows = tbody.querySelectorAll("tr");
    rows.forEach(row => {
        const checkbox = row.querySelector("input[type='checkbox']");
        if (checkbox && checkbox.checked) {
            const input = row.querySelector("input[type='number']");
            if (input) {
                reloadDataManufacturingMW(input); // Llamar a la función para ese input
            }
        }
    });
}


// Función para eliminar un item (span) y actualizar todos los selects
function removeItem(element, value) {
    const span = element.parentElement;
    const item = $$$(`manufacturing-${value.trim().replace(/\s+/g, '-')}`);
    const itemMW = $$$(`manufacturingMW-${value.trim().replace(/\s+/g, '-')}`);
    var checkbox = $$$(`check-manufacturing-${value.trim().replace(/\s+/g, '-')}`)
    var checkboxMW = $$$(`check-manufacturingMW-${value.trim().replace(/\s+/g, '-')}`)
             
    checkbox.checked = false
    checkManufacturingCosts(checkbox)
    checkboxMW.checked = false
    checkManufacturingCostsMW(checkboxMW)
    span.remove();
    item.remove();
    itemMW.remove()
    const index = items.indexOf(value);
    if (index > -1) {
        items.splice(index, 1);
    }
    var checkbox = $$$('use-day-in-itemsManufacturing');
    if (checkbox.checked){
        checkbox.checked = !checkbox.checked;
        useDaysInMF()
        checkbox.checked = true;
        useDaysInMF()}
    removeAllElemetsByItems(value)
    updateSelectOptions();
    calculateTotalByItem();
    reloadRowProfitManufacturingMW()
    const projectsCountSpan = document.getElementById('projects-count');
    projectsCountSpan.textContent = items.length - 1;

}
function removeAllElemetsByItems(item){
    const selects = document.querySelectorAll(".innerSelect");
    const filteredSelects = Array.from(selects).filter(select => select.value === item)
    .filter(select => {
        const parentRow = select.closest('tr');
        return parentRow && !parentRow.classList.contains('generate_by_items'); 
    });
    filteredSelects.forEach(select => {
        const removeButton = select.closest('tr')?.querySelector('.remove_btn');
        if (removeButton) {
            removeButton.click();
        }
    });
}

// Actualiza las opciones en todos los selects con clase "innerSelect"
function updateSelectOptions() {
    const selects = document.querySelectorAll(".innerSelect");
    selects.forEach(select => {
        const selectedValue = select.value;
        select.innerHTML = ""; 
        
        // Añadir las opciones existentes en el array
        items.forEach(value => {
            const newOption = document.createElement("option");
            newOption.value = value;
            newOption.textContent = value;
            select.appendChild(newOption);
        });
        if (items.includes(selectedValue)) {
            select.value = selectedValue;
        }
        
    });
    calculateTotalByItem()
}


// Evitar que el formulario se envíe al presionar Enter
$$$('itemInput').addEventListener('keydown', function(event) {
if (event.key === 'Enter') {
    event.preventDefault();    
    addItem(); // Agregar el item al presionar Enter
}
});


let costManagement = $('#cost-management')
let itemSelects = costManagement.querySelectorAll('#itemsSelect');
let costInputs = costManagement.querySelectorAll('#total_Cost');


function calculateTotalByItem() {
let itemSelects = costManagement.querySelectorAll('#itemsSelect');
validateInputs()
const totalsByItem = {};
const descriptionByItem = {};
itemSelects.forEach((select, index) => {
    const selectedItem = select.value;

    // Inicializar el total si no existe
    if (!totalsByItem[selectedItem]) {
        totalsByItem[selectedItem] = 0;
    }

    if (!descriptionByItem[selectedItem]) {
        descriptionByItem[selectedItem] = {};
    }

    // Obtener el costo correspondiente según la sección
    let cost = 0; // Inicializar cost

    if (select.closest('#materials-section')) {
        // Usar querySelector en lugar de getElementById
        const materialCostInput = select.parentElement.parentElement.parentElement.querySelector("#materials_Cost");
        if(materialCostInput){
            cost = parseFloat(materialCostInput.value)
        }
    } else if (select.closest('#contractor-section')) {
        const contractorCostInput = select.parentElement.parentElement.parentElement.querySelector("#contractor_UnitCost");
        if(contractorCostInput){
            cost = parseFloat(contractorCostInput.value)
        }
    } else if (select.closest('#labor-section')) {
        const laborCostInput = select.parentElement.parentElement.parentElement.querySelector("#Labor_Cost");
        if(laborCostInput){
            cost = parseFloat(laborCostInput.value)
        }
    } else if (select.closest('#misc-section')) {
        const miscCostInput = select.parentElement.parentElement.parentElement.querySelector("#misc_UnitCost");
        if(miscCostInput){
            cost = parseFloat(miscCostInput.value)
        }
    }
    else if (select.closest('#deducts10')) {
            const dedusctsCostInput = select.parentElement.parentElement.parentElement.querySelector("#deducts_UnitCost");
            if(dedusctsCostInput){
                cost = parseFloat(dedusctsCostInput.value)
        }
    }
        
    // Sumar el costo al total
    nameDesc = select.parentElement.querySelector("input").value
    totalsByItem[selectedItem] += cost; 
    descriptionByItem[selectedItem][nameDesc] = cost
    
    // Para depuración: mostrar el total actual por cada elemento
});



// Mostrar todos los totales al final

// Obtener la referencia al cuerpo de la tabla
const tableBody = document.querySelector('#cost_per_items tbody');

// Limpiar el contenido de la tabla (en caso de que ya existan datos)
tableBody.innerHTML = '';
// Obtener las claves (nombres de los ítems) y ordenarlas alfabéticamente
const sortedItems = Object.keys(totalsByItem).sort();

// Iterar sobre los ítems ordenados
sortedItems.forEach(item => {
    if (totalsByItem.hasOwnProperty(item)) {
        // Crear una nueva fila
        row = `
        <tr >
            <td class="p-0  px-2">${item}</td>
            <td class="p-0  px-2">$${totalsByItem[item].toFixed(2)}</td>
        </tr>`
        // Añadir la fila al cuerpo de la tabla
        tableBody.insertAdjacentHTML('beforeend', row);
        // Añadir las celdas a la fila
        

        Object.entries(descriptionByItem[item]).forEach(([subKey, subValue]) => {
                row = `
                <tr class="table-secondary p-4" style="font-size:0.8rem">
                    <td colspan="2" class="p-0 border px-4">* $${subKey} - (${subValue})</td>
                </tr>`;
            tableBody.insertAdjacentHTML('beforeend', row);
            });
            
    }
});
calculateProfitByItem()
calculateProfitAndCostByItem()
}
// Escuchar los cambios en los selects y los costos
itemSelects.forEach(select => select.addEventListener('change', calculateTotalByItem));
costInputs.forEach(input => input.addEventListener('input', calculateTotalByItem));

calculateTotalByItem();


function checkManufacturingCosts(checkbox) {
const isChecked = checkbox.checked;
const valueItem = checkbox.parentElement.textContent
if (isChecked) {
    addRowCostManufacturing(valueItem);
    var lastProfits = $$('.automaticProfit');
    if (lastProfits) {
        lastProfits.forEach(profit => {
            profit.remove();
        });
    }
    useDaysInMF()
    updateRowNumbers(profitSection)
} else {
    
    removeRowCostManufacturing(valueItem);
}
updateRowNumbers(laborSection)
};


function addRowCostManufacturing(valueItem){
const tbodyLabor = $$$('labor-section');
let stringIdItem = valueItem.trim().replace(/\s+/g, '-')
const rowCountLabor = tbodyLabor.querySelectorAll('tr').length; 
const days = $$$('days-manufacturing-'+stringIdItem).value
const CostByDay = $$$("Labor_Total").value
const TotlaCostByItems = CostByDay * days
// Create a new table row for labor input
const newRowLabor = document.createElement('tr');
newRowLabor.id = valueItem.trim().replace(/\s+/g, '-')
newRowLabor.classList.add('generated-by-utils');

newRowLabor.innerHTML = `
        <td class="text-center p-0"><strong>${rowCountLabor}</strong></td>
        <td colspan="2"  class="p-0 ">
            <div class="d-flex align-items-center ">
                <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                    <option value="${stringIdItem}">${stringIdItem}</option>
                </select>
                <input class="form-control-budget" type="text" id="laborDescInput" name="Labor_desc" value="manufacturing cost (${stringIdItem})">
            </div>
        </td>
        <td class="p-0">
            <div class="input-group p-0">
                <span class="money_simbol_input">$</span>
                <input class="form-control-budget text-end" type="number" name="Labor_hourly" step="1" value="${CostByDay}" readonly>
            </div>
        </td>
        <td class="p-0"><input class="form-control-budget" type="number" name="Labor_hour" step="0" value="${days}" readonly></td>
        <td class="p-0"><input class="form-control-budget" type="text" name="Labor_lead-time" value="${days} days"></td>                           
        <td class="p-0"> 
            <div class="input-group p-0">
                <span class="money_simbol_input">$</span>
                <input class="form-control-budget text-end" type="number" name="Labor_Cost" id="Labor_Cost" step="0.01" value="${TotlaCostByItems}" readonly disabled>
            </div>
        </td>
        <td class="p-0 text-center" style="width:0px">
        </td>
`;

tbodyLabor.appendChild(newRowLabor);
updateSelectOptions()
updateTotalCost()

}


function removeRowCostManufacturing(valueItem){
    const tbodyLabor = $$$('labor-section');
    // Create a new table row for labor input
    const RowLabor = document.getElementById(valueItem.trim().replace(/\s+/g, '-'));
    if (RowLabor){
        RowLabor.remove()
        updateTotalCost()
    }
    }


function removeRowCostManufacturingMW(valueItem){
    const tbodyLabor = $$$('labor-section');
    // Create a new table row for labor input
    const RowLabor = document.getElementById(`${valueItem.trim().replace(/\s+/g, '-')}MW`);
    if (RowLabor){
        RowLabor.remove()
        updateTotalCost()
    }
}
    
const tableCostPerManufacturing = $('#cost_per_manufacturing');

tableCostPerManufacturing.addEventListener('input', function(event) {
    if (event.target.classList.contains('days-manufacturing')) {
        updateRowCostManufacturing(event.target);
    }
    
});


function updateRowCostManufacturing(input){
    const item = input.parentElement.parentElement.querySelector('.checkManufacturingCost');
    if (input.value && item.checked){
        removeRowCostManufacturing(item.textContent.replace(/\s+/g, '').trim());
        addRowCostManufacturing(item.textContent.replace(/\s+/g, '').trim())
        updateTotalCost()
    }
}     


var checkboxitemsManufacturing = $$$('use-day-in-itemsManufacturing')                                                                                  
checkboxitemsManufacturing.addEventListener('change', useDaysInMF);

function useDaysInMF() {
    try {
        var checkbox = $$$('use-day-in-itemsManufacturing');
        var profitTr = $$$('automaticProfitperDay');
        var profitPerDay = $('#profit-value');
        var daysPerItems = $$('.days-manufacturing');
        var namePerItems = $$('.checkManufacturingCost');

        if (checkbox.checked) {
            try {
                if (profitTr) {
                    profitTr.remove();
                }
            } catch (error) {
                console.error("Error removing 'automaticProfitperDay' row:", error);
            }

            daysPerItems.forEach((day, index) => {
                try {
                    // Obtener el checkbox correspondiente a esta fila
                    const checkbox = namePerItems[index].querySelector('input[type="checkbox"]');
            
                    // Verificar si el checkbox está marcado
                    if (checkbox && checkbox.checked) {
                        const tbodyProfit = $$$('profit-section');
                        const rowCountProfit = tbodyProfit.querySelectorAll('tr').length; // Correct row counT

                        var newRow = document.createElement("tr");
                        newRow.id = `automaticProfit`; // ID único para cada fila
                        newRow.className = "align-middle generated-by-utils automaticProfit";
                        newRow.innerHTML = `
                            <td class="text-center p-0"><strong>${rowCountProfit}</strong></td>
                            <td colspan="4"  class="p-0">
                                <div class="d-flex align-items-center">
                                    <select id="itemsSelect" class="innerSelect me-2" style="width: auto;">
                                        <option value="${namePerItems[index].textContent.trim().replace(/\s+/g, '-')}">${namePerItems[index].textContent.trim().replace(/\s+/g, '-')}</option> 
                                    </select>
                                    <input class="form-control-budget" type="text" name="profit_desc" value="profit per manufacturing day (${namePerItems[index].textContent.trim()})">
                                </div>
                            </td>
                            <td class="p-0">
                                <input class="form-control-budget" type="text" name="profit_lead-time" value="Inmediate" step="0.01">
                            </td>
                            <td class="p-0" style="width:200px">
                                <input class="form-control-budget profit_item'" type="number" name="Profit_UnitCost" step="1"   id="profit_item" value="${day.value * profitPerDay.value}" readonly>
                            </td>`;
                        // Agregar la nueva fila al tbody solo si el checkbox está marcado\
                        tbodyProfit.appendChild(newRow);
                    }
                } catch (error) {
                    console.error("Error adding new row for automaticProfit:", error);
                }
            });
            
            try {
                updateSelectOptions();
                updateTotalCost();
            } catch (error) {
                console.error("Error updating select options:", error);
            }

        } else {
            try {
                var lastProfits = $$('.automaticProfit');
                if (lastProfits) {
                    lastProfits.forEach(profit => {
                        profit.remove();
                    });
                }
                toggleProfitByDay()
            } catch (error) {
                console.error("Error removing rows with class 'automaticProfit':", error);
            }

            try {
                updateSelectOptions();
            } catch (error) {
                console.error("Error updating select options after removal:", error);
            }
        }
    } catch (error) {
        console.error("Unexpected error in useDaysInMF function:", error);
    }
    updateRowNumbers(profitSection)
}


function calculateProfitByItem() {
    profitManagement = $('.profitManagement')
    let itemSelects = profitManagement.querySelectorAll('#itemsSelect');
    
    const totalsByItem = {};
    const descriptionByItem = {};
    
    itemSelects.forEach((select, index) => {
        const selectedItem = select.value;
    
        // Inicializar el total si no existe
        if (!totalsByItem[selectedItem]) {
            totalsByItem[selectedItem] = 0;
        }
    
        if (!descriptionByItem[selectedItem]) {
            descriptionByItem[selectedItem] = {};
        }
    
        // Obtener el costo correspondiente según la sección
        let cost = 0; // Inicializar cost
    
        if (select.closest('#profit-section')) {
            // Usar querySelector en lugar de getElementById
            const profitCostInput = select.parentElement.parentElement.parentElement.querySelector("#profit_item");
            if(profitCostInput){
                cost = parseFloat(profitCostInput.value) || 0;
            }
            
        }
    
        // Sumar el costo al total
        nameDesc = select.parentElement.querySelector("input").value
        totalsByItem[selectedItem] += cost; 
        descriptionByItem[selectedItem][nameDesc] = cost
        
    });
    
    // Mostrar todos los totales al final
    
    // Obtener la referencia al cuerpo de la tabla
    const tableBody = document.querySelector('#profit_per_items tbody');
    
    // Limpiar el contenido de la tabla (en caso de que ya existan datos)
    tableBody.innerHTML = '';
    // Obtener las claves (nombres de los ítems) y ordenarlas alfabéticamente
    const sortedItems = Object.keys(totalsByItem).sort();
    
    // Iterar sobre los ítems ordenados
    sortedItems.forEach(item => {
        if (totalsByItem.hasOwnProperty(item)) {
            // Crear una nueva fila
            row = `
            <tr >
                <td class="p-0  px-2">${item}</td>
                <td class="p-0  px-2">$${totalsByItem[item].toFixed(2)}</td>
            </tr>`
            // Añadir la fila al cuerpo de la tabla
            tableBody.insertAdjacentHTML('beforeend', row);
            // Añadir las celdas a la fila
            
    
            Object.entries(descriptionByItem[item]).forEach(([subKey, subValue]) => {
                    row = `
                    <tr class="table-secondary p-4" style="font-size:0.8rem">
                        <td colspan="2" class="p-0 border px-4">* $${subKey} - (${subValue})</td>
                    </tr>`;
                tableBody.insertAdjacentHTML('beforeend', row);
                });
                
        }
    });
    }
function calculateProfitAndCostByItem() {
    let itemSelects = $$('#itemsSelect');
    
    const totalsByItem = {};
    const descriptionByItem = {};
    
    itemSelects.forEach((select, index) => {
        const selectedItem = select.value;
    
        // Inicializar el total si no existe
        if (!totalsByItem[selectedItem]) {
            totalsByItem[selectedItem] = 0;
        }
    
        if (!descriptionByItem[selectedItem]) {
            descriptionByItem[selectedItem] = {};
        }
    
        // Obtener el costo correspondiente según la sección
        let cost = 0; // Inicializar cost
        if (select.closest('#materials-section')) {
            // Usar querySelector en lugar de getElementById
            const materialCostInput = select.parentElement.parentElement.parentElement.querySelector("#materials_Cost");
            if(materialCostInput){
                cost = parseFloat(materialCostInput.value) || 0;
            }
        } else if (select.closest('#contractor-section')) {
            const contractorCostInput = select.parentElement.parentElement.parentElement.querySelector("#contractor_UnitCost");
            if(contractorCostInput){
                cost = parseFloat(contractorCostInput.value) || 0; // Convertir a número
            }
        } else if (select.closest('#labor-section')) {
            const laborCostInput = select.parentElement.parentElement.parentElement.querySelector("#Labor_Cost");
            if(laborCostInput){
                cost = parseFloat(laborCostInput.value) || 0
            }
        } else if (select.closest('#misc-section')) {
            const miscCostInput = select.parentElement.parentElement.parentElement.querySelector("#misc_UnitCost");
            if(miscCostInput){
                cost = parseFloat(miscCostInput.value) || 0
            }
            
        } else if  (select.closest('#profit-section')) {
            // Usar querySelector en lugar de getElementById
            const profitCostInput = select.parentElement.parentElement.parentElement.querySelector("#profit_item");
            if(profitCostInput){
                cost = parseFloat(profitCostInput.value) || 0;
            }
            
        }
    
        // Sumar el costo al total
        nameDesc = select.parentElement.querySelector("input").value
        totalsByItem[selectedItem] += cost; 
        descriptionByItem[selectedItem][nameDesc] = cost
        
    });
    
    // Mostrar todos los totales al final
    
    // Obtener la referencia al cuerpo de la tabla
    const tableBody = document.querySelector('#selling_price tbody');
    
    // Limpiar el contenido de la tabla (en caso de que ya existan datos)
    tableBody.innerHTML = '';
    // Obtener las claves (nombres de los ítems) y ordenarlas alfabéticamente
    const sortedItems = Object.keys(totalsByItem).sort();
    
    // Iterar sobre los ítems ordenados
    sortedItems.forEach(item => {
        if (totalsByItem.hasOwnProperty(item)) {
            // Crear una nueva fila
            row = `
            <tr >
                <td class="p-0  px-2">${item}</td>
                <td class="p-0  px-2">$${totalsByItem[item].toFixed(2)}</td>
            </tr>`
            // Añadir la fila al cuerpo de la tabla
            tableBody.insertAdjacentHTML('beforeend', row);
            // Añadir las celdas a la fila
            
    
            Object.entries(descriptionByItem[item]).forEach(([subKey, subValue]) => {
                    row = `
                    <tr class="table-secondary p-4" style="font-size:0.8rem">
                        <td colspan="2" class="p-0 border px-4">* $${subKey} - (${subValue})</td>
                    </tr>`;
                tableBody.insertAdjacentHTML('beforeend', row);
                });
                
        }
    });
    }


document.getElementById('productDetail-form').addEventListener('input', function(event) {
    calculateTotalByItem()
});
    


document.addEventListener("DOMContentLoaded", function() {
    const manufacturingSection = document.getElementById("manufacturingItems");
    const totalField = document.getElementById("Labor_Total");
    updateTotalCost()
    

    // Función para actualizar el total y manejar checkboxes
    function updateTotal() {
        let total = 0;

        // Sumar los valores de todos los inputs de tipo number
        manufacturingSection.querySelectorAll('input[type="number"]').forEach(input => {
            total += parseFloat(input.value) || 0; // Sumar el valor o 0 si está vacío
        });

        totalField.value = total; // Actualiza el campo de total

        // Habilitar o deshabilitar checkboxes
        toggleCheckboxes(false);
        toggleCheckboxes(true);
        updateRowNumbers(laborSection);
    }

    // Función para manejar el cambio en los inputs
    function handleInputChange(event) {
        updateTotal();
    }

    manufacturingSection.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener("input", handleInputChange);
    });
});



function toggleCheckboxes(enable) {
    const checkboxesContainer = document.getElementById("cost_per_manufacturing");
    checkboxesContainer.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = enable; // Habilita o deshabilita el checkbox
        checkManufacturingCosts(checkbox); // Llama a la función correspondiente

    });
}

document.addEventListener("DOMContentLoaded", function() {
    const costPerManufacturing = document.getElementById("cost_per_manufacturing");
    function updateTotalDays(event) {
        if (event.target.classList.contains('days-manufacturing')) {
            toggleCheckboxes(false);
            toggleCheckboxes(true);
            try {
                var lastProfits = $$('.automaticProfit');
                if (lastProfits) {
                    lastProfits.forEach(profit => {
                        profit.remove();
                    });
                    useDaysInMF()
                }
                
            } catch (error) {
                console.error("Error removing rows with class 'automaticProfit':", error);
            }
            updateRowNumbers(laborSection);
        }
    }

    costPerManufacturing.addEventListener("input", updateTotalDays);

    const daysInput = document.getElementById("days-per-profit");
    const profitInput = document.getElementById("profit-value");

    daysInput.addEventListener("input", () => {
        var checkbox = $$$('use-day-in-itemsManufacturing');
        if (checkbox.checked){
            checkbox.checked = !checkbox.checked;
            useDaysInMF()
            checkbox.checked = true;
            useDaysInMF()
        }else {
            var checkbox = $$$("cbox3");
            checkbox.checked = !checkbox.checked;
            toggleProfitByDay()
            checkbox.checked = true;
            toggleProfitByDay()
        }
    });

    profitInput.addEventListener("input", () => {
        
        var checkbox = $$$('use-day-in-itemsManufacturing');
        if (checkbox.checked){
            checkbox.checked = !checkbox.checked;
            useDaysInMF()
            checkbox.checked = true;
            useDaysInMF()
        }else {
            var checkbox = $$$("cbox3");
            checkbox.checked = !checkbox.checked;
            toggleProfitByDay()
            checkbox.checked = true;
            toggleProfitByDay()
        }
        
    });
});
function getUtilsData() {
    // Obtener el checkbox y verificar si está marcado HOLE
    const addHoleChecked = document.getElementById('Add-hole-check').checked;
    const addUtilitiesChecked = document.getElementById('add-utilities-per-FT').checked;
    const addRemovalChecked = document.getElementById('add-removal-per-FT').checked;

    // Obtener los valores de los campos de texto y convertir a número
    const totalFt = parseFloat(document.getElementById("total-ft").value.replace(/,/g, '')) || 0;
    const totalPosts = parseFloat(document.getElementById("total-posts").value.replace(/,/g, '')) || 0;

    // Obtener los valores de los campos relacionados con los agujeros
    const holeQuantity = parseFloat(document.getElementById("QT").value.replace(/,/g, '')) || 0;
    const holeCost = parseFloat(document.getElementById("cost-???").value.replace(/,/g, '')) || 0;
    const costPerHole = parseFloat(document.getElementById("cost-per-hole").value.replace(/,/g, '')) || 0;

    // Obtener los valores de los campos de utilidades por FT
    const utilitiesCost = parseFloat(document.getElementById("utilities-cost").value.replace(/,/g, '')) || 0;

    // Obtener los valores de los costos de remoción por FT
    const removalCost = parseFloat(document.getElementById("removal-cost").value.replace(/,/g, '')) || 0;

    const addUnitCostMi = document.getElementById('cbox2').checked;

    let tableData = {
        manufacturingItems: {},
        costPerManufacturing: [] 
    };
    const rows = document.querySelectorAll("#manufacturingItems tr");
    rows.forEach(row => {
        const cells = row.querySelectorAll("td");
        const total = parseFloat(document.getElementById("Labor_Total").value.replace(/,/g, '')) || 0;
        tableData.manufacturingItems['Total'] = total;
        if (cells.length > 1) {
            const itemName = cells[0].textContent.trim();
            const value = parseFloat(cells[1].querySelector("input").value.replace(/,/g, '')) || 0;
            tableData.manufacturingItems[itemName] = value;
        }
    });

    // Obtener valores de la segunda tabla (checkboxes y días)
    const costRows = document.querySelectorAll("#cost_per_manufacturing tr");

    costRows.forEach(row => {
        const checkBox = row.querySelector("input[type='checkbox']");
        const itemName = row.querySelector("td").textContent.trim();
        const daysValue = parseFloat(row.querySelector("input[type='number']").value.replace(/,/g, '')) || 0;

        const isChecked = checkBox ? checkBox.checked : false;

        tableData.costPerManufacturing.push({
            item: itemName,
            checked: isChecked,
            days: daysValue
        });
    });

    const addUnitCostMW = document.getElementById('cboxMW').checked;
    const dataUnitCostMWItems = [];
    const dataUnitCostMWCost = [];

    // Obtener las filas de la tabla #manufacturingItems (items)table_UnitCostMW
    const manufacturingItems = document.querySelectorAll("#manufacturingItemsMW tr");
    manufacturingItems.forEach(row => {
        const columns = row.querySelectorAll("td");
        if (columns.length >= 2) {
            const itemName = columns[0].textContent.trim();
            const inputValue = parseFloat(columns[1].querySelector("input") ? columns[1].querySelector("input").value.replace(/,/g, '') : 0);
            dataUnitCostMWCost.push({
                item: itemName,
                value: inputValue
            });
        }
    });

    const costRowsMW = document.querySelectorAll("#cost_per_manufacturingMW tr");
    costRowsMW.forEach(row => {
        const columns = row.querySelectorAll("td");
        if (columns.length >= 4) {
            const checkBox = row.querySelector("input[type='checkbox']");
            const itemName = columns[0].textContent.trim();
            const qtyWLD = parseFloat(columns[1].querySelector(".qtyWLD-manufacturingMW") ? columns[1].querySelector(".qtyWLD-manufacturingMW").value.replace(/,/g, '') : 0);
            const qtyASST = parseFloat(columns[2].querySelector(".qtyASST-manufacturingMW") ? columns[2].querySelector(".qtyASST-manufacturingMW").value.replace(/,/g, '') : 0);
            const days = parseFloat(columns[3].querySelector(".days-manufacturingMW") ? columns[3].querySelector(".days-manufacturingMW").value.replace(/,/g, '') : 0);

            const isChecked = checkBox ? checkBox.checked : false;

            dataUnitCostMWItems.push({
                item: itemName,
                checked: isChecked,
                qtyWLD: qtyWLD,
                qtyASST: qtyASST,
                days: days
            });
        }
    });

    const adddataProfitByDay  = document.getElementById('cbox3').checked;

    const adddataProfitByDayMW  = document.getElementById('cboxMWadd').checked;
    const valueProfitByDayMW = document.getElementById('profitByDay').value;

    const dataProfitByDay = {
        days: null,
        profitValue: null,
        useDayInItemsManufacturing: false
    };
    
    // Obtener los valores de la tabla #table_ProfitByDay
    const profitByDayTable = document.querySelector("#table_ProfitByDay");

    // Verificar si la tabla existe y si contiene los elementos esperados
    if (profitByDayTable) {
        // Obtener el valor de los días
        const daysInput = profitByDayTable.querySelector("#days-per-profit");
        if (daysInput && daysInput.value) {
            dataProfitByDay.days = parseFloat(daysInput.value) || 0.00; // Asigna 0.00 si el valor es vacío o no es un número
        } else {
            dataProfitByDay.days = 0.00; // Si no hay valor, asigna 0.00
        }

        // Obtener el valor del beneficio
        const profitValueInput = profitByDayTable.querySelector("#profit-value");
        if (profitValueInput && profitValueInput.value) {
            dataProfitByDay.profitValue = parseFloat(profitValueInput.value) || 0.00; // Asigna 0.00 si el valor es vacío o no es un número
        } else {
            dataProfitByDay.profitValue = 0.00; // Si no hay valor, asigna 0.00
        }

        // Obtener el estado del checkbox
        const useDayInItemsCheckbox = profitByDayTable.querySelector("#use-day-in-itemsManufacturing");
        if (useDayInItemsCheckbox) {
            dataProfitByDay.useDayInItemsManufacturing = useDayInItemsCheckbox.checked;
        }
    } else {
        // Si no hay tabla, inicializa los datos con valores predeterminados
        dataProfitByDay.days = 0.00; // 0.00 como valor predeterminado
        dataProfitByDay.profitValue = 0.00; // 0.00 como valor predeterminado
        dataProfitByDay.useDayInItemsManufacturing = false; // Valor predeterminado para el checkbox
    }


    const addLoans  = document.getElementById('cbox4').checked;
    const dataLoansToProject = {
        percentage: null
    };
    
    // Obtener el valor de la tabla #loans-to-the-project
    const loansTable = document.querySelector("#loans-to-the-project");
    
    // Obtener el valor del porcentaje
    const percentageInput = loansTable.querySelector("#percentage-loans");
    if (percentageInput) {
        dataLoansToProject.percentage =  parseFloat(percentageInput.value) || 0.00;
    }
    
    const dataHolePosts = {
        addHoleChecked: addHoleChecked,
        addUtilitiesChecked: addUtilitiesChecked,
        addRemovalChecked: addRemovalChecked,
        totalFt: totalFt,
        totalPosts: totalPosts,
        holeQuantity: holeQuantity,
        holeCost: holeCost,
        costPerHole: costPerHole,
        utilitiesCost: utilitiesCost,
        removalCost: removalCost
    };

    const dataUnitCostMi = {
        addUnitCostMi: addUnitCostMi,  // Estado del checkbox
        manufacturingData: tableData.manufacturingItems,  // Datos de la primera tabla
        costData: tableData.costPerManufacturing  // Datos de la segunda tabla
        
    };

    const dataUnitCostMW = {
        addUnitCostMW: addUnitCostMW,  // Estado del checkbox
        dataUnitCostMWCost: dataUnitCostMWCost,  // Datos de la primera tabla
        dataUnitCostMWItems: dataUnitCostMWItems, // Datos de la segunda tabla
        adddataProfitByDayMW:adddataProfitByDayMW,
        valueProfitByDayMW:valueProfitByDayMW
    };

    const dataProfitByDayTotal = {
        adddataProfitByDay: adddataProfitByDay,  // Estado del checkbox
        dataProfitByDay: dataProfitByDay,  // Datos de la primera tabla
    };

    const dataLoans = {
        addLoans: addLoans,  // Estado del checkbox
        dataLoansToProject: dataLoansToProject,  // Datos de la primera tabla
    };
    const profitTotal = $$$("total_profit").value;
    const costTotal = $$$("grand_Cost").value
    const profitFTTotal = parseFloat(profitTotal.replace(/,/g, ''));
    const costFTTotal = parseFloat(costTotal.replace(/,/g, ''));

    data = {
        dataHolePosts:dataHolePosts,
        dataUnitCostMi:dataUnitCostMi,
        dataUnitCostMW:dataUnitCostMW,
        dataProfitByDay: dataProfitByDayTotal,
        dataLoans: dataLoans,
        profitTotal:profitFTTotal,
        costTotal:costFTTotal,
    }
    return data
}

function isGeneratedByUtils(row) {
    return row.classList.contains('generated-by-utils');
}

function getCostManagementData() {
    const laborData = [];
    const materialsData = [];
    const contractorData = [];
    const miscData = [];
    const deductsData = [];
    const profitData = [];

    // Obtener datos de la sección de trabajo (labor)
    document.querySelectorAll('#labor-section tr').forEach((row, index) => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 0) {
            laborData.push({
                index: index,
                laborDescription: cells[1]?.querySelector('input[name="Labor_desc"]')?.value || '',
                costByDay: parseFloat(cells[2]?.querySelector('input[name="Labor_hourly"]')?.value) || 0,
                days: parseInt(cells[3]?.querySelector('input[name="Labor_hour"]')?.value) || 0,
                leadTime: cells[4]?.querySelector('input[name="Labor_lead-time"]')?.value || '',
                laborCost: parseFloat(cells[5]?.querySelector('input[name="Labor_Cost"]')?.value) || 0,
                itemValue: row.querySelector('#itemsSelect')?.value, 
                isGeneratedByUtils: row.classList.contains('generated-by-utils') || false,
            });
        }
    });

    // Obtener datos de la sección de materiales
    document.querySelectorAll('#materials-section tr').forEach((row, index) => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 0) {
            materialsData.push({
                index: index,
                materialDescription: cells[1]?.querySelector('input[name="materials_desc"]')?.value || '',
                quantity: parseInt(cells[2]?.querySelector('input[name="materials_qt"]')?.value) || 0,
                unitCost: parseFloat(cells[3]?.querySelector('input[name="materials_UnitCost"]')?.value) || 0,
                leadTime: cells[4]?.querySelector('input[name="materials_lead-time"]')?.value || '',
                cost: parseFloat(cells[5]?.querySelector('input[name="materials_Cost"]')?.value) || 0,
                itemValue: row.querySelector('#itemsSelect')?.value, 
                isGeneratedByUtils: row.classList.contains('generated-by-utils') || false,
                isGeneratedByCheckList: row.classList.contains('AutoCheckList') || false,
                idGeneratedByCheckList: row.classList.contains('AutoCheckList') ? row.id || '' : 'null',
            });
        }
    });

    // Obtener datos de la sección de contratistas
    document.querySelectorAll('#contractor-section tr').forEach((row, index) => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 0) {
            contractorData.push({
                index: index,
                contractorDescription: cells[1]?.querySelector('input[name="contractor_desc"]')?.value || '',
                leadTime: cells[2]?.querySelector('input[name="contractor_lead-time"]')?.value || '',
                contractorCost: cells[3]?.querySelector('input[name="contractor_UnitCost"]')?.value || '',
                itemValue: row.querySelector('#itemsSelect')?.value, 
                isGeneratedByUtils: row.classList.contains('generated-by-utils') || false,
            });
        }
    });

    // Obtener datos de la sección de misceláneos (misc)
    document.querySelectorAll('#misc-section tr').forEach((row, index) => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 0) {
            miscData.push({
                index: index,
                description: cells[1]?.querySelector('input[name="misc_desc"]')?.value || '',
                leadTime: cells[2]?.querySelector('input[name="misc_lead-time"]')?.value || '',
                miscCost: cells[3]?.querySelector('input[name="misc_UnitCost"]')?.value || '',
                itemValue: row.querySelector('#itemsSelect')?.value, 
                isGeneratedByUtils: row.classList.contains('generated-by-utils') || false
            });
        }
    });

    // Obtener datos de la sección de deducciones (deducts)
    document.querySelectorAll('#deducts-section tr').forEach((row, index) => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 0) {
            deductsData.push({
                index: index,
                description: cells[1]?.querySelector('input[name="deducts_desc"]')?.value || '',
                leadTime: cells[2]?.querySelector('input[name="deducts_lead-time"]')?.value || '',
                unitCost: cells[3]?.querySelector('input[name="deducts_UnitCost"]')?.value || 0,
                itemValue: row.querySelector('#itemsSelect')?.value, 
                isGeneratedByUtils: row.classList.contains('generated-by-utils') || false
            });
        }
    });

    // Obtener datos de la sección de ganancias (profit)
    document.querySelectorAll('#profit-section tr').forEach((row, index) => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 0) {
            profitData.push({
                index: index,
                profitDescription: cells[1]?.querySelector('input[name="profit_desc"]')?.value || '',
                leadTime: cells[2]?.querySelector('input[name="profit_lead-time"]')?.value || '',
                profitValue: cells[3]?.querySelector('input[name="Profit_UnitCost"]')?.value || 0,
                itemValue: row.querySelector('#itemsSelect')?.value, 
                isGeneratedByUtils: row.classList.contains('generated-by-utils') || false,
            });
        }
    });
    primaryBudget = document.querySelector(".related-budget")?.dataset.relatedBudgetId || null;



    const utilsData = getUtilsData();
    const data = {
        laborData,
        materialsData,
        contractorData,
        miscData,
        deductsData,
        profitData,
        utilsData,
        primaryBudget, 
    };

    const projectId = document.getElementById('project-container').dataset.projectId;
    const csrfToken = document.getElementById('csrf-token').dataset.csrf;
    let isModify = false
    let isChangeOrder = false
    let budgetId = null
    const hiddenDataElement = document.getElementById('hiddenData');
    if (hiddenDataElement) {
        isModify = hiddenDataElement.getAttribute('data-modify') === 'true';
        budgetId = hiddenDataElement.getAttribute('data-budget-id');} 

    const hiddenDataElementCO = document.getElementById('hiddenDataCO');
    if (hiddenDataElementCO) {
        isChangeOrder = hiddenDataElementCO.getAttribute('data-change-order') === 'true';
        budgetId = hiddenDataElementCO.getAttribute('data-budget-id');
        console.log(budgetId)} 

    if (isChangeOrder) {
        fetch(`/projects/${projectId}/new_change_order/${budgetId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(data),
        })
        .then(() => {
            const loadingOverlay = document.getElementById('loadingOverlay');
            loadingOverlay.classList.add('d-none');
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    } else if (isModify) {
        fetch(`/projects/${projectId}/edit_budget/${budgetId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(data),
        })
        .then(() => {
            const loadingOverlay = document.getElementById('loadingOverlay');
            window.location.href = `/projects/${projectId}/`;
            loadingOverlay.classList.add('d-none');
        })
        .catch((error) => {
            console.error('Error:', error);
        });} else if (!isChangeOrder && !isModify)  {
        // Llamada para crear un presupuesto nuevo
        fetch(`/projects/${projectId}/new_budget/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(data),
        })
        .then(() => {
            window.location.href = `/projects/${projectId}/`;
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }

    }
 

document.getElementById('save-btn').addEventListener('click', function(event) {
    event.preventDefault(); // Evita el envío inmediato del formulario

    // Referencia al botón y al overlay de carga
    const saveButton = document.getElementById('save-btn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Mostrar overlay de carga
    loadingOverlay.classList.remove('d-none');
    
    // Deshabilitar el botón para evitar múltiples envíos
    saveButton.setAttribute('disabled', true);
    
    // Llama a la función para manejar los datos
    getCostManagementData();
});




document.querySelectorAll('[data-bs-toggle="collapse"]').forEach((toggle) => {
    console.log('Se activo')
    toggle.addEventListener('click', function () {
        const icon = this; // El ícono que se hizo clic
        const targetId = this.getAttribute('data-bs-target'); // Obtiene el ID del colapso
        const target = document.querySelector(targetId);

        // Listener para actualizar la clase cuando el colapso termine
        target.addEventListener('shown.bs.collapse', () => {
            icon.classList.add('rotated');
        });

        target.addEventListener('hidden.bs.collapse', () => {
            icon.classList.remove('rotated');
        });
    });
});


function validateInputs() {
    let saveBtn = 'none'
    const inputs = document.querySelectorAll('#management-section input'); 
    saveBtn = document.getElementById('save-btn');
    let allValid = true;
    inputs.forEach(input => {
        if (!input.readOnly) {
            if (input.value.trim() === '') {
                input.style.boxShadow = '0px 4px 5px 0px rgba(255, 0, 0, 0.54)';
                allValid = false; // Marcamos que hay un input inválido
            } else {
                input.style.boxShadow = '';
            }
        }
    });
    saveBtn.disabled = !allValid;
}

document.querySelectorAll('#management-section input').forEach(input => {
    input.addEventListener('input', validateInputs);
});

validateInputs();



function addPaintRow() {
    const paintId = "paint_Automatic"; // ID único para la fila de pintura
    const tbodyMaterial = document.getElementById('materials-section');
    const existingRow = document.getElementById(paintId);

    if (existingRow) {
        tbodyMaterial.removeChild(existingRow);
        calculateTotalByItem()
        updateRowNumbers(materialsSection)
    } else {
        const paintDetails = {
            item_value: "Paint", 
            material_description: "General painting for the project", 
            quantity: 0, 
            unit_cost: 0, 
            lead_time: "N/A", 
            cost: 0, 
            id: paintId ,
            isCheckList: true
        };

        // Llama a la función para crear la fila del material pasando los datos
        createMaterialRow(paintDetails);
    }
}


function addConcrete() {
    const concreteId = "concrete_Automatic"; // ID único para la fila de concreto
    const tbodyMaterial = document.getElementById('materials-section');
    const existingRow = document.getElementById(concreteId);

    if (existingRow) {
        tbodyMaterial.removeChild(existingRow);
        calculateTotalByItem();
        updateRowNumbers(materialsSection);
    } else {
        const concreteDetails = {
            item_value: "Concrete", 
            material_description: "General concrete for the project", 
            quantity: 0, 
            unit_cost: 0, 
            lead_time: "N/A", 
            cost: 0, 
            id: concreteId,
            isCheckList: true
        };

        createMaterialRow(concreteDetails);
    }
}

function addWelding() {
    const weldingId = "welding_Automatic"; // ID único para la fila de soldadura
    const tbodyMaterial = document.getElementById('materials-section');
    const existingRow = document.getElementById(weldingId);

    if (existingRow) {
        tbodyMaterial.removeChild(existingRow);
        calculateTotalByItem();
        updateRowNumbers(materialsSection);
    } else {
        const weldingDetails = {
            item_value: "Welding Ext.", 
            material_description: "Welding extension for the project", 
            quantity: 0, 
            unit_cost: 0, 
            lead_time: "N/A", 
            cost: 0, 
            id: weldingId,
            isCheckList: true
        };

        createMaterialRow(weldingDetails);
    }
}

function addDrawings() {
    const drawingsId = "drawings_Automatic"; // ID único para la fila de dibujos
    const tbodyMaterial = document.getElementById('materials-section');
    const existingRow = document.getElementById(drawingsId);

    if (existingRow) {
        tbodyMaterial.removeChild(existingRow);
        calculateTotalByItem();
        updateRowNumbers(materialsSection);
    } else {
        const drawingsDetails = {
            item_value: "Drawings", 
            material_description: "Architectural drawings for the project", 
            quantity: 0, 
            unit_cost: 0, 
            lead_time: "N/A", 
            cost: 0, 
            id: drawingsId,
            isCheckList: true
        };

        createMaterialRow(drawingsDetails);
    }
}

function addWindscreen() {
    const windscreenId = "windscreen_Automatic"; // ID único para la fila de parabrisas
    const tbodyMaterial = document.getElementById('materials-section');
    const existingRow = document.getElementById(windscreenId);

    if (existingRow) {
        tbodyMaterial.removeChild(existingRow);
        calculateTotalByItem();
        updateRowNumbers(materialsSection);
    } else {
        const windscreenDetails = {
            item_value: "Windscreen", 
            material_description: "Windscreen for the project", 
            quantity: 0, 
            unit_cost: 0, 
            lead_time: "N/A", 
            cost: 0, 
            id: windscreenId,
            isCheckList: true 
        };

        createMaterialRow(windscreenDetails);
    }
    updateTotalCost()
    calculateTotalByItem()
}


function resizeInput(input) {
    // Crear un elemento temporal para medir el tamaño del texto
    const tempElement = document.createElement("span");
    tempElement.style.visibility = "hidden";
    tempElement.style.position = "absolute";
    tempElement.style.whiteSpace = "nowrap";
    tempElement.style.font = window.getComputedStyle(input).font;
    
    // Copiar el texto del input al elemento temporal
    tempElement.textContent = input.value || input.placeholder;
    
    // Insertar temporalmente el elemento en el DOM para medirlo
    document.body.appendChild(tempElement);
    const textWidth = tempElement.offsetWidth + 20; // Agregar un margen extra
    document.body.removeChild(tempElement);

    // Ajustar el ancho del input al tamaño del texto
    input.style.width = `${textWidth}px`;
}

document.getElementById('toggleDisplayButton').addEventListener('click', function () {
    const costManagement = document.getElementById('cost-management');
    const displayButtonIcon = document.getElementById('DisplayButton');
    const elements = document.querySelectorAll('.costTable');
    if (costManagement.classList.contains('flex-row')) {
        costManagement.classList.remove('flex-row');
        costManagement.classList.add('flex-column');
        displayButtonIcon.classList.remove('bi-file-spreadsheet-fill');
        displayButtonIcon.classList.add('bi-layout-sidebar-reverse');
        elements.forEach((element) => {
            element.classList.remove('col-md-6');
        });
    } else {
        costManagement.classList.remove('flex-column');
        costManagement.classList.add('flex-row');
        displayButtonIcon.classList.remove('bi-layout-sidebar-reverse');
        displayButtonIcon.classList.add('bi-file-spreadsheet-fill');
        elements.forEach((element) => {
            element.classList.add('col-md-6');
        });
    }
});