let folderIDS = {};

let currentPath = ['home'];
let selectedFiles = [];

function handleFolderClick(event) {
        const folder = event.currentTarget.getAttribute('data-folder');
        const folderName = event.currentTarget.getAttribute('data-folder-name');
        currentPath = ['home', folder];
        document.getElementById('currentPath').textContent = folderName;
        displayFiles(folder);
        const folderItems = document.querySelectorAll('.folder-container');
        folderItems.forEach(f => f.classList.remove('active'));
        event.currentTarget.classList.add('active');
        const uploadBtn = document.getElementById('uploadBtn');
        uploadBtn.disabled = false;
        document.getElementById('files-container').setAttribute('data-current-folder-id', folder);
        closeModalFile()
    };
function displayFiles(folderId) {
  getChildStructure(folderId)
}


function loadFolder() {
  const projectId = $("#document-list").data("project-id");
  const formData = new FormData();
  const deleteButton = document.getElementById('button-delete-project');
  formData.append('folder_id', projectId);
  console.log(projectId)
  const loadingOverlay = document.getElementById('loadingOverlay-file');
  if (loadingOverlay.classList.contains('d-none')) {
    loadingOverlay.classList.remove('d-none');
  }
  fetch("/projects/get-folder/", {
    method: 'POST',
    body: formData,
    headers: {
      'X-CSRFToken': '{{ csrf_token }}',
    }
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Error en la solicitud');
    }
    return response.json();
    loadingOverlay.classList.add('d-none');
  })
  .then(data => {
    if (data.structure && data.structure.length > 0) {
      console.log(data.structure)
      const folderHtml = renderFolderStructure(data.structure)
      document.getElementById("document-list").innerHTML = folderHtml;
    } else {
      document.getElementById("document-list").innerHTML = "<p class='text-muted'>No se encontraron documentos.</p>";
    }
    loadingOverlay.classList.add('d-none');
  })
  .catch(error => {
    console.error("Error al cargar las carpetas:", error);
    document.getElementById("document-list").innerHTML = "<p class='text-danger'>Error al cargar los documentos.</p>";
    loadingOverlay.classList.add('d-none');
  });
}

getChildStructure = (folderId) => {
  const container = document.getElementById('child-list');
  const loadingOverlayChild = document.getElementById('loadingOverlayChild');
  if (loadingOverlayChild.classList.contains('d-none')) {
    loadingOverlayChild.classList.remove('d-none');
  }
  fetch(`/projects/get-files/${folderId}`, {
    method: 'GET',
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Error en la solicitud');
    }
    return response.json();
    loadingOverlayChild.classList.add('d-none');
  })
  .then(data => {
    if (data.structure  && data.structure.length > 0) {
      const filesHtml = renderFilesStructure(data.structure)
      document.getElementById("files-container").innerHTML = filesHtml;
    } else {
      document.getElementById("files-container").innerHTML =  '<span class="text-muted text-center w-100 align-self-center">Folder is empty, please upload files.</span>';
    }
    loadingOverlayChild.classList.add('d-none');
  })
  .catch(error => {
    console.error("Error al cargar las carpetas:", error);
    document.getElementById("files-container").innerHTML = "<p class='text-danger'>Error al cargar los documentos.</p>";
    loadingOverlayChild.classList.add('d-none');
  });
}

document.querySelector(".file-input").addEventListener('change', () => {
  const childLoadingOverlay = document.getElementById('loadingOverlayChild');
  if (childLoadingOverlay.classList.contains('d-none')) {
    childLoadingOverlay.classList.remove('d-none');
  }
  const fileInput = document.querySelector(".file-input");
  const folderIdInput = document.getElementById('files-container').getAttribute('data-current-folder-id');
  const formData = new FormData();

  if (fileInput.files.length > 0) {
      formData.append('file_name', fileInput.files[0].name);
      formData.append('mimeType', fileInput.files[0].type);
  } else {
      showAlert("No se han seleccionado archivos.", 'warning');
      return;
  }

  formData.append('folder_id', folderIdInput);

  fetch("/projects/upload-file/", {
      method: 'POST',
      body: formData,
      headers: {
          'X-CSRFToken': '{{ csrf_token }}',
      }
  })
  .then(response => response.json())
  .then(data => {
      uploadFile(fileInput.files[0], data.uploadUrl, folderIdInput);
  })
  .catch(error => {
      showAlert("Error uploading file: " + error, 'warning');
  });
});

