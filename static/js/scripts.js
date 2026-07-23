document.addEventListener("DOMContentLoaded", function() {
    // Navigation menu
    const navMenu = document.getElementById('nav-menu');
    const navToggle = document.getElementById('nav-toggle');
    const navClose = document.getElementById('nav-close');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('show-menu');
        });
    }

    if (navClose && navMenu) {
        navClose.addEventListener('click', () => {
            navMenu.classList.remove('show-menu');
        });
    }

    // Enter → next field (delegation — works after HTMX swaps)
    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter') return;
        const input = e.target;
        if (!input.matches('.input-box input, .input-box select, .field input, .profile-container input')) return;
        if (input.type === 'submit' || input.tagName === 'BUTTON') return;
        e.preventDefault();
        const fields = Array.from(document.querySelectorAll('.input-box input, .input-box select, .field input, .profile-container input'));
        const index = fields.indexOf(input);
        if (index === -1) return;
        const next = fields[index + 1];
        if (next) next.focus();
        else input.blur();
    });

    document.addEventListener('change', (e) => {
        const input = e.target;
        if (!input.matches('.input-box input, .input-box select, .field input, .profile-container input')) return;
        if (input.value.trim() !== '' || (input.tagName === 'SELECT' && input.selectedIndex !== 0)) {
            input.classList.add('filled');
        } else {
            input.classList.remove('filled');
        }
    });

    // Copy / delete / confirmation — event delegation (works after HTMX swaps)
    let deleteForm = null;
    let orderId = null;

    document.addEventListener('click', function(event) {
        const copyBtn = event.target.closest('.copy');
        if (copyBtn) {
            const row = copyBtn.closest('tr');
            if (!row) return;
            const rowData = Array.from(row.querySelectorAll('td:nth-child(-n+5)')).map(td => td.innerText).join('\n');
            navigator.clipboard.writeText(rowData);

            const clipboardIcon = copyBtn.querySelector('.clipboard');
            const checkmarkIcon = copyBtn.querySelector('.checkmark');
            if (clipboardIcon && checkmarkIcon) {
                clipboardIcon.style.display = 'none';
                checkmarkIcon.style.display = 'inline-block';
                setTimeout(() => {
                    clipboardIcon.style.display = 'inline-block';
                    checkmarkIcon.style.display = 'none';
                }, 1500);
            }
            return;
        }

        const removeInvoiceBtn = event.target.closest('.remove-invoice');
        if (removeInvoiceBtn) {
            event.preventDefault();
            const removeConfirmation = document.getElementById('removeConfirmation');
            if (removeConfirmation) {
                removeConfirmation.style.display = 'block';
                deleteForm = removeInvoiceBtn.closest('form');
                orderId = null;
            }
            return;
        }

        const deleteOrderBtn = event.target.closest('a.delete');
        if (deleteOrderBtn) {
            event.preventDefault();
            const removeConfirmation = document.getElementById('removeConfirmation');
            if (removeConfirmation) {
                removeConfirmation.style.display = 'block';
                orderId = deleteOrderBtn.getAttribute('order-id');
                deleteForm = null;
            }
            return;
        }

        if (event.target.closest('#cancel-btn') || event.target.closest('#exit-btn')) {
            const removeConfirmation = document.getElementById('removeConfirmation');
            if (removeConfirmation) removeConfirmation.style.display = 'none';
            return;
        }

        if (event.target.closest('#delete-btn')) {
            const removeConfirmation = document.getElementById('removeConfirmation');
            if (deleteForm) {
                deleteForm.submit();
            } else if (orderId) {
                htmx.ajax('GET', `/orders/pending/delete/${orderId}/`, {
                    target: '#main-content',
                    swap: 'innerHTML',
                });
            }
            if (removeConfirmation) removeConfirmation.style.display = 'none';
        }
    });

    const loginCard = document.getElementById("login-card");
    const loginOverlay = document.getElementById("login-overlay");
    const closeIcon = document.getElementById("close-icon");
    const loginForm = document.querySelector(".login-form");
    const loginBtn = document.querySelector(".login-heading");
    const signupBtn = document.querySelector(".signup-heading");
    const signupLink = document.querySelector("form .signup-link a");

    function displayLoginForm() {
        if (!loginCard || !loginOverlay) return;
        loginCard.style.display = "flex";
        loginOverlay.style.display = "block";
    }

    function hideLoginForm() {
        if (!loginCard || !loginOverlay) return;
        loginCard.style.display = "none";
        loginOverlay.style.display = "none";
    }

    function moveLoginForm(direction) {
        if (!loginForm) return;
        loginForm.style.marginLeft = direction === "left" ? "-50%" : "0%";
    }

    document.addEventListener('click', function (e) {
        if (e.target.closest('#login-btn, #back-to-login, #animated-login-btn')) {
            displayLoginForm();
        }
    });

    if (closeIcon) {
        closeIcon.addEventListener("click", hideLoginForm);
    }

    if (signupBtn) {
        signupBtn.onclick = () => moveLoginForm("left");
    }

    if (loginBtn) {
        loginBtn.onclick = () => moveLoginForm("right");
    }

    if (signupLink && signupBtn) {
        signupLink.onclick = () => {
            signupBtn.click();
            return false;
        };
    }
});

