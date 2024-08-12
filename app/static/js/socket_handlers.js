import { socket } from "./socket.js";
import { updateRow, addRow, updateCounts, handleHideEvent } from "./general_script.js";


// Request-related events
function handleRequestEvents() {
    socket.on('requests_hidden', async data => { for (const id of data.query_ids) { handleHideEvent('requests-table', id); } });
    socket.on('new_request', async (data) => addRow('requests-table', data.request));
    socket.on('request_checked', async (data) => updateRow('requests-table', data.request.id, data.request));
}

// Source-related events
function handleSourceEvents() {
    socket.on('sources_hidden', async data => { for (const id of data.source_ids) { handleHideEvent('sources-table', id); } });
    socket.on('lead_source_check_started', async (data) => updateRow('sources-table', data.source.id, data.source));
    socket.on('new_lead_source', async (data) => addRow('sources-table', data.source));
    socket.on('source_checked', async (data) => updateRow('sources-table', data.source.id, data.source));
}

// Lead-related events
function handleLeadEvents() {
    socket.on('leads_hidden', async data => {
    	for (const id of data.lead_ids) {
     		handleHideEvent('leads-table', id);
       	if ($('#hidden-leads-count').length > 0) {
           let currentCount = parseInt($('#hidden-leads-count').text()) || 0;
           let newCount = currentCount + 1;
           $('#hidden-leads-count').text(newCount);
        }
     	}
    });
    socket.on('lead_check_started', async (data) => updateRow('leads-table', data.lead.id, data.lead));
    socket.on('lead_checked', async (data) => updateRow('leads-table', data.lead.id, data.lead));
    socket.on('new_lead', async (data) => addRow('leads-table', data.lead));
    socket.on('lead_liked', async (data) => {
        updateRow('leads-table', data.lead.id, data.lead);
        if (data.lead.liked) {
            updateRow('liked-leads-table', data.lead.id, data.lead);
        }
        updateCounts();

        if ($('#liked-leads-count').length > 0) {
	        let currentCount = parseInt($('#liked-leads-count').text()) || 0;
	        let newCount = data.lead.liked ? currentCount + 1 : currentCount - 1;
	        $('#liked-leads-count').text(newCount);
        }
    });
}

export { handleRequestEvents, handleSourceEvents, handleLeadEvents };