browserFile = () => {
  const fileInput = document.querySelector(".file-input");
  fileInput.click();
};

maximize = () => {
  const modal = document.getElementById('file-viewer');
  modal.classList.toggle('fullscreen');
  const fileButtonsActions = document.getElementById('file-buttons-actions');
  fileButtonsActions.classList.toggle('fullscreen');
}

viewFile = (url) => {
  const modal = document.getElementById('iframe-file');
  modal.src = '';
  openModalFile()
  modal.src = url;
}

openModalFile = () => {
  const modal = document.getElementById('file-viewer');
  if (modal.classList.contains('d-none')) {
    modal.classList.remove('d-none');
  }
}

closeModalFile = () => {
  const modal = document.getElementById('file-viewer');
  if (modal.classList.contains('fullscreen')) {
    modal.classList.remove('fullscreen');
    const fileButtonsActions = document.getElementById('file-buttons-actions');
    fileButtonsActions.classList.remove('fullscreen');
  }
  if (!modal.classList.contains('d-none')) {
    modal.classList.add('d-none');
  }
}

function renderFilesStructure(files) {
  let html = "<div class='d-flex flex-row justify-content-start  gap-2  flex-wrap'>";
  files.forEach((file) => {
    const truncatedName = file.name.length > 25
      ? `${file.name.slice(0, 20)}...${file.formatName}` 
      : file.name;
    html += `
        <div class="d-flex flex-column position-relative justify-content-center align-items-center p-2 rounded-2 m-0 file-container border border-2" data-file="${file.id}" style="width: 100px; height: 100px; cursor: pointer;" onclick="viewFile('${file.url}')">
          <div class="position-absolute top-0 end-0 m-1" style="width: 20px; height: 20px;">
          </div>
          <i class="bi bi-${file.mimeType} fs-1 mb-2 text-primary"></i>
          <span id="file-name-${file.id}" 
                class="d-flex flex-row flex-nowrap file-name text-center"  
                style="font-size: 0.8rem; max-width: 90px; line-height: 1;">
            ${truncatedName}
          </span>
          <div class="btn-group position-absolute top-0 end-0 m-1" style="width: 20px; height: 20px;">
            <button class="btn btn-light btn-sm text-primary dropdown-toggle px-0 border border-2 rounded-2" type="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="true" onclick="event.stopPropagation();">
            </button>
            <div class="dropdown-menu z-index-100 bg-light ser-select-none" style="--bs-dropdown-min-width: .5rem !important;     --bs-dropdown-link-active-bg:rgb(219, 219, 219)">
              <button class="dropdown-item py-0 px-2 text-dark" onclick="event.stopPropagation(); viewFile('${file.url}')">View</button>
              <button class="dropdown-item py-0 px-2 text-dark" onclick="event.stopPropagation(); downloadFile('${file.url}')">Download</button>
              <button class="dropdown-item py-0 px-2 text-light bg-danger" onclick="event.stopPropagation(); deleteObjet('${file.id}')">Delete</button>
            </div>
          </div>
        </div>`;
  });
  html += "</div>";                 
  return html;
}

