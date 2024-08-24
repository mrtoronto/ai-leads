import { socket } from "./socket.js";
import {
    dataCache,
    getSourceTableColumns,
    updateCounts,
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
                dataCache.requests = data.requests.reduce((acc, request) => ({ ...acc, [request.id]: request }), {});
                dataCache.sources = data.lead_sources.reduce((acc, source) => ({ ...acc, [source.id]: source }), {});
                dataCache.leads = data.leads.reduce((acc, lead) => ({ ...acc, [lead.id]: lead }), {});
                resolve(data);
            });
            socket.emit('get_initial_data', { 'get_in_progress': true });
        });
    };

    document.getElementById('checking-queries-table-container').innerHTML = createTableComponent(
        'Queries (in-progress)', 'checking-queries',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid', '', 'check-all', 'hide-all', 'export-csv']
    );

    document.getElementById('checking-lead-sources-table-container').innerHTML = createTableComponent(
        'Lead Sources (in-progress)', 'checking-lead-sources',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );
    document.getElementById('checking-leads-table-container').innerHTML = createTableComponent(
        'Leads (in-progress)', 'checking-leads',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );

    fetchData({'get_in_progress':true, 'get_requests': true, 'get_sources': true, 'get_leads': true}).then(data => {
    		console.log(data);
        const queries_unfinished = data.requests.filter(query => !query.finished);
        const lead_sources_checking = data.lead_sources.filter(source => source.checking && !source.hidden);
        const leads_checking = data.leads.filter(lead => lead.checking && !lead.hidden);

        createTable('checking-queries-table', getQueryTableColumns(), queries_unfinished);
        createTable('checking-lead-sources-table', getSourceTableColumns(), lead_sources_checking);
        createTable('checking-leads-table', getLeadTableColumns(), leads_checking);

        initializeClicks();
		    initializeSearches(['checking-queries', 'checking-lead-sources', 'checking-leads']);
				initializeSelectAll(['checking-queries', 'checking-lead-sources', 'checking-leads']);

				updateCounts();
    });
		handleLeadEvents('checking-leads');
   	handleSourceEvents('checking-lead-sources');
   	handleRequestEvents('checking-queries');


});
