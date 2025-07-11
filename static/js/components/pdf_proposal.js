
// Email Modal Functions - Global scope
function openEmailModal() {
    const modal = new bootstrap.Modal(document.getElementById('emailModal'));
    modal.show();
}

function sendProposalEmail() {
    const form = document.getElementById('emailForm');
    const formData = new FormData(form);
    
    // Get project and proposal IDs from data attributes
    const mainContainer = document.getElementById('main-pdf');
    const projectId = mainContainer.getAttribute('data-project-id');
    const proposalId = mainContainer.getAttribute('data-proposal-id');
    
    // Add project and proposal IDs
    formData.append('project_id', projectId);
    formData.append('proposal_id', proposalId);
    
    // Show loading state
    const sendButton = document.querySelector('#emailModal .btn-success');
    const originalText = sendButton.innerHTML;
    sendButton.innerHTML = '<i class="bi bi-hourglass-split"></i> Sending...';
    sendButton.disabled = true;
    
    // Send the email
    fetch('/send_proposal_email/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showAlert('Email sent successfully!', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('emailModal'));
            modal.hide();
        } else {
            showAlert('Error sending email: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error sending email. Please try again.', 'danger');
    })
    .finally(() => {
        // Restore button state
        sendButton.innerHTML = originalText;
        sendButton.disabled = false;
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Text area functions
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
