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
        <div class="card-text">Scanned: ${lead.checked ? 'Yes' : 'No'}</div>
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
        <div class="card-text">Scanned: ${source.checked ? 'Yes' : 'No'}</div>
        <div class="card-text">Quality Score: ${source.quality_score}</div>
        ${source.query_obj ? `<a href="/query/${source.query_obj.guid}" class="btn btn-primary mt-2">View Query</a>` : ''}
        ${source.hidden ? '<div class="card-text">[[ HIDDEN ]]</div>' : ''}
    `);
}

export function createQueryDetailsComponent(query) {
    return createCardComponent("Query Details", `
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div class="card-text card-text-name">${query.user_query}</div>
            ${query.finished ?
                '<i class="fas fa-check" style="font-size: 1.5em;"></i>' :
                '<div class="spinner-border" role="status"  style="height: 1.5em; width: 1.5em;"><span class="visually-hidden">Loading...</span></div>'
            }
        </div>
        <hr>
        <div class="card-text"><b>Search Progress</b>: ${query.n_results_retrieved && query.n_results_requested ? Math.round((query.n_results_retrieved / query.n_results_requested) * 100) : 0}%</div>
        ${query.n_results_retrieved ? `<div class="card-text"><b>Search Results Checked</b>: ${query.n_results_retrieved}</div>` : ''}
        ${query.location ? `<div class="card-text"><b>Location</b>: ${query.location}</div>` : ''}
        ${query.total_cost_credits ? `<div class="card-text"><b>Cost</b>: ${Math.trunc(query.total_cost_credits).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')} credits</div>` : ''}

        ${query.example_leads.length > 0 ? `
        <div class="card-text mt-2"><b>Example Leads</b>:
            ${query.example_leads.map(lead => `
            <a href="${lead.url}" target="_blank">
                <div>${lead.name || lead.url}${lead.description ? `: ${lead.description}` : ''}</div>
            </a>`).join('')}
        </div>` : ''}
        ${query.budget ? `<div class="card-text mt-2"><b>Budget</b>: ${query.budget.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')} credits</div>` : ''}
        ${query.over_budget ? '<div class="card-text"><b>Budget exceeded</b></div>' : ''}
        ${query.hidden ? '<div class="card-text mt-4"><b>HIDDEN</b></div>' : ''}
    `);
}

export function createTableComponent(title, id_prefix) {
    const dropdownActionClasses = ['select-all', 'select-checked', 'select-unchecked', 'select-invalid','check-all', 'export-csv',  'unselect-all', 'hide-all', 'unhide-all'];
    const tableId = `${id_prefix}-table`;
    const actionsDropdownId = `${id_prefix}-actions-dropdown`;
    const selectDropdownId = `${id_prefix}-select-dropdown`;
    const searchId = `${id_prefix}-search`;
    
    const actionClasses = dropdownActionClasses.filter(cls => ['check-all', 'export-csv', 'hide-all', 'unhide-all'].includes(cls));
    const selectClasses = dropdownActionClasses.filter(cls => ['select-all', 'select-checked', 'select-unchecked', 'select-invalid', 'unselect-all'].includes(cls));

    const actionMenu = dropdownActionClasses.length > 0 ? `
    <div class="select-all-container">
        <span class="selected-count" id="${tableId}-selected-count"></span>
        <div class="dropdown">
            <button class="btn btn-secondary dropdown-toggle" type="button" id="${selectDropdownId}" data-bs-toggle="dropdown" aria-expanded="false">
                Select
            </button>
            <ul class="dropdown-menu" aria-labelledby="${selectDropdownId}">
                ${selectClasses.map(actionClass => `<li><a class="dropdown-item ${actionClass}" href="#">${getActionDisplayName(actionClass)}</a></li>`).join('')}
            </ul>
        </div>
        <div class="dropdown">
            <button class="btn btn-secondary dropdown-toggle" type="button" id="${actionsDropdownId}" data-bs-toggle="dropdown" aria-expanded="false">
                Actions
            </button>
            <ul class="dropdown-menu" aria-labelledby="${actionsDropdownId}">
                ${actionClasses.map(actionClass => `<li><a class="dropdown-item ${actionClass}" href="#">${getActionDisplayName(actionClass)}</a></li>`).join('')}
            </ul>
        </div>
    </div>` : '';

    return `
        <div class="mt-5">
            <h2 style="text-align: center;">${title}</h2>
            <div id="${tableId}-count" class="text-center small"></div>
            <div style="display: flex; justify-content: space-between; margin-top: 1em;">
                <input type="text" id="${searchId}" placeholder="Search ${title.toLowerCase()}..." class="table-search-input form-control" style="width: 100%;">
                ${actionMenu}
            </div>
            <div id="${tableId}" class="table-container" style="width: 100%;">
                <div class="loading-icon-container">
                    <img class="loading-icon" src="/static/assets/chunk-loader.svg">
                </div>
            </div>
        </div>
    `;
}

function getActionDisplayName(actionClass) {
    switch(actionClass) {
        case 'select-all':
            return 'Select Visible';
        case 'unselect-all':
            return 'Unselect Visible';
        case 'select-checked':
            return 'Select Scanned';
        case 'select-unchecked':
            return 'Select Unscanned';
        case 'select-invalid':
            return 'Select Invalid';
        case 'check-all':
            return 'Scan Selected';
        case 'hide-all':
            return 'Hide Selected';
        case 'unhide-all':
            return 'Unhide Selected';
        case 'export-csv':
            return 'Export to CSV';
        default:
            return '';
    }
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

export function createSourceStatusBar() {
    return createCardComponent('Lead Sources', `
        <div id="query-sources-status-bar">
            <div id="source-progress-counter" class="mb-2" style="display: flex; justify-content: flex-start; align-items: center;">
                <b>Scanned</b>: <span class="spinner-border spinner-border-sm ms-1" role="status" aria-hidden="true"></span>
            </div>
            <div class="progress mb-3">
                <div id="checked-sources-bar" class="progress-bar checked-sources-bar" role="progressbar" style="width: 0%"></div>
                <div id="in-progress-sources-bar" class="progress-bar in-progress-sources-bar" role="progressbar" style="width: 0%"></div>
                <div id="unchecked-sources-bar" class="progress-bar" role="progressbar" style="width: 0%; background-color: rgba(172, 177, 207, 0.451);"></div>
            </div>
            <hr>
            <div class="status-buttons">
                <button id="check-10-sources" class="btn btn-primary check-sources-btn">Scan 10</button>
                <button id="check-50-sources" class="btn btn-primary check-sources-btn">Scan 50</button>
                <button id="check-100-sources" class="btn btn-primary check-sources-btn">Scan 100</button>
                <button id="check-all-sources" class="btn btn-primary check-sources-btn">Scan All</button>
            </div>
        </div>
    `, 'bg-light text-dark mb-4');
}
