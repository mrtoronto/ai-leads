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
            socket.emit('get_initial_data');
        });
    };

    document.getElementById('all-queries-table-container').innerHTML = createTableComponent(
        'All Queries', 'all-queries-table', 'all-queries-search', 'all-queries-table-select-all', 'all-queries-table-dropdown',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('running-queries-table-container').innerHTML = createTableComponent(
        'Running Queries', 'running-queries-table', 'running-queries-search', 'running-queries-table-select-all', 'running-queries-table-dropdown',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );

    // Initialize tables
    fetchData().then(requests => {
        createTable('all-queries-table', getQueryTableColumns(), requests);
        createTable('running-queries-table', getQueryTableColumns(), requests.filter(request => !request.finished));

  		  initializeClicks();
		    initializeSearches();
		    initializeSelectAll(['all-queries-table-container', 'running-queries-table-container']);
				handleLeadEvents();
     		handleSourceEvents();
       	handleRequestEvents();
    });
});
