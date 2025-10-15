document.addEventListener('DOMContentLoaded', () => {
    const bankForm = document.getElementById('bank-form');
    const bankInputsContainer = document.getElementById('bank-inputs');
    const addRowBtn = document.getElementById('add-row-btn');
    const resultsContainer = document.getElementById('results');
    const resultsTableBody = document.getElementById('results-table-body');
    const showPointsBtn = document.getElementById('show-points-btn');
    const pointsHeader = document.getElementById('points-header');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessage = document.getElementById('error-message');
    const bankRowTemplate = document.getElementById('bank-row-template');

    // Global bank count variable, initialized by the number of existing rows.
    let bankCount = document.querySelectorAll('.input-row').length;

    // List of field names used in the template (for re-indexing)
    const fieldNames = ['bank-name', 'kppm', 'ab', 'apb', 'ckpn', 'npl-gross', 'npl-net', 'roa', 'roe', 'nim', 'bopo', 'cir', 'ldr'];

    /**
     * Re-indexes all bank input rows, updating the Bank # heading, 
     * and ensuring input and label IDs are uniquely associated (e.g., bank-name-1, bank-name-2).
     */
    const reindexBanks = () => {
        const bankRows = document.querySelectorAll('#bank-inputs .input-row');
        bankRows.forEach((row, index) => {
            const newIndex = index + 1; // 1-based index for display and IDs

            // 1. Update Heading Text
            const heading = row.querySelector('.bank-heading');
            if (heading) {
                heading.textContent = `Bank #${newIndex}`;
            }

            // 2. Update Input and Label IDs
            fieldNames.forEach(name => {
                // Find input by its name attribute (which stays constant)
                const input = row.querySelector(`[name="${name}"]`);
                // Find the corresponding label using the 'for' attribute, which starts with the field name
                const label = row.querySelector(`label[for^="${name}"]`);

                if (input) {
                    const newId = `${name}-${newIndex}`;
                    input.id = newId;
                }
                if (label) {
                    const newId = `${name}-${newIndex}`;
                    label.htmlFor = newId;
                }
            });
        });
        // Update the global bank count to reflect the current number of rows
        bankCount = bankRows.length;
    };

    // Function to add a new row for bank input using the template
    const addBankRow = () => {
        const newRow = bankRowTemplate.content.cloneNode(true);
        const newRowDiv = newRow.querySelector('.input-row');

        // Append the new row before re-indexing
        bankInputsContainer.appendChild(newRowDiv);

        // Re-index all banks to correctly number the new row and ensure unique IDs
        reindexBanks();
    };

    // Event listener for the "Add Another Bank" button
    addRowBtn.addEventListener('click', addBankRow);

    // New: Event delegation for the "Delete Bank" button
    bankInputsContainer.addEventListener('click', (e) => {
        const deleteBtn = e.target.closest('.delete-row-btn');
        if (deleteBtn) {
            const rowToRemove = deleteBtn.closest('.input-row');
            const currentBankRows = document.querySelectorAll('#bank-inputs .input-row');

            // Prevent deleting the very first bank row (must always have at least one)
            if (currentBankRows.length <= 1) {
                errorMessage.textContent = "You must have at least one bank to analyze.";
                errorMessage.classList.remove('hidden');
                return;
            } else {
                errorMessage.classList.add('hidden');
            }

            if (rowToRemove) {
                rowToRemove.remove();
                reindexBanks(); // Update the numbering and IDs of remaining rows
            }
        }
    });

    // Event listener for form submission (Calculate)
    bankForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Clear previous results and errors
        resultsTableBody.innerHTML = '';
        resultsContainer.classList.remove('visible');
        showPointsBtn.classList.add('hidden');
        pointsHeader.classList.add('hidden');
        errorMessage.classList.add('hidden');
        loadingIndicator.classList.remove('hidden');

        // Collect all bank data from the form
        const bankRows = document.querySelectorAll('.input-row');
        const banksData = [];
        bankRows.forEach(row => {
            const inputs = row.querySelectorAll('input');
            const bank = {};
            let allInputsFilled = true;
            inputs.forEach(input => {
                // Only collect inputs that have a name
                if (input.name) {
                    bank[input.name] = input.value;
                    if (input.required && !input.value) {
                        allInputsFilled = false;
                    }
                }
            });
            if (allInputsFilled) {
                banksData.push(bank);
            }
        });

        if (banksData.length === 0) {
            loadingIndicator.classList.add('hidden');
            errorMessage.textContent = 'Please enter data for at least one bank.';
            errorMessage.classList.remove('hidden');
            return;
        }

        try {
            // Send data to the Flask backend
            const response = await fetch('http://127.0.0.1:5000/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(banksData),
            });

            loadingIndicator.classList.add('hidden');

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Something went wrong.');
            }

            const rankedBanks = await response.json();

            // Display the results in the table
            rankedBanks.forEach(bank => {
                const row = document.createElement('tr');
                row.className = 'bg-white hover:bg-gray-50';
                row.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${bank.rank}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${bank.name}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${bank.ldr} %</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 points-cell" data-points="${bank.total_points}" style="display: none;"></td>
                `;
                resultsTableBody.appendChild(row);
            });

            // Show results section and the "Show Points" button
            resultsContainer.classList.add('visible');
            showPointsBtn.classList.remove('hidden');

        } catch (error) {
            loadingIndicator.classList.add('hidden');
            errorMessage.textContent = `Error: ${error.message}`;
            errorMessage.classList.remove('hidden');
        }
    });

    // Event listener for the "Show Points" button
    showPointsBtn.addEventListener('click', () => {
        const pointsCells = document.querySelectorAll('.points-cell');
        const isHidden = pointsCells[0].style.display === 'none';

        pointsCells.forEach(cell => {
            if (isHidden) {
                cell.textContent = cell.getAttribute('data-points');
                cell.style.display = '';
            } else {
                cell.style.display = 'none';
            }
        });

        if (isHidden) {
            pointsHeader.classList.remove('hidden');
            showPointsBtn.textContent = 'Hide Points';
        } else {
            pointsHeader.classList.add('hidden');
            showPointsBtn.textContent = 'Show Points';
        }
    });

    // Initial re-indexing to ensure all existing elements (especially Bank #1) are properly marked.
    reindexBanks();
});
