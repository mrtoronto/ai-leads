$(document).ready(function () {
		const advancedOptionsContainer = $('#advancedOptionsContainer');
    const showAdvancedOptionsBtn = $('.showAdvancedOptionsBtn');
    const autoCheckCheckbox = $('#autoCheck');
    const autoHideCheckbox = $('#autoHide');
    const budgetInput = $('#budget');
    const nResultsInput = $('#n_results');
    const nResultsOutput = $('#nResultsOutput');
    const budgetValue = $('#budget');
    const budgetOutput = $('#budgetOutput');
    const estimateValue = $('#priceEstimate');

    showAdvancedOptionsBtn.on('click', function() {
        advancedOptionsContainer.toggle();
    });

    autoCheckCheckbox.on('change', function() {
        if (!this.checked) {
					budgetInput.val(0);
					budgetOutput.val('No Budget');
        }
        budgetInput.prop('disabled', !this.checked);
        autoHideCheckbox.prop('disabled', !this.checked);
    });

    // New event listeners for n_results and budget inputs
    nResultsInput.on('input', function() {
        nResultsOutput.val(this.value == '1' ? this.value + ' Result' : this.value + ' Results');
        let new_estimate = 200 + (this.value * 75);
        estimateValue.val(new_estimate + ' Credits');
    });

    budgetInput.on('input', function() {
        budgetOutput.val(this.value == 0 ? 'No Budget' : this.value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') + ' Credits');
    });

    if (document.querySelector('#lead-form')) {
        document.querySelector('#lead-form').addEventListener('submit', function (event) {
            event.preventDefault();
            const query = document.querySelector('#query').value;
            const nResults = document.querySelector('#n_results').value;
            const exampleLeads = document.querySelector('#exampleLeads').value;
            const autoCheck = document.querySelector('#autoCheck').checked;
            const autoHide = document.querySelector('#autoHide').checked;
            const budget = document.querySelector('#budget').value;
            const location = document.querySelector('#location').value;
            const priceEstimate = document.querySelector('#priceEstimate').value;

            if (!window.is_auth) {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'You must be logged in to submit a request!',
                    showConfirmButton: true,
                    confirmButtonText: 'OK',
                    confirmButtonColor: '#3E8CFF'
                });
                return;

            }

            if ((query === '') || (query === null) || (query === undefined) || (query.trim() === '')) {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Enter a query to search for!',
                    showConfirmButton: true,
                    confirmButtonText: 'OK',
                    confirmButtonColor: '#3E8CFF'
                });
                return;
            }

            fetch("/submit_request", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    exampleLeads: exampleLeads,
                    autoCheck: autoCheck,
                    autoHide: autoHide,
                    budget: budget,
                    nResults: nResults,
                    location: location,
                    priceEstimate: priceEstimate
                })
            }).then(response => response.json())
                .then(data => {
                    if (data.message) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Success',
                            text: data.message,
                            showConfirmButton: true,
                            confirmButtonText: 'Go to Query',
                            confirmButtonColor: '#3E8CFF'
                        }).then((result) => {
                            if (result.isConfirmed) {
                                window.location.href = `/query/${data.guid}`;
                            }
                        });
                    }
                }).catch((error) => {
                    console.error('Error:', error);
                });
        });
    }
});
