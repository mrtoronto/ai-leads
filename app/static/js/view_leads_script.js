import { socket } from "./socket.js";
import {
    dataCache,
    initializeSearches,
    initializeClicks,
    getLeadTableColumns,
    createTable,
    initializeSelectAll
} from "./general_script.js";

import { createTableComponent } from "./components.js";

import { handleLeadEvents } from "./socket_handlers.js";

document.addEventListener('DOMContentLoaded', function() {
    const fetchData = () => {
        return new Promise(resolve => {
            socket.once('initial_data', data => {
                dataCache.leads = data.leads.reduce((acc, lead) => ({ ...acc, [lead.id]: lead }), {});
                resolve(data.leads);
            });
            socket.emit('get_initial_data');
        });
    };

    document.getElementById('all-leads-table-container').innerHTML = createTableComponent(
        'All Leads', 'all-leads-table', 'all-leads-search', 'all-leads-table-select-all', 'all-leads-table-dropdown',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('hidden-leads-table-container').innerHTML = createTableComponent(
        'Hidden Leads', 'hidden-leads-table', 'hidden-leads-search', 'hidden-leads-table-select-all', 'hidden-leads-table-dropdown',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('checked-leads-table-container').innerHTML = createTableComponent(
        'Checked Leads', 'checked-leads-table', 'checked-leads-search', 'checked-leads-table-select-all', 'checked-leads-table-dropdown',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('unchecked-leads-table-container').innerHTML = createTableComponent(
        'Unchecked Leads', 'unchecked-leads-table', 'unchecked-leads-search', 'unchecked-leads-table-select-all', 'unchecked-leads-table-dropdown',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );

    // Initialize tables
    fetchData().then(leads => {
        createTable('all-leads-table', getLeadTableColumns(), leads);
        createTable('hidden-leads-table', getLeadTableColumns(), leads.filter(lead => lead.hidden), true);
        createTable('checked-leads-table', getLeadTableColumns(), leads.filter(lead => !lead.checking && lead.checked));
        createTable('unchecked-leads-table', getLeadTableColumns(), leads.filter(lead => !lead.checking && !lead.checked));
		    initializeSearches();
		    initializeClicks();
		    initializeSelectAll(['all-leads', 'hidden-leads', 'checked-leads', 'unchecked-leads']);
    });
    handleLeadEvents('all-leads-table-container');
    handleLeadEvents('hidden-leads-table-container');
    handleLeadEvents('checked-leads-table-container');
    handleLeadEvents('unchecked-leads-table-container');

});
