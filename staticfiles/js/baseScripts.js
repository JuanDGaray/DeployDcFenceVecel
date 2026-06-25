document.addEventListener('DOMContentLoaded', function () {
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  const tooltipList = tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl, {
    html: true,
    sanitize: false
  }));
});


  
function showAlert(message, type) {
  const alertContainer = document.getElementById("alert-container");
  const alert = document.createElement("div");
  alert.classList.add("alert", `alert-${type}`, "alert-dismissible", "fade", "show");
  alert.role = "alert";
  alert.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  alertContainer.appendChild(alert);
  setTimeout(() => {
      alert.classList.remove("show");
      alert.classList.add("fade");
      alert.remove();
  }, 4000); 
  return alert;
}


function parseFetchJson(response) {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    return response.text().then(() => {
      const error = new Error('Server returned a non-JSON response');
      error.status = response.status;
      error.nonJson = true;
      throw error;
    });
  }
  return response.json().then((data) => {
    if (!response.ok) {
      const error = new Error(data.message || data.error || 'Request failed');
      error.status = response.status;
      Object.assign(error, data);
      throw error;
    }
    return data;
  });
}

function ajaxGetRequest(url, successCallback, errorCallback) {
  fetch(url, {
    credentials: 'same-origin',
    headers: {
      Accept: 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    },
  })
    .then(parseFetchJson)
    .then((data) => {
      successCallback(data);
    })
    .catch((error) => {
      if (!error.nonJson) {
        console.error('Error:', error);
      }
      if (errorCallback) {
        errorCallback(error);
      }
    });
}


function ajaxPostRequest(url, data, csrfToken, successCallback, errorCallback) {
  const isFormData = data instanceof FormData;
  const headers = {
    'X-CSRFToken': csrfToken,
  };
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  console.log('data', data);
  headers.Accept = 'application/json';
  headers['X-Requested-With'] = 'XMLHttpRequest';

  fetch(url, {
    method: 'POST',
    credentials: 'same-origin',
    body: isFormData ? data : JSON.stringify(data),
    headers: headers,
  })
    .then(parseFetchJson)
    .then((data) => {
      successCallback(data);
    })
    .catch((error) => {
      if (!error.nonJson) {
        console.error('Ajax Error:', error);
      }
      if (errorCallback) errorCallback(error);
    });
}


