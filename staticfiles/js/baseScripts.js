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


function ajaxGetRequest(url, successCallback, errorCallback) {
  fetch(url)
    .then(response => {
      if (!response.ok) {
        return response.json().then(errData => {
          throw { status: response.status, ...errData };
        });
      }
      return response.json();
    })
    .then(data => {
      successCallback(data);
    })
    .catch(error => {
      console.error('Error:', error);
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
  fetch(url, {
    method: 'POST',
    body: isFormData ? data : JSON.stringify(data),
    headers: headers,
  })
    .then(response => {
      console.log('response', response);
      if (!response.ok) {
        return response.json().then(errData => {
          console.log('errData', errData);
          throw { status: response.status, ...errData };
        });
      }
      return response.json();
    })
    .then(data => {
      successCallback(data);
    })
    .catch(error => {
      console.error("Ajax Error:", error);
      if (errorCallback) errorCallback(error);
    });
}


