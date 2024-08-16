document.addEventListener('DOMContentLoaded', function() {
    console.log('Clinic Management System loaded');

    const confirmDelete = (event) => {
        if (!confirm('Are you sure you want to delete this patient?')) {
            event.preventDefault();
        }
    };

    document.querySelectorAll('.delete-patient').forEach(button => {
        button.addEventListener('click', confirmDelete);
    });

    const validateForm = (form) => {
        let isValid = true;
        form.querySelectorAll('input, select, textarea').forEach(input => {
            if (input.hasAttribute('required') && !input.value.trim()) {
                isValid = false;
                input.classList.add('border-red-500');
            } else {
                input.classList.remove('border-red-500');
            }
        });
        return isValid;
    };

    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(this)) {
                event.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });

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

    const imageInput = document.getElementById('image');
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            previewImage(this);
        });
    }

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

    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            filterTable(this);
        });
    }

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

    document.querySelectorAll('th').forEach((header, index) => {
        header.addEventListener('click', function() {
            sortTable(index);
        });
    });
});
