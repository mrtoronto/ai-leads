import { socket } from "./socket.js";
import {
    dataCache,
    initializeSearches,
    updateCounts,
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
            socket.emit('get_initial_data', { 'get_requests': false, 'get_lead_sources': false, 'get_hidden_leads': true });
        });
    };

    document.getElementById('all-leads-table-container').innerHTML = createTableComponent(
        'All Leads', 'all-leads',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('hidden-leads-table-container').innerHTML = createTableComponent(
        'Hidden Leads', 'hidden-leads',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('checked-leads-table-container').innerHTML = createTableComponent(
        'Checked Leads', 'checked-leads',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('unchecked-leads-table-container').innerHTML = createTableComponent(
        'Unchecked Leads', 'unchecked-leads',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );

    // Initialize tables
    fetchData({'get_lead_sources': false, 'get_hidden_leads': true, 'get_requests': false}).then(leads => {
        createTable('all-leads-table', getLeadTableColumns(), leads.filter(lead => !lead.hidden));
        createTable('hidden-leads-table', getLeadTableColumns(), leads.filter(lead => lead.hidden), true);
        createTable('checked-leads-table', getLeadTableColumns(), leads.filter(lead => !lead.checking && lead.checked && !lead.hidden));
        createTable('unchecked-leads-table', getLeadTableColumns(), leads.filter(lead => !lead.checking && !lead.checked && !lead.hidden));
		    initializeSearches(['all-leads', 'hidden-leads', 'checked-leads', 'unchecked-leads']);
		    initializeClicks();
		    initializeSelectAll(['all-leads', 'hidden-leads', 'checked-leads', 'unchecked-leads']);
				updateCounts();
    });
    handleLeadEvents('all-leads');
    handleLeadEvents('hidden-leads');
    handleLeadEvents('checked-leads');
    handleLeadEvents('unchecked-leads');

});
