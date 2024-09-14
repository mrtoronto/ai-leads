import { socket } from "./socket.js";

$(document).ready(function () {

    let justRewritten = false;

    $('#rewriteQueryBtn').on('click', function () {
        if (!window.is_auth) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'You must be logged in to use this feature!',
                showConfirmButton: true,
                confirmButtonText: 'OK',
                confirmButtonColor: '#3E8CFF'
            });
            return;
        }

        const query = $('#query').val();
        const location = $('#location').val();
        // const exampleLeads = $('#exampleLeads').val().split(',');
        const autoCheck = $('#autoCheck').is(':checked');
        const autoHide = $('#autoHide').is(':checked');
        const budget = $('#budget').val();
        const n_results = $('#n_results').val();

        const button = $('#rewriteQueryBtn');
        const icon = button.find('i');
        icon.removeClass('fa-lightbulb').addClass('fa-spinner fa-spin');
        button.prop('disabled', true);

        const exampleLeads = [];
        $('.example-lead-input').each(function() {
            const value = $(this).val().trim();
            if (value) {
                exampleLeads.push(value);
            }
        });

        socket.emit('rewrite_query', {
            query: query,
            location: location,
            exampleLeads: exampleLeads,
            autoCheck: autoCheck,
            autoHide: autoHide,
            budget: budget,
            n_results: n_results
        });
    });

    // Listen for the new rewritten query
    socket.on('new_rewritten_query', function (data) {
        $('#query').val(data.new_query);
        queryInput.trigger('input');

        const button = $('#rewriteQueryBtn');
        const icon = button.find('i');
        icon.removeClass('fa-spinner fa-spin').addClass('fa-lightbulb');
        button.prop('disabled', false);

        justRewritten = true;
    });

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

    const exampleLeadsContainer = $('#exampleLeadsContainer');
    const addExampleLeadBtn = $('.add-example-lead');

    function addExampleLeadInput() {
        const inputGroup = $('<div class="input-group mb-2"></div>');
        const input = $('<input type="text" class="form-control example-lead-input" placeholder="Enter URL">');
        const removeBtn = $('<button class="btn btn-outline-secondary remove-example-lead" type="button"><i class="fa-solid fa-trash"></i></button>');

        removeBtn.on('click', function() {
            inputGroup.remove();
        });

        inputGroup.append(input, removeBtn);
        exampleLeadsContainer.append(inputGroup);
    }

    addExampleLeadBtn.on('click', addExampleLeadInput);

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
        let new_estimate = 200 + (this.value * 40);
        estimateValue.val(new_estimate + ' Credits');
    });

    budgetInput.on('input', function() {
        budgetOutput.val(this.value == 0 ? 'No Budget' : this.value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') + ' Credits');
    });

    const queryInput = $('.submit-request-form-query-input');
    queryInput.on('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight + 7) + 'px';
    });

    if (document.querySelector('#lead-form')) {
        document.querySelector('#lead-form').addEventListener('submit', function (event) {
            event.preventDefault();
            const query = document.querySelector('#query').value;
            const nResults = document.querySelector('#n_results').value;
            const autoCheck = document.querySelector('#autoCheck').checked;
            const autoHide = document.querySelector('#autoHide').checked;
            const budget = document.querySelector('#budget').value;
            const location = document.querySelector('#location').value;
            const priceEstimate = document.querySelector('#priceEstimate').value;

            const exampleLeads = [];
            $('.example-lead-input').each(function() {
                const value = $(this).val().trim();
                if (value) {
                    exampleLeads.push(value);
                }
            });

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

            if (justRewritten) {
                justRewritten = false;
                Swal.fire({
                    icon: 'success',
                    title: 'Success',
                    text: data.message,
                    showConfirmButton: true,
                    allowOutsideClick: false,
                    confirmButtonText: 'Go to Query',
                    confirmButtonColor: '#3E8CFF'
                }).then((result) => {
                    submitQueryWithoutCheck(query);
                });
            } else {
                // Show spinner
                Swal.fire({
                    title: 'Validating query...',
                    html: 'Please wait while we check your query.',
                    allowOutsideClick: false,
                    showConfirmButton: false,
                    willOpen: () => {
                        Swal.showLoading();
                    }
                });

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
                        Swal.close();
                        if (data.guid) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Success',
                                text: data.message,
                                showConfirmButton: true,
                                allowOutsideClick: false,
                                confirmButtonText: 'Go to Query',
                                confirmButtonColor: '#3E8CFF'
                            }).then((result) => {
                                if (result.isConfirmed) {
                                    window.location.href = `/query/${data.guid}`;
                                }
                            });
                        } else if (data.alternative_queries) {
                            Swal.fire({
                                icon: 'warning',
                                title: 'Hold up...',
                                html: `
                                    <p>${data.message}</p>
                                    <p>What do you think of these instead?</p>
                                    <p>
                                        <hr>
                                        ${data.alternative_queries.map((q, index) => `<a href="#" class="alternative-query" data-index="${index}"><strong>${q}</strong></a><hr>`).join('')}
                                    </p>
                                    <p>Click on a query to use it, or proceed with your original query below.</p>
                                `,
                                showCancelButton: true,
                                confirmButtonText: 'Proceed with original',
                                cancelButtonText: 'Cancel',
                                confirmButtonColor: '#3E8CFF',
                                cancelButtonColor: '#d33'
                            }).then((result) => {
                                if (result.isConfirmed) {
                                    submitQueryWithoutCheck(query);
                                }
                            });

                            // Add click event listeners to the alternative queries
                            document.querySelectorAll('.alternative-query').forEach(link => {
                                link.addEventListener('click', function(e) {
                                    e.preventDefault();
                                    const selectedQuery = data.alternative_queries[this.dataset.index];
                                    document.querySelector('#query').value = selectedQuery;
                                    Swal.close();
                                    submitQueryWithoutCheck(selectedQuery);
                                });
                            });
                        }
                    }).catch((error) => {
                        console.error('Error:', error);
                        Swal.fire({
                            icon: 'error',
                            title: 'Error',
                            text: 'An error occurred while processing your request.',
                            showConfirmButton: true,
                            confirmButtonText: 'OK',
                            confirmButtonColor: '#3E8CFF'
                        });
                    });
            }
        });
    }
});

