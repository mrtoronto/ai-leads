import { socket } from "./socket.js";
import {
	dataCache,
	initializeSearches,
	initializeClicks,
	searchTable,
	sortTable,
	updateCounts,
	createTable,
	updateRow,
	addRow,
	handleHideEvent,
	initializeSelectAll
} from "./general_script.js";

import { getLeadTableColumns, getLikedLeadTableColumns, getQueryTableColumns, getSourceTableColumns } from "./make_table_columns.js"

import { createTableComponent } from "./components.js";

import { handleLeadEvents, handleSourceEvents, handleRequestEvents } from "./socket_handlers.js";

document.addEventListener('DOMContentLoaded', function() {
		console.log(window.is_mobile);
		const fetchData = () => {
        return new Promise(resolve => {
            socket.once('initial_data', data => {
            		// check if data is an empty object
              	if (Object.keys(data).length === 0) {
                        if (!window.is_auth) {
                            return;
                        }
               	}

                dataCache.requests = data.requests.reduce((acc, request) => ({ ...acc, [request.id]: request }), {});
                dataCache.sources = data.lead_sources.reduce((acc, source) => ({ ...acc, [source.id]: source }), {});
                dataCache.leads = data.leads.reduce((acc, lead) => ({ ...acc, [lead.id]: lead }), {});
                dataCache.likedLeads = data.leads.filter(lead => lead.liked);
                console.log(data);
                $('.count-spinner').remove();
                $('#liked-leads-count').text(data.n_liked);
                $('#hidden-leads-count').text(data.n_hidden);

                if ((data.n_liked > 50) && (data.n_hidden > 50)) {
                		$('#retrain-model-btn').prop('disabled', false);
                }
                resolve(data);
            });
            socket.emit('get_initial_data');
        });
    };

		document.getElementById('queries-table-container').innerHTML = createTableComponent(
        'Queries', 'requests', ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('lead-sources-table-container').innerHTML = createTableComponent(
        'Lead Sources', 'sources',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('leads-table-container').innerHTML = createTableComponent(
        'Leads', 'leads',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('liked-leads-table-container').innerHTML = createTableComponent(
        'Liked Leads', 'liked-leads',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid', 'check-all', 'hide-all', 'export-csv']
    );

    // Initialize tables
    fetchData().then(data => {
        createTable('requests-table', getQueryTableColumns(), data.requests);
        createTable('sources-table', getSourceTableColumns(), data.lead_sources);
        createTable('leads-table', getLeadTableColumns(), data.leads);
        createTable('liked-leads-table', getLikedLeadTableColumns(), data.leads.filter(lead => lead.liked));
        updateCounts();
    });

    document.getElementById('retrain-model-btn').addEventListener('click', function() {
      // can you make the button disabled and a spinner
      $('#retrain-model-btn').prop('disabled', true);
      $('#retrain-model-btn').html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Retraining...');
    	socket.emit('retrain_model');
    });

    socket.on('credit_error', function (data) {
			let toast_class;
    	if (data.lead) {
				updateRow('leads-table', data.lead.id, data.lead);
				toast_class = 'credit-lead-error-toast';
			} else if (data.source) {

				updateRow('sources-table', data.source.id, data.source);
				toast_class = 'credit-source-error-toast';
			} else if (data.request) {
				updateRow('requests-table', data.request.id, data.request);
				toast_class = 'credit-request-error-toast';
			}

    	if ($(`.${toast_class}`).length == 0) {
				iziToast.warning({
	        title: 'Warning',
	        message: data.message,
	        class: toast_class,
	        position: 'topRight',
	        timeout: 10000
	      });
			}

    });

    socket.on('model_retrained', function(data) {
        $('#retrain-model-btn').prop('disabled', false);
        $('#retrain-model-btn').html('Retrain Model');
        if (data.trained_at) {
            $('#last-trained-time').text(`Last trained: ${new Date(data.trained_at).toLocaleString()}`);
        }
    });

    // Add event listeners for forms and buttons
    // document.getElementById('create-lead-source-form').addEventListener('submit', function(event) {
    //     event.preventDefault();
    //     const url = document.getElementById('lead-source-url').value;
    //     socket.emit('create_lead_source', { url });
    //     document.getElementById('lead-source-url').value = '';
    // });

    // Toggle Lead Source Form
    // document.getElementById('toggle-lead-source-form').addEventListener('click', function() {
    //     const formContainer = document.getElementById('lead-source-form-container');
    //     formContainer.style.display = (formContainer.style.display === 'none' || formContainer.style.display === '') ? 'block' : 'none';
    // });

    // document.getElementById('toggle-lead-form').addEventListener('click', function() {
    //     const formContainer = document.getElementById('lead-form-container');
    //     formContainer.style.display = (formContainer.style.display === 'none' || formContainer.style.display === '') ? 'block' : 'none';
    // });

    // document.getElementById('create-lead-form').addEventListener('submit', function(event) {
    //     event.preventDefault();
    //     const url = document.getElementById('lead-url').value;
    //     socket.emit('create_lead', { url });
    //     document.getElementById('lead-url').value = '';
    // });


    // document.querySelector('#lead-form').addEventListener('submit', function (event) {
    //     event.preventDefault();
    //     const query = document.querySelector('#query').value;

    //     document.querySelector('.submit-request-btn').disabled = true;

    //     fetch("/submit_request", {
    //         method: 'POST',
    //         headers: {
    //             'Content-Type': 'application/json'
    //         },
    //         body: JSON.stringify({ query: query })
    //     }).then(response => response.json())
    //       .then(data => {
    //           if (data.message) {
    //             iziToast.success({ title: 'Success', message: data.message });
    //           }
    //       }).catch((error) => {
    //           console.error('Error:', error);
    //       });
    // });

    initializeSearches();
    initializeClicks();

    // Bind socket events
    handleLeadEvents();
    handleSourceEvents();
    handleRequestEvents();

    initializeSelectAll();

});
