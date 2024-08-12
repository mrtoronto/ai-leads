import { socket } from "./socket.js";
import { searchTable, updateRow, addRow, createAllTables, initializeClicks, initializeSearches } from "./general_script.js";
import { createSourceDetailsComponent, createTableComponent, initializeLikeButtons } from "./components.js";
import { handleLeadEvents, handleSourceEvents } from "./socket_handlers.js";


document.addEventListener('DOMContentLoaded', function() {
    const sourceId = document.getElementById('source-id').value;
    socket.emit('get_source_data', { source_id: sourceId });

    socket.on('source_data', function(data) {
        const container = document.querySelector('.container');
        container.innerHTML = '';

        container.innerHTML += createSourceDetailsComponent(data.source);
        container.innerHTML += createTableComponent("Associated Leads", "leads-table", "leads-search");

        createAllTables({
            leads: data.leads
        });

        initializeClicks();
        initializeSearches();

        handleLeadEvents();
    });

    socket.on('leads_hidden', async data => { for (const id of data.lead_ids) {handleHideEvent('leads-table', id);} });
    socket.on('lead_check_started', async (data) => updateRow('leads-table', data.lead.id, data));
    socket.on('lead_checked', async (data) => updateRow('leads-table', data.lead.id, data.lead));
    socket.on('new_lead', async (data) => addRow('leads-table', data.lead));
});
