
function updateTableMi(data) {
    const rows = document.querySelectorAll("#manufacturingItems tr");

    data.forEach(entry => {
        rows.forEach(row => {
            // Encuentra el `td` que tiene el nombre del item
            const itemCell = row.querySelector("td:first-child");
            if (itemCell && itemCell.textContent.trim() === entry.item) {
                // Encuentra el input asociado y actualiza su valor
                const input = row.querySelector("input");
                if (input) {
                    input.value = entry.value;
                }
            }
        });
    });
}

function updateManufacturingTable(data) {
    data.forEach(entry => {
        const row = document.querySelector(`#manufacturing-${entry.item.trim().replace(/\s+/g, '-')}`);
        if (row) {
            const daysInput = row.querySelector(`input[type="number"]`);
            if (daysInput) {
                daysInput.value = entry.days;
            }
            const checkbox = row.querySelector(`input[type="checkbox"]`);
            if (checkbox) {
                checkbox.checked = entry.checked;
                checkManufacturingCosts(checkbox)
            }
        }
    });
}

function updateManufacturingMWTable(data) {
    data.forEach(entry => {
        // Encuentra la fila por el id basado en el item
        const row = document.querySelector(`#manufacturingMW-${entry.item.trim().replace(/\s+/g, '-')}`);
        if (row) {
            // Actualiza el campo de qtyWLD si existe
            const qtyWLDInput = row.querySelector(`input.qtyWLD-manufacturingMW`);
            if (qtyWLDInput) {
                qtyWLDInput.value = entry.qtyWLD;
            }
            // Actualiza el campo de qtyASST si existe
            const qtyASSTInput = row.querySelector(`input.qtyASST-manufacturingMW`);
            if (qtyASSTInput) {
                qtyASSTInput.value = entry.qtyASST;
            }
            // Actualiza el campo de días si existe
            const daysInput = row.querySelector(`input.days-manufacturingMW`);
            if (daysInput) {
                daysInput.value = entry.days;
            }
            // Actualiza el checkbox si existe
            const checkbox = row.querySelector(`input[type="checkbox"]`);
            if (checkbox) {
                checkbox.checked = entry.checked;
                checkManufacturingCostsMW(checkbox)
            }
        }
    });
}

function populateUtils(data) {
    const utilsData = data[0];
    utilsData.cost_data.forEach(entry => addItem(entry.item));
    document.getElementById("assistantCostByDay").value = utilsData.data_unit_cost_mw[0].value;;
    document.getElementById("welderCostByDay").value = utilsData.data_unit_cost_mw[1].value;
    

    document.getElementById("Labor_gas").value = utilsData.manufacturing_data.Gas  || 0;
    document.getElementById("Labor_water").value = utilsData.manufacturing_data.Water  || 0;
    document.getElementById("Labor_Auxiliary").value = utilsData.manufacturing_data.Auxiliary  || 0;
    document.getElementById("Labor_Installer").value = utilsData.manufacturing_data.Installer  || 0;
    document.getElementById("Labor_Total").value = utilsData.manufacturing_data.Total  || 0;
    
    updateTableMi(utilsData.data_unit_cost_mw)
    updateManufacturingTable(utilsData.cost_data)
    updateManufacturingMWTable(utilsData.data_unit_cost_mw_items)

    const totalFtAdPost = document.getElementById('tbodyFt&Post')
    utilsData.totalFtAdPost.forEach((obj) => {
        // Asegúrate de que es un objeto y no vacío
        if (obj && typeof obj === "object") {
            Object.keys(obj).forEach((key) => {
                const entry = obj[key]; // Accede al contenido del objeto por la clave
                const element = document.getElementById(key); // Busca el elemento en el DOM
    
                if (element) {
                    console.log(`Elemento encontrado para ID: ${key}`);

                    const ft = entry.ft || 0;
                    const posts = entry.posts || 0;
                    const checkboxStatus = entry.checkbox_id ;
                    element.checked = checkboxStatus;
                    const ftInput = element.closest('tr').querySelector('input[name="ft"]');
                    const postsInput = element.closest('tr').querySelector('input[name="posts"]');
                    if (ftInput) {
                        ftInput.value = ft;
                    }
                    if (postsInput) {
                        postsInput.value = posts;
                    }
                } else {
                    console.warn(`No se encontró ningún elemento con ID: ${key}`);
                }
            });
        } else {
            console.warn("El objeto dentro de utilsData.totalFtAdPost no es válido.");
        }
    });
    


    document.getElementById("QT").value = utilsData.hole_quantity;
    document.getElementById("cost-???").value = utilsData.hole_cost;
    document.getElementById("cost-per-hole").value = utilsData.cost_per_hole;
    document.getElementById("utilities-cost").value = utilsData.utilities_cost;
    document.getElementById("removal-cost").value = utilsData.removal_cost;
    document.getElementById("profitByDay").value = utilsData.data_profit_by_daymw;
    document.getElementById("profit-value").value = utilsData.profit_value;
    document.getElementById("days-per-profit").value = utilsData.days;


    
    document.getElementById("cbox1").checked = utilsData.add_post_and_hole;
    document.getElementById("cbox2").checked = utilsData.add_unit_cost_mi;
    document.getElementById("cboxMW").checked = utilsData.add_unit_cost_mw;
    document.getElementById("cbox3").checked = utilsData.add_data_profit_by_day;
    document.getElementById("Add-hole-check").checked = utilsData.add_hole_checked;
    document.getElementById("add-utilities-per-FT").checked = utilsData.add_utilities_checked;
    document.getElementById("add-removal-per-FT").checked = utilsData.add_removal_checked;
    document.getElementById("cboxMWadd").checked = utilsData.add_data_profit_by_day;
    document.getElementById("use-day-in-itemsManufacturing").checked = utilsData.use_day_in_items_manufacturing
    document.getElementById("add-utilities-per-FT").checked = utilsData.add_utilities_checked;
    document.getElementById("cbox4").checked = utilsData.add_loans;

}

