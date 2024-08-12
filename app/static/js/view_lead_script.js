import { socket } from "./socket.js";
import { createLeadDetailsComponent, createSourceDetailsComponent, createQueryDetailsComponent, initializeLikeButtons } from "./components.js";
import { handleLeadEvents } from "./socket_handlers.js";

document.addEventListener('DOMContentLoaded', function() {
    const leadId = document.getElementById('lead-id').value;
    socket.emit('get_lead_data', { lead_id: leadId });

    socket.on('lead_data', function(data) {
        const container = document.querySelector('.container');
        container.innerHTML = '';

        container.innerHTML += createLeadDetailsComponent(data.lead);

        if (data.lead.lead_source) {
            container.innerHTML += createSourceDetailsComponent(data.lead.lead_source);
        }

        if (data.lead.query_obj) {
            container.innerHTML += createQueryDetailsComponent(data.lead.query_obj);
        }
        initializeLikeButtons();
    });
});
