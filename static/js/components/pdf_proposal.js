
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
