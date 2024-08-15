import { socket } from "./socket.js";

export function createCardComponent(title, content) {
    return `
        <div class="mt-5">
        	<h5 class="card-title">${title}</h5>
	        <div class="card mt-2">
	            <div class="card-body">
	                ${content}
	            </div>
	        </div>
				</div>
    `;
}

export function createLeadDetailsComponent(lead) {
		const likeButtonHtml = `
	        <div class="liked-lead-btn socket-btn" data-id="${lead.id}" style="text-align: right; margin-bottom: -1em;">
	            <i class="fa-${lead.liked ? 'solid' : 'regular'} fa-thumbs-up" style="font-size: 36px;"></i>
	        </div>
    `;
    return createCardComponent("Lead Details", `
    		<div style="display: flex; justify-content: space-between">
    			<div class="card-text card-text-name">${lead.name}</div>
 					${likeButtonHtml}
      	</div>
        <div class="card-text">${lead.description}</div>
        <div class="card-text"><a href="${lead.url}" target="_blank">${lead.url}</a></div>
        <div class="card-text">Contact Info: ${lead.contact_info}</div>
        <div class="card-text">Contact Page: <a href="${lead.contact_page}" target="_blank">${lead.contact_page}</a></div>
        <hr>
        ${!lead.valid ? `<div class="card-text">Invalid URL</div>` : ''}
        <div class="card-text">Checked: ${lead.checked ? 'Yes' : 'No'}</div>
        <div class="card-text">Liked: ${lead.liked ? 'Yes' : 'No'}</div>
        <div class="card-text">Quality Score: ${lead.quality_score || 0}</div>
        ${lead.query_obj ? `<a href="/query/${lead.query_obj.guid}" class="btn btn-primary mt-2">View Query</a>` : ''}
        ${lead.lead_source ? `<a href="/source/${lead.lead_source.guid}" class="btn btn-primary mt-2">View Source</a>` : ''}
        ${lead.hidden ? '<div class="card-text">[[ HIDDEN ]]</div>' : ''}
    `);
}

export function createSourceDetailsComponent(source) {
    return createCardComponent("Source Details", `
        <div class="card-text card-text-name">${source.name}</div>
        <div class="card-text">${source.description}</div>
        <div class="card-text"><a href="${source.url}" target="_blank">${source.url}</a></div>
        <hr>
        ${!source.valid ? `<div class="card-text">Invalid URL</div>` : ''}
        <div class="card-text">Checked: ${source.checked ? 'Yes' : 'No'}</div>
        <div class="card-text">Quality Score: ${source.quality_score}</div>
        ${source.query_obj ? `<a href="/query/${source.query_obj.guid}" class="btn btn-primary mt-2">View Query</a>` : ''}
        ${source.hidden ? '<div class="card-text">[[ HIDDEN ]]</div>' : ''}
    `);
}

export function createQueryDetailsComponent(query) {
    return createCardComponent("Query Details", `
        <div class="card-text card-text-name">${query.user_query}</div>
        <div class="card-text">Reformatted: ${query.reformatted_query}</div>
        <hr>
        <div class="card-text">Finished: ${query.finished ? 'Yes' : 'No'}</div>
        ${query.hidden ? '<div class="card-text">[[ HIDDEN ]]</div>' : ''}
    `);
}

export function createTableComponent(title, tableId, searchId) {
    return `
        <div class="mt-5">
            <h2 style="text-align: center;">${title}</h2>
            <div id="${tableId}-count" class="text-center small"></div>
            <input type="text" id="${searchId}" placeholder="Search ${title.toLowerCase()}...">
            <div id="${tableId}" class="table-container" style="width: 100%;"></div>
        </div>
    `;
}

export function initializeLikeButtons() {
    document.addEventListener('click', function(event) {
        if (event.target.closest('.liked-lead-btn')) {
            const button = event.target.closest('.liked-lead-btn');
            const leadId = button.getAttribute('data-id');
            socket.emit('liked_lead', { lead_id: leadId });
        } else if (event.target.closest('.liked-source-btn')) {
            const button = event.target.closest('.liked-source-btn');
            const sourceId = button.getAttribute('data-id');
            socket.emit('liked_source', { source_id: sourceId });
        }
    });

    // Handle socket events for updating the like status
    socket.on('lead_liked', function(data) {
        updateLikeButton('.liked-lead-btn', data.lead);
    });

    socket.on('source_liked', function(data) {
        updateLikeButton('.liked-source-btn', data.source);
    });
}

function updateLikeButton(buttonSelector, item) {
    const button = document.querySelector(`${buttonSelector}[data-id="${item.id}"]`);
    if (button) {
        const icon = button.querySelector('i');
        icon.className = `fa-${item.liked ? 'solid' : 'regular'} fa-thumbs-up`;

        const likedStatus = button.closest('.card-body').querySelector('.liked-status');
        if (likedStatus) {
            likedStatus.textContent = `Liked: ${item.liked ? 'Yes' : 'No'}`;
        }
    } else {
    		console.error(`Could not find button with selector: ${buttonSelector}[data-id="${item.id}"]`);
    }
}
