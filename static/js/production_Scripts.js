function debounce(fn, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn.apply(this, args), wait);
    };
}

let productionRequestSeq = 0;

function currentProductionView() {
    const table = document.getElementById('tableView');
    if (table && !table.classList.contains('d-none')) {
        return 'table';
    }
    return localStorage.getItem('productionView') || 'card';
}

function applyProductionView(mode) {
    const table = document.getElementById('tableView');
    const card = document.getElementById('cardView');
    if (!table || !card) {
        return;
    }
    const showTable = mode === 'table';
    table.classList.toggle('d-none', !showTable);
    card.classList.toggle('d-none', showTable);
}

function productionFiltersUrl() {
    const form = document.getElementById('productionFilters');
    const params = new URLSearchParams(new FormData(form));
    for (const [key, value] of [...params.entries()]) {
        if (!String(value).trim()) {
            params.delete(key);
        }
    }
    const query = params.toString();
    const action = form.getAttribute('action') || '/production/';
    return query ? `${action}?${query}` : action;
}

async function loadProductionResults(url) {
    const seq = ++productionRequestSeq;
    const loader = document.getElementById('loader');
    const view = currentProductionView();
    if (loader) {
        loader.classList.remove('d-none');
    }
    try {
        const response = await fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin',
        });
        if (!response.ok) {
            throw new Error('Search failed');
        }
        const html = await response.text();
        if (seq !== productionRequestSeq) {
            return;
        }
        const doc = new DOMParser().parseFromString(html, 'text/html');
        const nextResults = doc.getElementById('productionResults');
        const currentResults = document.getElementById('productionResults');
        if (nextResults && currentResults) {
            currentResults.innerHTML = nextResults.innerHTML;
        }
        const nextTotal = doc.getElementById('productionTotal');
        const currentTotal = document.getElementById('productionTotal');
        if (nextTotal && currentTotal) {
            currentTotal.textContent = nextTotal.textContent;
        }
        applyProductionView(view);
        const nextUrl = new URL(url, window.location.origin);
        history.replaceState(null, '', nextUrl.pathname + nextUrl.search);
    } catch (error) {
        console.error(error);
    } finally {
        if (seq === productionRequestSeq && loader) {
            loader.classList.add('d-none');
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const toggleTable = document.getElementById('toggleTableView');
    const toggleCard = document.getElementById('toggleCardView');
    const form = document.getElementById('productionFilters');
    const results = document.getElementById('productionResults');

    applyProductionView(localStorage.getItem('productionView') || 'card');

    if (toggleTable) {
        toggleTable.addEventListener('click', function () {
            localStorage.setItem('productionView', 'table');
            applyProductionView('table');
        });
    }
    if (toggleCard) {
        toggleCard.addEventListener('click', function () {
            localStorage.setItem('productionView', 'card');
            applyProductionView('card');
        });
    }
    if (!form || !results) {
        return;
    }

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        loadProductionResults(productionFiltersUrl());
    });

    const searchAsYouType = debounce(function () {
        loadProductionResults(productionFiltersUrl());
    }, 350);

    ['searchInputID', 'searchInputName', 'searchInputCustomer'].forEach(function (id) {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', searchAsYouType);
        }
    });

    const seller = document.getElementById('searchInputSeller');
    if (seller) {
        seller.addEventListener('change', function () {
            loadProductionResults(productionFiltersUrl());
        });
    }

    results.addEventListener('click', function (event) {
        const link = event.target.closest('a.page-link');
        if (!link) {
            return;
        }
        event.preventDefault();
        loadProductionResults(link.href);
    });
});
