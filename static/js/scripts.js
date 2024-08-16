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
    // Add sorting functionality to table headers
    document.querySelectorAll('th').forEach((header, index) => {
        header.addEventListener('click', function() {
            sortTable(index);
        });
    });

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

    // Function to handle pagination
    const paginate = (items, itemsPerPage, currentPage) => {
        const startIndex = (currentPage - 1) * itemsPerPage;
        return items.slice(startIndex, startIndex + itemsPerPage);
    };

    // Add pagination to patient table
    const patientsTable = document.getElementById('patientsTable');
    if (patientsTable) {
        const itemsPerPage = 10;
        const rows = Array.from(patientsTable.querySelectorAll('tbody tr'));
        const pageCount = Math.ceil(rows.length / itemsPerPage);
        let currentPage = 1;

        const updateTable = () => {
            const paginatedRows = paginate(rows, itemsPerPage, currentPage);
            patientsTable.querySelector('tbody').innerHTML = '';
            paginatedRows.forEach(row => patientsTable.querySelector('tbody').appendChild(row));
        };

        const createPagination = () => {
            const pagination = document.createElement('nav');
            pagination.innerHTML = `
                <ul class="pagination justify-content-center">
                    <li class="page-item"><a class="page-link" href="#" id="prevPage">Previous</a></li>
                    <li class="page-item"><a class="page-link" href="#" id="nextPage">Next</a></li>
                </ul>
            `;
            patientsTable.parentNode.insertBefore(pagination, patientsTable.nextSibling);

            document.getElementById('prevPage').addEventListener('click', (e) => {
                e.preventDefault();
                if (currentPage > 1) {
                    currentPage--;
                    updateTable();
                }
            });

            document.getElementById('nextPage').addEventListener('click', (e) => {
                e.preventDefault();
                if (currentPage < pageCount) {
                    currentPage++;
                    updateTable();
                }
            });
        };

        updateTable();
        createPagination();
    }

    // Function to create charts for patient data
    const createCharts = () => {
        const ctx = document.getElementById('heartRateChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: heartRateDates,
                    datasets: [{
                        label: 'Heart Rate',
                        data: heartRates,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    };

    // Call createCharts if the chart container exists
    if (document.getElementById('heartRateChart')) {
        createCharts();
    }
});