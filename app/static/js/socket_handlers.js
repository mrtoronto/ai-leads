import { socket } from "./socket.js";
import { updateRow, addRow, updateCounts, handleHideEvent } from "./general_script.js";

import { createQueryDetailsComponent } from "./components.js";


// Request-related events
function handleRequestEvents(tableId='requests') {
		tableId = tableId + '-table';
    socket.on('queries_updated', async data => { for (const request of data.queries) { updateRow(tableId, request) } });
}

// Source-related events
function handleSourceEvents(tableId='sources', query_id=null) {
		tableId = tableId + '-table';
    socket.on('sources_updated', async data => { for (const source of data.sources) {
    	if (query_id && source.query_id == query_id) {
				updateRow(tableId, source);
			} else if (!query_id) {
    		updateRow(tableId, source);
			}
    } });
}

// Lead-related events
function handleLeadEvents(tableId='leads', query_id=null, source_id=null) {
		tableId = tableId + '-table';
    socket.on('leads_updated', async data => { for (const lead of data.leads) {
    	if ((query_id && lead.query_id == query_id) || (source_id && lead.source_id == source_id)) {
    		updateRow(tableId, lead);
     	} else if (!query_id && !source_id) {
		 		updateRow(tableId, lead);
		 	}
    } });
}

// Modify the handleQueryCardUpdate function
function handleQueryCardUpdate(selector, queryId) {
    socket.on('queries_updated', async data => {
        for (const query of data.queries) {
            if (query.id == queryId) {
                const cardContainer = document.querySelector(selector);
                if (cardContainer) {
                    cardContainer.innerHTML = createQueryDetailsComponent(query);
                }
                break;
            }
        }
    });
}

export { handleRequestEvents, handleSourceEvents, handleLeadEvents, handleQueryCardUpdate };
