import { socket, fetchData } from "./socket.js";
import { createTable, updateCounts, getLeadTableColumns, initializeClicks, initializeSearches, initializeSelectAll } from "./general_script.js";
import { createSourceDetailsComponent, createTableComponent, initializeLikeButtons } from "./components.js";
import { handleLeadEvents, handleSourceEvents } from "./socket_handlers.js";


document.addEventListener('DOMContentLoaded', function() {
    const sourceId = document.getElementById('source-id').value;

    document.getElementById('source-leads-table-container').innerHTML = createTableComponent(
        'Leads from Source', 'source-leads',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );

    fetchData({'source_id': sourceId}).then(data => {
        const container = document.querySelector('.source-container');
        container.innerHTML = '';

        container.innerHTML += createSourceDetailsComponent(data.source);

        createTable('source-leads-table', getLeadTableColumns(), data.leads.filter(lead => !lead.hidden));

		    initializeClicks();
		    initializeSearches(['source-leads']);
		    initializeSelectAll(['source-leads']);

				updateCounts();
    });

    handleLeadEvents('source-leads', sourceId);
});
