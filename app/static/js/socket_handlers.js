import { socket } from "./socket.js";
import { updateRow, addRow, updateCounts, handleHideEvent } from "./general_script.js";


// Request-related events
function handleRequestEvents(tableId='requests-table') {
    socket.on('requests_hidden', async data => { for (const id of data.query_ids) { handleHideEvent(tableId, id); } });
    socket.on('new_request', async (data) => addRow(tableId, data.request));
    socket.on('request_checked', async (data) => updateRow(tableId, data.request.id, data.request));
}

// Source-related events
function handleSourceEvents(tableId='sources-table') {
    socket.on('sources_hidden', async data => { for (const id of data.source_ids) { handleHideEvent(tableId, id); } });
    socket.on('lead_source_check_started', async (data) => updateRow(tableId, data.source.id, data.source));
    socket.on('new_lead_source', async (data) => addRow(tableId, data.source));
    socket.on('source_checked', async (data) => updateRow(tableId, data.source.id, data.source));
}

// Lead-related events
function handleLeadEvents(tableId='leads-table') {
    socket.on('leads_hidden', async data => {
    	for (const id of data.lead_ids) {
     		handleHideEvent(tableId, id);
       	if ($('#hidden-leads-count').length > 0) {
           let currentCount = parseInt($('#hidden-leads-count').text()) || 0;
           let newCount = currentCount + 1;
           $('#hidden-leads-count').text(newCount);
        }
     	}
    });
    socket.on('lead_check_started', async (data) => updateRow(tableId, data.lead.id, data.lead));
    socket.on('lead_checked', async (data) => updateRow(tableId, data.lead.id, data.lead));
    socket.on('new_lead', async (data) => addRow(tableId, data.lead));
    socket.on('lead_liked', async (data) => {
        updateRow(tableId, data.lead.id, data.lead);
        updateCounts();

        if ($('#liked-leads-count').length > 0) {
	        let currentCount = parseInt($('#liked-leads-count').text()) || 0;
	        let newCount = data.lead.liked ? currentCount + 1 : currentCount - 1;
	        $('#liked-leads-count').text(newCount);
        }
    });
}

export { handleRequestEvents, handleSourceEvents, handleLeadEvents };
