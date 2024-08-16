import { socket } from "./socket.js";
import { searchTable, createAllTables, initializeClicks, initializeSearches, initializeSelectAll } from "./general_script.js";
import { handleLeadEvents, handleSourceEvents, handleRequestEvents } from "./socket_handlers.js";
import { createQueryDetailsComponent, createTableComponent } from "./components.js";

document.addEventListener('DOMContentLoaded', function() {
    const queryId = document.getElementById('query-id').value;
    socket.emit('get_query_data', { query_id: queryId });

    socket.on('query_data', function(data) {
        const container = document.querySelector('.container');
        container.innerHTML = '';

        container.innerHTML += createQueryDetailsComponent(data.query);
        // container.innerHTML += createTableComponent("Associated Leads", "leads-table", "leads-search");
        // container.innerHTML += createTableComponent("Associated Sources", "sources-table", "sources-search");
        //
        container.innerHTML += createTableComponent(
              'Leads from Query', 'leads-table', 'leads-search', 'leads-table-select-all', 'leads-table-dropdown',
              ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid', 'check-all', 'hide-all', 'export-csv']
          );
          container.innerHTML += createTableComponent(
              'Sources from Query', 'sources-table', 'sources-search', 'sources-table-select-all', 'sources-table-dropdown',
              ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid', 'check-all', 'hide-all', 'export-csv']
          );

        createAllTables({
            leads: data.leads,
            sources: data.sources
        });


        // Re-add event listeners for search inputs
        document.getElementById('leads-search').addEventListener('input', (e) => searchTable('leads-table', e.target.value));
        document.getElementById('sources-search').addEventListener('input', (e) => searchTable('sources-table', e.target.value));
		    initializeClicks();
		    initializeSearches();
		    initializeSelectAll();
    });




    handleLeadEvents();
    handleSourceEvents();
    handleRequestEvents();
});