function addManualData(data) {
    const filteredLabors = data.labors.filter(labor => !labor.is_generated_by_utils);
    filteredLabors.forEach((material, index) => {
        createLaborRow(material)
    });

    const filteredMaterials = data.materials.filter(material => !material.is_generated_by_utils);
    filteredMaterials.forEach((material, index) => {
        createMaterialRow(material)
    });

    const filteredContractors = data.contractors.filter(contractor => !contractor.is_generated_by_utils);
    filteredContractors.forEach((contractor, index) => {
        createContractorRow(contractor)
    });

    const filteredMisc = data.misc_data.filter(misc => !misc.is_generated_by_utils);
    filteredMisc.forEach((misc, index) => {
        createMiscRow(misc)
    });

    const filteredDeducts = data.deducts.filter(deduct => !deduct.is_generated_by_utils);
    filteredDeducts.forEach((deduct, index) => {
        createDeductsRow(deduct)
    });

    const filteredProfit = data.profits.filter(profit => !profit.is_generated_by_utils);
    filteredProfit.forEach((profit, index) => {
        createProfitRow(profit)
    });
    
}

function toggleCheckboxesInChecklist(data) {
    const filteredMaterials = data.filter(material => material.is_generated_by_checklist);
    const checkboxes = document.querySelectorAll('#Checklist input[type="checkbox"]');
    const checklistIds = filteredMaterials.map(material => material.id_generated_by_checklist);
    const checkboxIds = Array.from(checkboxes).map(checkbox => checkbox.id);
    checkboxIds.forEach(checkboxId => {
        const matchingId = `${checkboxId}_Automatic`;
        if (checklistIds.includes(matchingId)) {
            const checkbox = document.querySelector(`#${checkboxId}`);
            if (checkbox) {
                checkbox.checked = true;
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    populateUtils(dataC.utils);
    addManualData(dataC)
    toggleAddHole()
    toggleUtilitiesPerFT()
    toggleTable()
    toggleUnitCostCLF()
    toggleUnitCostMW()
    toggleProfitByDay()
    activeRowProfitManufacturingMW(this)
    toggleRemmovalPerFT()
    useDaysInMF()
    toggleCheckboxesInChecklist(dataC.materials)
    reloadRowProfitManufacturingMW()
});
