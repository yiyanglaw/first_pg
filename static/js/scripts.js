document.addEventListener('DOMContentLoaded', function() {
    console.log('Clinic Management System loaded');

    // Function to confirm delete action
    const confirmDelete = (event) => {
        if (!confirm('Are you sure you want to delete this patient?')) {
            event.preventDefault();
        }
    };

    // Add event listeners to delete buttons
    document.querySelectorAll('.btn-danger').forEach(button => {
        button.addEventListener('click', confirmDelete);
    });

    // Function to validate form inputs
    const validateForm = (form) => {
        let isValid = true;
        form.querySelectorAll('input, select, textarea').forEach(input => {
            if (input.hasAttribute('required') && !input.value.trim()) {
                isValid = false;
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }
        });
        return isValid;
    };

    // Add form validation to all forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(this)) {
                event.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });

    // Function to preview image before upload
    const previewImage = (input) => {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const preview = document.getElementById('imagePreview');
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
            reader.readAsDataURL(input.files[0]);
        }
    };

    // Add image preview functionality
    const imageInput = document.getElementById('image');
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            previewImage(this);
        });
    }

    // Function to toggle password visibility
    const togglePassword = (button, inputId) => {
        const input = document.getElementById(inputId);
        if (input.type === 'password') {
            input.type = 'text';
            button.textContent = 'Hide';
        } else {
            input.type = 'password';
            button.textContent = 'Show';
        }
    };

    // Add password toggle functionality
    const passwordToggle = document.getElementById('passwordToggle');
    if (passwordToggle) {
        passwordToggle.addEventListener('click', function() {
            togglePassword(this, 'password');
        });
    }

    // Function to filter patients table
    const filterTable = (input) => {
        const filter = input.value.toUpperCase();
        const table = document.querySelector('table');
        const rows = table.getElementsByTagName('tr');

        for (let i = 1; i < rows.length; i++) {
            const nameCell = rows[i].getElementsByTagName('td')[0];
            const phoneCell = rows[i].getElementsByTagName('td')[2];
            if (nameCell && phoneCell) {
                const nameValue = nameCell.textContent || nameCell.innerText;
                const phoneValue = phoneCell.textContent || phoneCell.innerText;
                if (nameValue.toUpperCase().indexOf(filter) > -1 || phoneValue.toUpperCase().indexOf(filter) > -1) {
                    rows[i].style.display = '';
                } else {
                    rows[i].style.display = 'none';
                }
            }
        }
    };

    // Add table filtering functionality
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            filterTable(this);
        });
    }

    // Function to sort table
    const sortTable = (n) => {
        const table = document.querySelector('table');
        let rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
        switching = true;
        dir = 'asc';
        while (switching) {
            switching = false;
            rows = table.rows;
            for (i = 1; i < (rows.length - 1); i++) {
                shouldSwitch = false;
                x = rows[i].getElementsByTagName('td')[n];
                y = rows[i + 1].getElementsByTagName('td')[n];
                if (dir == 'asc') {
                    if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                        shouldSwitch = true;
                        break;
                    }
                } else if (dir == 'desc') {
                    if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                        shouldSwitch = true;
                        break;
                    }
                }
            }
            if (shouldSwitch) {
                rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                switching = true;
                switchcount++;
            } else {
                if (switchcount == 0 && dir == 'asc') {
                    dir = 'desc';
                    switching = true;
                }
            }
        }
    };

    // Add sorting functionality to table headers
    document.querySelectorAll('th').forEach((header, index) => {
        header.addEventListener('click', function() {
            sortTable(index);
        });
    });

    // Function to show/hide additional patient info
    const togglePatientInfo = (button, patientId) => {
        const infoDiv = document.getElementById(`patientInfo-${patientId}`);
        if (infoDiv.style.display === 'none') {
            infoDiv.style.display = 'block';
            button.textContent = 'Hide Details';
        } else {
            infoDiv.style.display = 'none';
            button.textContent = 'Show Details';
        }
    };

    // Add event listeners to toggle patient info buttons
    document.querySelectorAll('.toggle-info').forEach(button => {
        button.addEventListener('click', function() {
            const patientId = this.getAttribute('data-patient-id');
            togglePatientInfo(this, patientId);
        });
    });
});