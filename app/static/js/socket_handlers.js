import { socket } from "./socket.js";
import { updateRow, addRow, updateCounts, handleHideEvent } from "./general_script.js";


// Request-related events
function handleRequestEvents(tableId='requests') {
		tableId = tableId + '-table';
		console.log('tableId:', tableId);
    socket.on('requests_updated', async data => { for (const request of data.queries) { updateRow(tableId, request) } });
}

// Source-related events
function handleSourceEvents(tableId='sources') {
		tableId = tableId + '-table';
    socket.on('sources_updated', async data => { for (const source of data.sources) { updateRow(tableId, source); } });
}

// Lead-related events
function handleLeadEvents(tableId='leads') {
		tableId = tableId + '-table';
    socket.on('leads_updated', async data => { for (const lead of data.leads) { updateRow(tableId, lead); } });
}

export { handleRequestEvents, handleSourceEvents, handleLeadEvents };
