import { socket } from "./socket.js";
import {
    dataCache,
    initializeSearches,
    initializeClicks,
    getQueryTableColumns,
    createTable,
    initializeSelectAll
} from "./general_script.js";

import { createTableComponent } from "./components.js";

import { handleRequestEvents, handleLeadEvents, handleSourceEvents } from "./socket_handlers.js";

document.addEventListener('DOMContentLoaded', function() {
    const fetchData = () => {
        return new Promise(resolve => {
            socket.once('initial_data', data => {
                dataCache.requests = data.requests.reduce((acc, request) => ({ ...acc, [request.id]: request }), {});
                resolve(data.requests);
            });
            socket.emit('get_initial_data', { 'get_leads': false, 'get_lead_sources': false });
        });
    };

    document.getElementById('all-queries-table-container').innerHTML = createTableComponent(
        'All Queries', 'all-queries',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('running-queries-table-container').innerHTML = createTableComponent(
        'Running Queries', 'running-queries',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );

    // Initialize tables
    fetchData().then(requests => {
        createTable('all-queries-table', getQueryTableColumns(), requests);
        createTable('running-queries-table', getQueryTableColumns(), requests.filter(request => !request.finished));

  		  initializeClicks();
		    initializeSearches(['all-queries', 'running-queries']);
		    initializeSelectAll(['all-queries', 'running-queries']);
				handleLeadEvents();
     		handleSourceEvents();
       	handleRequestEvents();
    });
});
