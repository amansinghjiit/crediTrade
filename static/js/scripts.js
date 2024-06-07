document.addEventListener("DOMContentLoaded", function() {
    // Navigation menu 
    const navMenu = document.getElementById('nav-menu');
    const navToggle = document.getElementById('nav-toggle');
    const navClose = document.getElementById('nav-close');

    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('show-menu'); 
        });
    }

    if (navClose) {
        navClose.addEventListener('click', () => {
            navMenu.classList.remove('show-menu');
        });
    }

    // Move to next field on enter
    const inputFields = document.querySelectorAll('.input-box input, .input-box select, .field input, .profile-container input');
    inputFields.forEach((input, index, arr) => {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const nextIndex = index + 1;
                if (nextIndex < arr.length) {
                    arr[nextIndex].focus();
                } else {
                    input.blur();
                }
            }
        });
    });

    // On filling of Input and Select Field
    inputFields.forEach(input => {
        input.addEventListener('change', () => {
            if (input.value.trim() !== '' || (input.tagName === 'SELECT' && input.selectedIndex !== 0)) {
                input.classList.add('filled');
            } else {
                input.classList.remove('filled');
            }
        });
    });

    // Copy
    document.querySelectorAll('.copy').forEach(button => {
        button.addEventListener('click', () => {
            const row = button.closest('tr');
            const rowData = Array.from(row.querySelectorAll('td:nth-child(-n+5)')).map(td => td.innerText).join('\n');
            navigator.clipboard.writeText(rowData);

            const clipboardIcon = button.querySelector('.clipboard');
            const checkmarkIcon = button.querySelector('.checkmark');

            clipboardIcon.style.display = 'none';
            checkmarkIcon.style.display = 'inline-block';

            setTimeout(() => {
                clipboardIcon.style.display = 'inline-block';
                checkmarkIcon.style.display = 'none';
            }, 1500);
        });
    });

    // Delete Invoice
    const removeConfirmation = document.getElementById("removeConfirmation");
    const cancelBtn = document.getElementById("cancel-btn");
    const deleteBtn = document.getElementById("delete-btn");
    const exitBtn = document.getElementById("exit-btn");
    let deleteForm, orderId;

    // Hide confirmation page when cancel or exit button is clicked
    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => removeConfirmation.style.display = "none");
    }

    if (exitBtn) {
        exitBtn.addEventListener("click", () => removeConfirmation.style.display = "none");
    }

    // Show confirmation dialog when any remove button is clicked
    document.querySelectorAll(".remove-invoice").forEach(button => {
        button.addEventListener("click", function(event) {
            event.preventDefault();
            removeConfirmation.style.display = "block";
            deleteForm = button.closest('form');
        });
    });

    // Handle delete action when delete button is clicked
    if (deleteBtn) {
        deleteBtn.addEventListener("click", () => {
            if (deleteForm) {
                deleteForm.submit(); 
            }
            removeConfirmation.style.display = "none";
        });

        deleteBtn.addEventListener("click", function() {
            if (orderId) {
                const deleteUrl = `delete/${orderId}/`; 
                window.location.href = deleteUrl;
            }
            removeConfirmation.style.display = "none";
        });
    }

    // Handle delete order action
    document.querySelectorAll(".delete").forEach(button => {
        button.addEventListener("click", function(event) {
            event.preventDefault();
            removeConfirmation.style.display = "block";
            orderId = this.getAttribute('order-id');
        });
    });

    const loginCard = document.getElementById("login-card");
    const loginOverlay = document.getElementById("login-overlay");
    const closeIcon = document.getElementById("close-icon");
    const loginForm = document.querySelector(".login-form");
    const loginBtn = document.querySelector(".login-heading");
    const signupBtn = document.querySelector(".signup-heading");
    const signupLink = document.querySelector("form .signup-link a");
    const loginIcons = document.querySelectorAll("#login-btn, #back-to-login, #animated-login-btn");

    loginIcons.forEach(icon => {
        icon.addEventListener("click", function() {
            displayLoginForm();
        });
    });

    closeIcon.addEventListener("click", function() {
        hideLoginForm();
    });

    signupBtn.onclick = () => {
        moveLoginForm("left");
    };

    loginBtn.onclick = () => {
        moveLoginForm("right");
    };

    signupLink.onclick = () => {
        signupBtn.click();
        return false;
    };

    function displayLoginForm() {
        loginCard.style.display = "flex";
        loginOverlay.style.display = "block";
    }

    function hideLoginForm() {
        loginCard.style.display = "none";
        loginOverlay.style.display = "none";
    }

    function moveLoginForm(direction) {
        const marginLeft = direction === "left" ? "-50%" : "0%";
        loginForm.style.marginLeft = marginLeft;
    }

     // Show Latest Transaction History
     const reverseTransactionHistory = (userProfileId) => {
        const transactionHistoryModal = document.querySelector(`#transactionHistoryModal${userProfileId} tbody`);
        const rows = transactionHistoryModal.querySelectorAll('tr');
        const reversedRows = Array.from(rows).reverse();
        transactionHistoryModal.innerHTML = '';
        reversedRows.forEach(row => transactionHistoryModal.appendChild(row));
        transactionHistoryModal.classList.add('reversed');
    };

    const dueAmountLinks = document.querySelectorAll('.due-amount-link');
    dueAmountLinks.forEach(link => {
        link.addEventListener('click', () => {
            const userProfileId = link.getAttribute('data-user-id');
            const transactionHistoryModal = document.querySelector(`#transactionHistoryModal${userProfileId} tbody`);
            if (!transactionHistoryModal.classList.contains('reversed')) {
                reverseTransactionHistory(userProfileId);
            }
        });
    });
});

// File Upload Confirmation
function handleFileSelection(event, orderId) {
    event.preventDefault();
    const fileInput = document.getElementById('invoice_' + orderId);
    fileInput.click();
}

function showConfirmationBox(orderId, fileInput) {
    if (fileInput.files.length > 0) {   
        const uploadConfirmation = document.getElementById('uploadConfirmation');
        uploadConfirmation.style.display = 'block';

        const fileNameElement = uploadConfirmation.querySelector('.file-name');
        fileNameElement.innerText = 'Selected file: ' + fileInput.files[0].name;

        const confirmButton = document.getElementById('confirm-button');
        confirmButton.onclick = () => {
            const form = document.getElementById('form_' + orderId);
            form.submit();
            uploadConfirmation.style.display = 'none';
        };

        const cancelButton = document.getElementById('cancel-button');
        cancelButton.onclick = () => {
            fileInput.value = '';
            uploadConfirmation.style.display = 'none';
        };

        const exitButton = document.getElementById('exit-button');
        exitButton.onclick = () => {
            fileInput.value = '';
            uploadConfirmation.style.display = 'none';
        };
    }
}