// File Upload Confirmation
function handleFileSelection(event, orderId) {
    event.preventDefault();
    const fileInput = document.getElementById('invoice_' + orderId);
    if (fileInput) fileInput.click();
}

function showConfirmationBox(orderId, fileInput) {
    if (!fileInput || fileInput.files.length === 0) return;

    const uploadConfirmation = document.getElementById('uploadConfirmation');
    if (!uploadConfirmation) return;

    uploadConfirmation.style.display = 'block';

    const fileNameElement = uploadConfirmation.querySelector('.file-name');
    if (fileNameElement) {
        fileNameElement.innerText = 'Selected file: ' + fileInput.files[0].name;
    }

    const confirmButton = document.getElementById('confirm-button');
    if (confirmButton) {
        confirmButton.onclick = () => {
            const form = document.getElementById('form_' + orderId);
            if (form) form.submit();
            uploadConfirmation.style.display = 'none';
        };
    }

    const cancelButton = document.getElementById('cancel-button');
    if (cancelButton) {
        cancelButton.onclick = () => {
            fileInput.value = '';
            uploadConfirmation.style.display = 'none';
        };
    }

    const exitButton = document.getElementById('exit-button');
    if (exitButton) {
        exitButton.onclick = () => {
            fileInput.value = '';
            uploadConfirmation.style.display = 'none';
        };
    }
}