// Function to submit the query without rechecking
function submitQuery(queryText) {
    const exampleLeads = [];
    $('.example-lead-input').each(function() {
        const value = $(this).val().trim();
        if (value) {
            exampleLeads.push(value);
        }
    });
    const formData = {
        query: queryText,
        exampleLeads: exampleLeads,
        autoCheck: $('#autoCheck').is(':checked'),
        autoHide: $('#autoHide').is(':checked'),
        budget: $('#budget').val(),
        nResults: $('#n_results').val(),
        location: $('#location').val(),
        priceEstimate: $('#priceEstimate').val(),
    };

    fetch("/submit_request", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    }).then(response => response.json())
    .then(data => {
        if (data.guid) {
            Swal.fire({
                icon: 'success',
                title: 'Query Submitted',
                text: 'Your query has been successfully submitted.',
                showConfirmButton: false,
                timer: 1500
            }).then(() => {
                window.location.href = `/query/${data.guid}`;
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'An error occurred while submitting your query.',
                showConfirmButton: true,
                confirmButtonText: 'OK',
                confirmButtonColor: '#3E8CFF'
            });
        }
    }).catch(error => {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'An error occurred while submitting your query.',
            showConfirmButton: true,
            confirmButtonText: 'OK',
            confirmButtonColor: '#3E8CFF'
        });
    });
}

// New function to submit the query without validation
function submitQueryWithoutCheck(queryText) {
    const exampleLeads = [];
    $('.example-lead-input').each(function() {
        const value = $(this).val().trim();
        if (value) {
            exampleLeads.push(value);
        }
    });
    const formData = {
        query: queryText,
        exampleLeads: exampleLeads,
        autoCheck: $('#autoCheck').is(':checked'),
        autoHide: $('#autoHide').is(':checked'),
        budget: $('#budget').val(),
        nResults: $('#n_results').val(),
        location: $('#location').val(),
        priceEstimate: $('#priceEstimate').val(),
        skip_validation: true
    };

    fetch("/submit_request", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    }).then(response => response.json())
    .then(data => {
        if (data.guid) {
            Swal.fire({
                icon: 'success',
                title: 'Success',
                text: data.message,
                showConfirmButton: true,
                allowOutsideClick: false,
                confirmButtonText: 'Go to Query',
                confirmButtonColor: '#3E8CFF'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = `/query/${data.guid}`;
                }
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'An error occurred while submitting your query.',
                showConfirmButton: true,
                confirmButtonText: 'OK',
                confirmButtonColor: '#3E8CFF'
            });
        }
    }).catch(error => {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'An error occurred while submitting your query.',
            showConfirmButton: true,
            confirmButtonText: 'OK',
            confirmButtonColor: '#3E8CFF'
        });
    });
}
