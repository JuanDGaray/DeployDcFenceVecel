
function autoResize(textarea) {
    textarea.style.height = 'auto';  // Reinicia la altura
    textarea.style.height = (textarea.scrollHeight) + 'px';  // Ajusta a la altura del contenido
    console.log(textarea.scrollHeight, 'hecho')
}

function autorResizeAllTextAreas() {
    const textareascopes = document.querySelectorAll('.scope-input');
    const textareamaterials = document.querySelectorAll('.materials-input');
    textareascopes.forEach((textarea) => {
        autoResize(textarea);
    });
    textareamaterials.forEach((textarea) => {
        autoResize(textarea);
    });
}


document.addEventListener("DOMContentLoaded", () => {
    autorResizeAllTextAreas()
});

function generatePDF() {
    // Selección del contenedor principal
    const element = document.getElementById('main-container');

    // Configuración de opciones para html2pdf
    const opt = {
        filename: `PS_{{ proposal.project_name }}__{{ proposal.id }}__{{now|date:"m-d-y" }}.pdf`,
        image: { 
            type: 'jpeg', 
            quality: 1
        },
        html2canvas: { 
            scale: 2,
            useCORS: true,
            logging: false,
            letterRendering: true
        },
        jsPDF: { 
            unit: 'mm', 
            format: 'a4', 
            orientation: 'portrait',
            hotfixes: ['px_scaling']
        },
        margin: [0, 0, 0, 0]
    };

    // Generación y descarga del PDF
    html2pdf().set(opt).from(element).save();
}