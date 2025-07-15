
// Email Modal Functions - Global scope
let quill = null;

function initializeQuill() {
    if (quill) return; // Ya inicializado
    
    console.log('Initializing Quill editor...'); // Debug log
    
    // Configure Quill toolbar - simplified version
    const toolbarOptions = [
        ['bold', 'italic', 'underline', 'strike'],
        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
        [{ 'size': ['small', false, 'large', 'huge'] }],
        [{ 'color': [] }, { 'background': [] }],
        [{ 'align': [] }],
    ];
    
    // Initialize Quill
    quill = new Quill('#emailBody', {
        theme: 'snow',
        modules: {
            toolbar: toolbarOptions
        },
        placeholder: 'Write your message here...'
    });
    
    console.log('Quill initialized:', quill); // Debug log
    
    // Set initial content
    const initialContent = `Dear client,

Thank you for your interest in our services. Please find attached the proposal for your project.

This proposal includes:
• Detailed scope of work
• Material specifications
• Pricing breakdown

Please review the attached proposal and let us know if you have any questions or need any modifications.

We look forward to working with you on this project.

Best regards,
DC Fence Team`;
    
    quill.setText(initialContent);
    console.log('Initial content set in Quill'); // Debug log
}

function openEmailModal() {
    console.log('Opening email modal...'); // Debug log
    const modal = new bootstrap.Modal(document.getElementById('emailModal'));
    modal.show();
    
    // Initialize Quill when modal opens
    setTimeout(() => {
        console.log('Checking if Quill needs initialization...'); // Debug log
        if (!quill) {
            console.log('Initializing Quill...'); // Debug log
            initializeQuill();
        } else {
            console.log('Quill already initialized'); // Debug log
        }
    }, 100);
}

function sendProposalEmail() {
    const form = document.getElementById('emailForm');
    const formData = new FormData();
    
    // Get basic form data
    formData.append('recipient_email', document.getElementById('recipientEmail').value);
    formData.append('recipient_name', document.getElementById('recipientName').value);
    formData.append('subject', document.getElementById('emailSubject').value);
    
    // Get rich text content from Quill
    if (!quill) {
        console.error('Quill editor not initialized!');
        alert('Editor not initialized. Please try again.');
        return;
    }
    
    const emailBody = quill.root.innerHTML;
    console.log('Quill content:', emailBody); // Debug log
    console.log('Quill content length:', emailBody.length); // Debug log
    formData.append('body', emailBody);
    
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
    fetch('/send_proposal_email/' + projectId + '/' + proposalId + '/', {
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
