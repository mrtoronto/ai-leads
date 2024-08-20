import { socket, fetchData } from "./socket.js";
import {
    dataCache,
    initializeSearches,
    initializeClicks,
    getQueryTableColumns,
    createTable,
    updateCounts,
    initializeSelectAll
} from "./general_script.js";

import { createTableComponent } from "./components.js";

import { handleRequestEvents, handleLeadEvents, handleSourceEvents } from "./socket_handlers.js";

document.addEventListener('DOMContentLoaded', function() {

    document.getElementById('all-queries-table-container').innerHTML = createTableComponent(
        'All Queries', 'all-queries',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('running-queries-table-container').innerHTML = createTableComponent(
        'Running Queries', 'running-queries',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );

    document.getElementById('hidden-queries-table-container').innerHTML = createTableComponent(
        'Hidden Queries', 'hidden-queries',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'unhide-all', 'export-csv']
    );

    // Initialize tables
    fetchData({'get_leads':false, 'get_lead_sources': false, 'get_hidden_queries':true}).then(data => {
    		const requests = data.requests;
        createTable('all-queries-table', getQueryTableColumns(), requests.filter(request => !request.hidden));
        createTable('running-queries-table', getQueryTableColumns(), requests.filter(request => !request.finished && !request.hidden));
        createTable('hidden-queries-table', getQueryTableColumns(), requests.filter(request => request.hidden));

  		  initializeClicks();
		    initializeSearches(['all-queries', 'running-queries', 'hidden-queries']);
		    initializeSelectAll(['all-queries', 'running-queries', 'hidden-queries']);

				updateCounts();
    });
   	handleRequestEvents('all-queries');
   	handleRequestEvents('running-queries');
   	handleRequestEvents('hidden-queries');
});