function renderFolderStructure(folders, parentId = '') {
  folderIDS = {}
  let html = "<div class='d-flex flex-wrap position-relative'>";
  folders.forEach((folder, index) => {
    const folderId = parentId + '-' + index;
    const restrictedNames = ['Evidence', 'Proposal', 'Documents', 'ChangeOrder', 'Invoices'];
    folderIDS[folder.name] = [folder.id]
    if (folder.type === 'folder') {
      html += `
      <div class="my-0 pe-auto w-100" style="cursor: pointer; w ">
        <div class="my-0 p-0 w-100">
          <div class="d-flex flex-row justify-content-start align-items-center folder-container px-2 py-1  rounded-2 w-100 m-0" data-folder="${folder.id}" data-folder-name="${folder.name}" onclick="handleFolderClick(event)">
                <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="30" height="30" viewBox="0 0 32 32">
                        <linearGradient id="KA3iPnJF2lqt7U2-W-Vona_oiCA327R8ADq_gr1" x1="16" x2="16" y1="4.905" y2="27.01" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#00b5f0"></stop><stop offset="1" stop-color="#008cc7"></stop></linearGradient><path fill="url(#KA3iPnJF2lqt7U2-W-Vona_oiCA327R8ADq_gr1)" d="M26,27H6c-1.105,0-2-0.895-2-2V7c0-1.105,0.895-2,2-2h4.027c0.623,0,1.22,0.247,1.66,0.688	l0.624,0.624C12.753,6.753,13.35,7,13.973,7H26c1.105,0,2,0.895,2,2v16C28,26.105,27.105,27,26,27z"></path><linearGradient id="KA3iPnJF2lqt7U2-W-Vonb_oiCA327R8ADq_gr2" x1="16" x2="16" y1="5" y2="27" gradientUnits="userSpaceOnUse"><stop offset="0" stop-opacity=".02"></stop><stop offset="1" stop-opacity=".15"></stop></linearGradient><path fill="url(#KA3iPnJF2lqt7U2-W-Vonb_oiCA327R8ADq_gr2)" d="M26,7H13.973	c-0.623,0-1.22-0.247-1.66-0.688l-0.625-0.625C11.247,5.247,10.65,5,10.027,5H6C4.895,5,4,5.895,4,7v18c0,1.105,0.895,2,2,2h20	c1.105,0,2-0.895,2-2V9C28,7.895,27.105,7,26,7z M27.75,25c0,0.965-0.785,1.75-1.75,1.75H6c-0.965,0-1.75-0.785-1.75-1.75V7	c0-0.965,0.785-1.75,1.75-1.75h4.027c0.56,0,1.087,0.218,1.484,0.615l0.625,0.625c0.491,0.491,1.143,0.761,1.837,0.761H26	c0.965,0,1.75,0.785,1.75,1.75V25z"></path><linearGradient id="KA3iPnJF2lqt7U2-W-Vonc_oiCA327R8ADq_gr3" x1="16" x2="16" y1="8.922" y2="27.008" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#00dcff"></stop><stop offset=".859" stop-color="#00bfff"></stop><stop offset="1" stop-color="#00a8e0"></stop></linearGradient><path fill="url(#KA3iPnJF2lqt7U2-W-Vonc_oiCA327R8ADq_gr3)" d="M27,27H5c-1.105,0-2-0.895-2-2V11	c0-1.105,0.895-2,2-2h22c1.105,0,2,0.895,2,2v14C29,26.105,28.105,27,27,27z"></path><linearGradient id="KA3iPnJF2lqt7U2-W-Vond_oiCA327R8ADq_gr4" x1="16" x2="16" y1="9" y2="27" gradientUnits="userSpaceOnUse"><stop offset="0" stop-opacity=".02"></stop><stop offset="1" stop-opacity=".15"></stop></linearGradient><path fill="url(#KA3iPnJF2lqt7U2-W-Vond_oiCA327R8ADq_gr4)" d="M27,9H5c-1.105,0-2,0.895-2,2v14	c0,1.105,0.895,2,2,2h22c1.105,0,2-0.895,2-2V11C29,9.895,28.105,9,27,9z M28.75,25c0,0.965-0.785,1.75-1.75,1.75H5	c-0.965,0-1.75-0.785-1.75-1.75V11c0-0.965,0.785-1.75,1.75-1.75h22c0.965,0,1.75,0.785,1.75,1.75V25z"></path>
                        </svg>
                    <span id="folder-name-${folder.id}" class='d-flex flex-row flex-nowrap ms-2 folder-name'>
                    ${folder.name}
                </span>
            </div>`}
  });
  html += "</div>";
  return html;
}




async function uploadFile(file, uploadUrl, folderIdInput) {
  const filesize = file.size;
  // Ensure we have a valid MIME type, default to application/octet-stream if not available
  const contentType = file.type || 'application/octet-stream';
  
  const response = await fetch(uploadUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': contentType,
        'Content-Length': filesize,
      },
      body: file
  }); 
  let result = null;
  if (response.ok) {
      const data = await response.json();
      showAlert("Archivos subidos exitosamente.", 'success');
      getChildStructure(folderIdInput);
      return data;
  } else {
    showAlert("Error uploading file: " + response.statusText, 'warning');
    return null;
  }
}

  

