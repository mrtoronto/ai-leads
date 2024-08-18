import { socket } from "./socket.js";
import {
    dataCache,
    getSourceTableColumns,
    getLeadTableColumns,
    createTable,
    getQueryTableColumns,
    initializeClicks,
		initializeSearches,
		initializeSelectAll
} from "./general_script.js";
import { createTableComponent } from "./components.js";

import { handleRequestEvents, handleLeadEvents, handleSourceEvents } from "./socket_handlers.js";

document.addEventListener('DOMContentLoaded', function() {
    const fetchData = () => {
        return new Promise(resolve => {
            socket.once('initial_data', data => {
                dataCache.sources = data.lead_sources.reduce((acc, source) => ({ ...acc, [source.id]: source }), {});
                dataCache.leads = data.leads.reduce((acc, lead) => ({ ...acc, [lead.id]: lead }), {});
                resolve(data);
            });
            socket.emit('get_initial_data');
        });
    };

    document.getElementById('checking-queries-table-container').innerHTML = createTableComponent(
        'Queries (in-progress)', 'checking-queries-table', 'checking-queries-search', 'checking-queries-table-select-all', 'checking-queries-table-dropdown',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid', '', 'check-all', 'hide-all', 'export-csv']
    );

    document.getElementById('checking-lead-sources-table-container').innerHTML = createTableComponent(
        'Lead Sources (in-progress)', 'checking-lead-sources-table', 'checking-lead-sources-search', 'checking-lead-sources-table-select-all', 'checking-lead-sources-table-dropdown',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('checking-leads-table-container').innerHTML = createTableComponent(
        'Leads (in-progress)', 'checking-leads-table', 'checking-leads-search', 'checking-leads-table-select-all', 'checking-leads-table-dropdown',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );

    fetchData().then(data => {
        const queries_unfinished = data.requests.filter(query => !query.finished);
        const lead_sources_checking = data.lead_sources.filter(source => source.checking && !source.hidden);
        const leads_checking = data.leads.filter(lead => lead.checking && !lead.hidden);

        createTable('checking-queries-table', getQueryTableColumns(), queries_unfinished);
        createTable('checking-lead-sources-table', getSourceTableColumns(), lead_sources_checking);
        createTable('checking-leads-table', getLeadTableColumns(), leads_checking);

        initializeClicks();
		    initializeSearches();
				initializeSelectAll(['checking-queries-table-container', 'checking-lead-sources-table-container', 'checking-leads-table-container']);
    });
		handleLeadEvents('checking-leads-table-container');
   	handleSourceEvents('checking-lead-sources-table-container');
   	handleRequestEvents('checking-queries-table-container');


});