window.initOrderInsights = function () {
    const dateRange = document.getElementById('dateRange');
    const selectAllCheckbox = document.getElementById('selectAll');
    const form = document.getElementById('updateAmountForm');
    if (!dateRange || !selectAllCheckbox || !form) return;

    if (dateRange._flatpickr) {
        dateRange._flatpickr.destroy();
    }

    let selectedDates = (dateRange.value || '').split(' to ');
    selectedDates = (selectedDates.length === 2 && selectedDates[0] && selectedDates[1])
        ? selectedDates.map(date => date.trim())
        : [];

    if (typeof flatpickr === 'function') {
        flatpickr(dateRange, {
            mode: 'range',
            dateFormat: 'Y-m-d',
            defaultDate: selectedDates,
            allowInput: false,
            theme: 'light'
        });
    }

    const selectedOrdersInput = document.getElementById('selectedOrdersInput');
    const selectedCountSpan = document.getElementById('selectedCount');
    const selectedRowsCount = document.getElementById('selectedRowsCount');
    const statsTableBody = document.getElementById('statsTableBody');
    const totalQuantity = document.getElementById('totalQuantity');
    const totalReturn = document.getElementById('totalReturn');

    const updateSelectedCount = () => {
        const count = document.querySelectorAll('.order-checkbox:checked:not(#selectAll)').length;
        if (selectedCountSpan) {
            selectedCountSpan.textContent = `${count} SELECTED`;
            selectedCountSpan.classList.toggle('d-none', count === 0);
        }
        if (selectedRowsCount) {
            selectedRowsCount.textContent = count;
        }
    };

    const updateSidebarTable = () => {
        if (!statsTableBody || !totalQuantity || !totalReturn) return;
        let modelStats = {};
        let totalQty = 0;
        let totalRet = 0;

        document.querySelectorAll('.order-checkbox:not(#selectAll)').forEach((checkbox) => {
            if (checkbox.checked) {
                const row = checkbox.closest('tr');
                if (!row || row.cells.length < 5) return;
                const model = row.cells[3].textContent.trim();
                const returnAmount = parseFloat(row.cells[4].textContent.trim()) || 0;

                if (!modelStats[model]) {
                    modelStats[model] = { quantity: 1, return: returnAmount };
                } else {
                    modelStats[model].quantity += 1;
                    modelStats[model].return += returnAmount;
                }

                totalQty += 1;
                totalRet += returnAmount;
            }
        });

        statsTableBody.innerHTML = '';
        for (const model in modelStats) {
            const tr = document.createElement('tr');
            const modelCell = document.createElement('td');
            const qtyCell = document.createElement('td');
            const retCell = document.createElement('td');
            modelCell.textContent = model;
            qtyCell.textContent = String(modelStats[model].quantity);
            retCell.textContent = `₹${modelStats[model].return}`;
            tr.appendChild(modelCell);
            tr.appendChild(qtyCell);
            tr.appendChild(retCell);
            statsTableBody.appendChild(tr);
        }

        totalQuantity.textContent = totalQty;
        totalReturn.textContent = `₹${totalRet}`;
    };

    selectAllCheckbox.onchange = function () {
        document.querySelectorAll('.order-checkbox:not(#selectAll)').forEach((checkbox) => {
            checkbox.checked = selectAllCheckbox.checked;
            checkbox.closest('tr')?.classList.toggle('table-info', selectAllCheckbox.checked);
        });
        updateSelectedCount();
        updateSidebarTable();
    };

    document.querySelectorAll('.order-checkbox:not(#selectAll)').forEach((checkbox) => {
        checkbox.onchange = function () {
            this.closest('tr')?.classList.toggle('table-info', this.checked);
            updateSelectedCount();
            updateSidebarTable();
        };
    });

    form.onsubmit = function () {
        const selectedOrders = [];
        document.querySelectorAll('.order-checkbox:not(#selectAll)').forEach((checkbox) => {
            if (checkbox.checked) selectedOrders.push(checkbox.value);
        });
        if (selectedOrdersInput) {
            selectedOrdersInput.value = selectedOrders.join(',');
        }
    };

    form.onkeydown = (event) => {
        if (event.key === 'Enter') event.preventDefault();
    };

    updateSelectedCount();
    updateSidebarTable();
};

document.addEventListener('DOMContentLoaded', () => {
    if (typeof window.initOrderInsights === 'function') {
        window.initOrderInsights();
    }
    if (typeof window.initLedger === 'function') {
        window.initLedger();
    }
    if (typeof window.initHome === 'function') {
        window.initHome();
    }
    if (typeof window.initPaymentsDashboard === 'function') {
        window.initPaymentsDashboard();
    }
});

window.initHome = function () {
    const particlesEl = document.getElementById('particles-js');
    if (!particlesEl) return;

    const startParticles = () => {
        if (typeof particlesJS !== 'function') return;
        particlesEl.innerHTML = '';
        particlesJS('particles-js', {
            particles: {
                number: { value: 80, density: { enable: true, value_area: 800 } },
                color: { value: '#00cccc' },
                shape: { type: 'circle', stroke: { width: 0, color: '#000000' } },
                opacity: { value: 0.5, random: true, anim: { enable: false, speed: 1, opacity_min: 0.1, sync: false } },
                size: { value: 3, random: true, anim: { enable: false, speed: 40, size_min: 0.1, sync: false } },
                line_linked: { enable: true, distance: 150, color: '#00cccc', opacity: 0.4, width: 1 },
                move: { enable: true, speed: 3, direction: 'none', random: false, straight: false, out_mode: 'out', bounce: false, attract: { enable: false, rotateX: 600, rotateY: 1200 } }
            },
            interactivity: {
                detect_on: 'canvas',
                events: {
                    onhover: { enable: false },
                    onclick: { enable: false },
                    resize: true
                },
                modes: {
                    grab: { distance: 400, line_linked: { opacity: 1 } },
                    bubble: { distance: 400, size: 40, duration: 2, opacity: 8, speed: 3 },
                    repulse: { distance: 200, duration: 0.4 },
                    push: { particles_nb: 4 },
                    remove: { particles_nb: 2 }
                }
            },
            retina_detect: true
        });
    };

    if (typeof particlesJS === 'function') {
        startParticles();
        return;
    }

    if (!document.querySelector('script[data-particles-js]')) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js';
        script.dataset.particlesJs = '1';
        script.onload = startParticles;
        document.body.appendChild(script);
    }
};

