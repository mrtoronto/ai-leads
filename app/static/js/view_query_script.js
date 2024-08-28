import { socket, fetchData } from "./socket.js";
import {
	createTable,
	initializeClicks,
	initializeSearches,
	initializeSelectAll,
	getLeadTableColumns,
	updateCounts,
	getSourceTableColumns
} from "./general_script.js";
import { handleLeadEvents, handleSourceEvents, handleRequestEvents, handleQueryCardUpdate } from "./socket_handlers.js";
import { createQueryDetailsComponent, createTableComponent } from "./components.js";

document.addEventListener('DOMContentLoaded', function() {
    const queryId = document.getElementById('query-id').value;

    document.getElementById('query-leads-table-container').innerHTML = createTableComponent(
        'Leads from Query', 'query-leads',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );

    document.getElementById('query-sources-table-container').innerHTML = createTableComponent(
        'Sources from Query', 'query-sources',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );

    fetchData({'query_id': queryId}).then(data => {
    		console.log(data);
        const container = document.querySelector('.query-container');
        container.innerHTML = '';
        container.innerHTML += createQueryDetailsComponent(data.query);

        createTable('query-leads-table', getLeadTableColumns(), data.leads.filter(request => !request.hidden));
        createTable('query-sources-table', getSourceTableColumns(), data.lead_sources.filter(request => !request.hidden));

		    initializeClicks();
		    initializeSearches(['query-leads', 'query-sources']);
		    initializeSelectAll(['query-leads', 'query-sources']);
				updateCounts();
    });

    handleQueryCardUpdate('.query-container', queryId);
    handleLeadEvents('query-leads', queryId);
    handleSourceEvents('query-sources', queryId);
});