function deleteObjet(fileId) {
  if (!confirm("Are you sure you want to delete this file?")) {
    return;
  }
  const currentFolderId = document.getElementById('files-container').getAttribute('data-current-folder-id');
  const childLoadingOverlay = document.getElementById('loadingOverlayChild');
  if (childLoadingOverlay.classList.contains('d-none')) {
    childLoadingOverlay.classList.remove('d-none');
  }
  showAlert('Borrando objeto...', 'info');
  fetch("/projects/delete-file/", {
    method: 'POST',
    body: JSON.stringify({ file_id: fileId }),
    headers: {
      'X-CSRFToken': '{{ csrf_token }}',
      'Content-Type': 'application/json'
    }
  })
  .then(response => {
    if (response.ok) {
      return response.json();
    } else {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
  })
  .then(data => {
    showAlert(data.message, 'success');
    getChildStructure(currentFolderId);
  })
  .catch(error => {
    console.error('Error deleting file:', error);
    showAlert(data.message, 'warning');
  });
  if (!childLoadingOverlay.classList.contains('d-none')) {
    childLoadingOverlay.classList.remove('d-none');
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const folderNameInput = document.getElementById("folder-name");
  const addFolderBtn = document.getElementById("add-folder-btn");

  function toggleButtonState() {
    addFolderBtn.disabled = folderNameInput.value.trim() === "";
  }
  folderNameInput.addEventListener("input", toggleButtonState);
  toggleButtonState();
});

document.getElementById("add-folder-btn").addEventListener("click", function () {
  const folderRootValue = document.getElementById("document-list").getAttribute("data-project-id");
  const folderNameInput = document.getElementById("folder-name");
  const folderName = folderNameInput.value.trim(); // Obtener el nombre de la carpeta
  const alertContainer = document.getElementById('alert-container');
  alertContainer.innerHTML = '';

  if (!folderRootValue) {
    showAlert('No se encontró un folder root válido.', 'danger');
    return;
  }

  if (!folderName) {
    showAlert('Por favor, ingresa un nombre para la carpeta.', 'warning');
    return;
  }
  const creatingAlert = showAlert('Creando carpeta, por favor no cerrar...', 'info');
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  const loadingOverlay = document.getElementById('loadingOverlay-file');
  loadingOverlay.classList.remove('d-none');
  fetch(`/projects/create-folder/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify({
      folder_root: folderRootValue,
      folder_name: folderName
    }),
  })
  .then((response) => {
    if (response.ok) {
      return response.json();
    } else {
      throw new Error("Error al crear la carpeta");
    }
  })
  .then((data) => {
    console.log("Carpeta creada exitosamente:", data);
    creatingAlert.remove();
    loadFolder();
    showAlert('Se ha creado la carpeta', 'success');  
    folderNameInput.value = '';
  })
  .catch((error) => {
    creatingAlert.remove();
    console.error("Error:", error);
    showAlert('No se pudo crear la carpeta.', 'danger');
    loadingOverlay.classList.add('d-none');
  });
});

$(document).ready(function () {
  const projectId = $("#document-list").data("project-id");
  if (projectId) {
    loadFolder(projectId);

  } else {
    $("#document-list").html("<p class='text-warning'>El proyecto no tiene un ID válido. Contacte al administrador.</p>");
    const loadingOverlay = document.getElementById('loadingOverlay-file');
    loadingOverlay.classList.add('d-none');
  }
});

function editFolderName(folderId) {
  const folderElement = document.getElementById(`folder-name-${folderId}`);
  const originalName = folderElement.textContent.trim();

  // Crear un campo de texto para editar el nombre de la carpeta
  const inputField = document.createElement('input');
  inputField.type = 'text';
  inputField.value = originalName;
  inputField.className = 'border border-secondary w-auto py-0 m-0';
  inputField.style.maxWidth = '100px';
  inputField.style.maxHeight = '20px';
  if (folderElement.hasAttribute('href')) {
    folderElement.removeAttribute('href');
}

  // Crear un botón de "check" para confirmar el cambio
  const checkButton = document.createElement('button');
  checkButton.textContent = '✔'; 
  checkButton.setAttribute('id', 'buttonCheckName');

  // Limpiar el contenido del folderElement y agregar el input y el checkButton
  folderElement.innerHTML = '';
  folderElement.appendChild(inputField);
  folderElement.appendChild(checkButton);

  // Seleccionar el texto dentro del campo de texto para facilitar la edición
  inputField.select();

  // Al hacer clic en el check, actualizamos el nombre de la carpeta
  checkButton.addEventListener('click', function() {
    const newName = inputField.value;
    updateFolderName(folderId, newName);
  });

  // Si el campo de texto pierde el foco, también actualizamos el nombre
  inputField.addEventListener('blur', function() {
    const newName = inputField.value;
    updateFolderName(folderId, newName);
  });
}