window.initLedger = function () {
    const form = document.getElementById('ledgerForm');
    const dateRangeInput = document.getElementById('dateRange');
    const userSelect = document.getElementById('user');
    const descriptionSelect = document.getElementById('description');
    if (!form || !dateRangeInput || !userSelect || !descriptionSelect) return;

    // requestSubmit fires submit event so HTMX can intercept (form.submit() would full-reload)
    const submitLedger = () => {
        if (typeof form.requestSubmit === 'function') form.requestSubmit();
        else form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    };

    userSelect.onchange = submitLedger;
    descriptionSelect.onchange = submitLedger;

    if (dateRangeInput._flatpickr) {
        dateRangeInput._flatpickr.destroy();
    }

    let selectedDates = (dateRangeInput.value || '').split(' to ');
    selectedDates = (selectedDates.length === 2 && selectedDates[0] && selectedDates[1])
        ? selectedDates.map(date => date.trim())
        : [];

    if (typeof flatpickr === 'function') {
        flatpickr(dateRangeInput, {
            mode: 'range',
            dateFormat: 'Y-m-d',
            defaultDate: selectedDates,
            allowInput: false,
            theme: 'dark',
            onClose: submitLedger,
        });
    }
};

window.disableSubmitButton = function (form) {
    const button = form.querySelector("button[type='submit']");
    if (button) {
        button.disabled = true;
        button.textContent = 'Processing';
        button.style.opacity = '0.6';
    }
};

window.initPaymentsDashboard = function () {
    if (!document.querySelector('.payment-table')) return;
    const today = new Date().toISOString().split('T')[0];
    document.querySelectorAll('input[type="date"][id^="id_date_"]').forEach((input) => {
        if (!input.value) {
            input.value = today;
        }
    });
};

window.copyTrackmatchTableData = function () {
    const table = document.getElementById("trackmatch-table");
    if (!table) return;
    let copyText = "";
    table.querySelectorAll("tbody tr").forEach(row => {
        const checkbox = row.querySelector(".row-select");
        if (checkbox && checkbox.checked) {
            const user = row.children[2].innerText.trim();
            const tracking = row.children[3].innerText.trim();
            const model = row.children[4].innerText.trim();
            copyText += `${user}\t${tracking}\t${model}\n`;
        }
    });
    if (!copyText) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(copyText);
        return;
    }
    const tempTextArea = document.createElement("textarea");
    tempTextArea.value = copyText;
    document.body.appendChild(tempTextArea);
    tempTextArea.select();
    document.execCommand("copy");
    document.body.removeChild(tempTextArea);
};

window.toggleTrackmatchSelectAll = function () {
    const selectAll = document.getElementById("trackmatchSelectAll");
    if (!selectAll) return;
    document.querySelectorAll(".row-select").forEach(checkbox => {
        checkbox.checked = selectAll.checked;
    });
};

window.toggleTrackmatchMissingTable = function () {
    const missingTable = document.getElementById("missing-table");
    const mainTable = document.getElementById("trackmatch-table");
    const toggleButton = document.getElementById("toggleButton");
    if (!missingTable || !mainTable || !toggleButton) return;

    if (missingTable.style.display === "none" || missingTable.style.display === "") {
        missingTable.style.display = "table";
        mainTable.style.display = "none";
        toggleButton.textContent = "Pending";
        toggleButton.classList.remove("btn-danger");
        toggleButton.classList.add("btn-warning");
    } else {
        missingTable.style.display = "none";
        mainTable.style.display = "table";
        toggleButton.textContent = "Missing";
        toggleButton.classList.remove("btn-warning");
        toggleButton.classList.add("btn-danger");
    }
};
