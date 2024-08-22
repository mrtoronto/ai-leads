import { socket } from "./socket.js";

// Data cache management
const dataCache = {
    requests: {},
    sources: {},
    leads: {}
};

window.confirmHides = true;

const desktopLeadNameFormatter = (cell, row) => {
    let content = cell ? cell : row.base_url;
    const isUrl = !cell;
    const percentage = row.quality_score !== null ? Math.floor(row.quality_score * 100) : 0;
    const color = `rgb(${Math.floor(255 - (percentage * 2.55))}, ${Math.floor(percentage * 2.55)}, 0)`;
    const containerStyle = 'text-align: left; padding: 5px; display: flex; flex-direction: row; align-items: center; gap: 1em;';
    const style = `${isUrl ? 'word-break: break-all;' : 'word-break: normal;'}`;
    const linkStyle = 'font-size: 12px; display: block;';
    const imageUrl = row.image_url
					? row.image_url
					: (row.checked && row.valid)
					? '/static/assets/ai-leads-checkMark.png'
					: (row.checked && !row.valid)
					? '/static/assets/ai-leads-x.png'
					: '/static/assets/placeholder_img.png';
    const imageLink = row.guid
					? `/lead/${row.guid}`
					: '#';
    const qualityBar = percentage > 0 ? `
        <div style="display: flex; align-items: center;">
	        <div class="quality-bar-container">
	            <div class="quality-bar" style="height: ${percentage}%; background-color: ${color};"></div>
	        </div>
        </div>` : '';
    return cell
        ? `<div style="${containerStyle}">${qualityBar}
		        <div style="min-width: 50px">
							<a href="${imageLink}"  target="_blank">
								<img src="${imageUrl}" alt="Lead image" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
							</a>
						</div>
		        <div style="display: flex; flex-direction: column; overflow: hidden;text-overflow: ellipsis;white-space: nowrap;">
		        	<a href="/lead/${row.guid}" class="lead-name" data-id="${row.id}" style="${style}">${content}</a>
		         	<a href="${row.base_url}" target="_blank" style="${linkStyle}">${row.base_url}</a>
		        </div>
					</div>`
        : `<div style="${containerStyle}">
          	<div style="min-width: 50px">
							<a href="${imageLink}"  target="_blank" style="min-width: 50px">
								<img src="${imageUrl}" alt="Lead image" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
							</a>
						</div>
          	<a href="${row.base_url}" target="_blank" style="${style}">${content}</a>
          </div>`;
}

const mobileLeadNameFormatter = (cell, row) => {
	const content = cell ? cell : row.url;
	const isUrl = !cell;
	const percentage = row.quality_score !== null ? Math.floor(row.quality_score * 100) : 0;
	const color = `rgb(${Math.floor(255 - (percentage * 2.55))}, ${Math.floor(percentage * 2.55)}, 0)`;
	const containerStyle = 'text-align: left; padding: 5px; display: flex; flex-direction: column;';
	const style = `${isUrl ? 'word-break: break-all;' : 'word-break: normal;'} min-width: 50px`;
	const linkStyle = 'font-size: 12px; display: block; min-width: 50px';
	const qualityBar = percentage > 0 ? `
					<div style="display: flex; align-items: center;">
							<div class="quality-bar-container">
                  <div class="quality-bar" style="height: ${percentage}%; background-color: ${color};"></div>
              </div>
					</div>` : '';
	const imageUrl = row.image_url
			? row.image_url
			: (row.checked && row.valid)
			? '/static/assets/ai-leads-checkMark.png'
			: (row.checked && !row.valid)
			? '/static/assets/ai-leads-x.png'
			: '/static/assets/placeholder_img.png';
	const imageLink = row.guid
					? `/lead/${row.guid}`
					: '#';
	return cell
					? `<div style="${containerStyle}">
									<div style="display: flex; align-items: center; gap: 0.5em;">
										${qualityBar}
										<div style="min-width: 50px">
											<a href="${imageLink}"  target="_blank">
												<img src="${imageUrl}" alt="Lead image" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
											</a>
										</div>
										<div style="display: flex; flex-direction: column; width: 100%;>
											<a href="${imageLink}" class="lead-name"  target="_blank" data-id="${row.id}" style="${style}">
												<span style="text-overflow: ellipsis;">${content}</span>
											</a>
											<a href="${imageLink}" target="_blank" style="${linkStyle}"  class="name-url">${row.url}</a>
										</div>
									</div>
						</div>`
					: `<div style="${containerStyle}">
									<div style="display: flex; align-items: center; gap: 0.5em;">
										<div style="min-width: 50px">
											<a href="${imageLink}" target="_blank">
												<img src="${imageUrl}" alt="Lead image" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
											</a>
										</div>
										<div style="display: flex; flex-direction: column; width: 100%; overflow: hidden;text-overflow: ellipsis;white-space: nowrap;">
											<a class="name-url" href="${row.url}" target="_blank" style="${style}">${content}</a>
										</div>
									</div>
							</div>`;
}

const addRowById = (tableId, row) => {
	switch (tableId) {
	    case 'requests-table':
	        return !row.hidden;
	    case 'sources-table':
	        return !row.hidden;
	    case 'checking-lead-sources-table':
	        return !row.hidden;
	    case 'leads-table':
	        return !row.hidden;
	    case 'liked-leads-table':
	        return !row.hidden;
	    case 'checking-leads-table':
	        return !row.hidden;
	    case 'checked-leads-table':
	        return !row.hidden;
	    case 'unchecked-leads-table':
	        return !row.hidden;
	    case 'all-leads-table':
	        return !row.hidden;
	    case 'hidden-leads-table':
	        return row.hidden;
	    case 'hidden-queries-table':
	        return row.hidden;
	    case 'running-queries-table':
	        return !row.finished && !row.hidden;
	    default:
	        if (tableId.includes('queries') || tableId.includes('sources') || tableId.includes('leads')) {
	            return !row.hidden;
	        }
	        console.error(`Unknown table id: ${tableId}`);
	        return false;
	}

}

const getTableColumnsById = (tableId) => {
    switch(tableId) {
        case 'requests-table':
            return getQueryTableColumns();
        case 'sources-table':
            return getSourceTableColumns();
        case 'checking-lead-sources-table-container':
            return getSourceTableColumns();
        case 'leads-table':
            return getLeadTableColumns();
        case 'liked-leads-table':
            return getLeadTableColumns();
        case 'checking-leads-table-container':
            return getLeadTableColumns();
        case 'checked-leads-table-container':
            return getLeadTableColumns();
        case 'unchecked-leads-table-container':
            return getLeadTableColumns();
        case 'all-leads-table-container':
            return getLeadTableColumns();
        case 'hidden-leads-table-container':
            return getLeadTableColumns();
        default:
						if (tableId.includes('queries')) {
						    return getQueryTableColumns();
						} else if (tableId.includes('sources')) {
						    return getSourceTableColumns();
						} else if (tableId.includes('leads')) {
						    return getLeadTableColumns();
						}
            console.error(`Unknown table id: ${tableId}`);
            return [];
    }
};

const applyFormatter = (formatter, cell, row) => {
    if (typeof formatter === 'function') {
        return formatter(cell, row);
    }
    return cell;
};

// Helper functions
function updateCounts() {
		const tables = [
		    "requests-table",
		    "sources-table",
		    "checking-lead-sources-table",
		    "leads-table",
		    "liked-leads-table",
		    "checking-leads-table",
		    "checked-leads-table",
		    "unchecked-leads-table",
		    "all-leads-table",
		    "hidden-leads-table",
				"all-queries-table",
				"running-queries-table",
				"hidden-queries-table",
				"query-leads-table",
				"query-sources-table"
		];
    tables.forEach(tableId => {
        const table = document.getElementById(tableId);
        if (table) {
						const bodyContainer = table.querySelector('.table-body-container');
						const count = bodyContainer ? bodyContainer.querySelectorAll('.table-row:not(.table-header)').length : 0;
            const countElement = document.getElementById(`${tableId}-count`);
            if (countElement) {
                countElement.textContent = `Total: ${count}`;
            } else {
            	console.log(`Count element not found for table: ${tableId}`);
            }
        } else {
        	console.log(`Table not found: ${tableId}`);
        }
    });
}

function searchTable(tableId, searchTerm) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('.table-row:not(.table-header)');

    rows.forEach(row => {
        const nameCell = row.querySelector('.table-cell[data-field="name"]');
        const urlCell = row.querySelector('.table-cell[data-field="name"] a');
        const queryCell = row.querySelector('.table-cell[data-field="user_query"]');
        const reformattedCell = row.querySelector('.table-cell[data-field="reformatted_query"]');
        const name = nameCell ? nameCell.textContent.toLowerCase() : '';
        const url = urlCell ? urlCell.href.toLowerCase() : '';
        const query = queryCell ? queryCell.textContent.toLowerCase() : '';
        const reformatted = reformattedCell ? reformattedCell.textContent.toLowerCase() : '';

        if (name.includes(searchTerm.toLowerCase()) || url.includes(searchTerm.toLowerCase()) || query.includes(searchTerm.toLowerCase()) || reformatted.includes(searchTerm.toLowerCase)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function sortTable(tableId, columnIndex) {
    const table = document.getElementById(tableId);
    const bodyContainer = table.querySelector('.table-body-container');
    const rows = Array.from(bodyContainer.querySelectorAll('.table-row'));
    const header = table.querySelector('.table-header');
    const headerCells = Array.from(header.querySelectorAll('.table-cell'));

    // Check if the columnIndex is valid
    if (columnIndex < 0 || columnIndex >= headerCells.length) {
        console.error(`Invalid column index: ${columnIndex}`);
        return;
    }

    const headerCell = headerCells[columnIndex];

    // Toggle sort direction
    let sortDirection = headerCell.getAttribute('data-sort') === 'asc' ? 'desc' : 'asc';
    headerCells.forEach(cell => cell.removeAttribute('data-sort'));
    headerCell.setAttribute('data-sort', sortDirection);

    rows.sort((a, b) => {
        const aCells = Array.from(a.querySelectorAll('.table-cell'));
        const bCells = Array.from(b.querySelectorAll('.table-cell'));

        if (columnIndex >= aCells.length || columnIndex >= bCells.length) {
            console.error(`Column index ${columnIndex} is out of range for some rows`);
            return 0;
        }

        const aCell = aCells[columnIndex];
        const bCell = bCells[columnIndex];
        const aValue = aCell ? aCell.textContent.trim() : '';
        const bValue = bCell ? bCell.textContent.trim() : '';

        // Check if the values are numbers
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);

        if (!isNaN(aNum) && !isNaN(bNum)) {
            return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
        } else {
            if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
            if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        }
    });

    // Clear and re-append sorted rows
    bodyContainer.innerHTML = '';
    rows.forEach(row => bodyContainer.appendChild(row));
}


// Column definitions
let getQueryTableColumns;
getQueryTableColumns = () => [
    { id: 'id', name: 'ID', field: 'id', hidden: true },
    { id: 'user_query', width: '200px', name: 'User Query', field: 'user_query', formatter: (cell, row) => `<a href="/query/${row.guid}" data-id="${row.id}">${cell}</a>` },
    { id: 'reformatted_query', width: '200px', name: 'Reformatted Query', field: 'reformatted_query' },
    { id: 'n_leads', name: '# of Leads', width: '90px', field: 'n_leads' },
    { id: 'n_sources', name: '# of Sources', width: '90px', field: 'n_sources' },
    { id: 'hidden', name: 'Hide', width: '90px', field: 'hidden', formatter: (_, row) => {
				if (row.hidden) {
					return `<div class="btn-danger-fill-light unhide-request-btn socket-btn full-width-action-btn" data-id="${row.id}"><i class="fa-solid fa-trash-can-arrow-up fa-icon"></i></div>`

			 } else {
					return `<div class="btn-danger-fill-light hide-request-btn socket-btn full-width-action-btn" data-id="${row.id}"><i class="fa-solid fa-trash-can fa-icon"></i></div>`
				}
			}
    }
];

let getSourceTableColumns;
getSourceTableColumns = () => [
    { id: 'id', name: 'ID', field: 'id', hidden: true },
    { id: 'checking', name: 'Checking', field: 'checking', hidden: true },
    {
        id: 'name',
        width: '300px',
        textAlign: 'left !important',
        name: 'Name',
        field: 'name',
        formatter: (cell, row) => {
            const content = cell ? cell : row.url;
            const isUrl = !cell;
            const containerStyle = 'text-align: left; padding: 5px; display: flex; flex-direction: row; gap: 1em;';
            const style = `${isUrl ? 'word-break: break-all;' : 'word-break: normal;'}`;
            const linkStyle = 'font-size: 10px; display: block;';
            const imageUrl = row.image_url
									? row.image_url
									: (row.checked && row.valid)
									? '/static/assets/ai-leads-checkMark.png'
									: (row.checked && !row.valid)
									? '/static/assets/ai-leads-x.png'
									: '/static/assets/placeholder_img.png';
		        const imageLink = row.guid
							? `/source/${row.guid}`
							: '#';
            return cell
									? `<div style="${containerStyle}; display: flex; align-items: center;">
													<div style="min-width: 50px">
														<a href="${imageLink}"  target="_blank">
															<img src="${imageUrl}" alt="Lead image" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
														</a>
													</div>
													<div style="display: flex; flex-direction: column; overflow: hidden;text-overflow: ellipsis;white-space: nowrap;">
													<a href="/source/${row.guid}" class="source-name" data-id="${row.id}" style="${style}">${content}</a>
													<a href="${row.url}" target="_blank" style="${linkStyle}">${row.url}</a>
													</div>
										</div>`
									: `<div style="${containerStyle}; display: flex; align-items: center;">
												<div style="display: flex; flex-direction: column; overflow: hidden;text-overflow: ellipsis;white-space: nowrap; min-width: 50px">
													<a href="${imageLink}"  target="_blank">
														<img src="${imageUrl}" alt="Lead image" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
													</a>
												</div>
												<a href="${row.url}" target="_blank" style="${style}" class="name-url">${content}</a>
										</div>`;
        }
    },
    { id: 'description', whiteSpace: 'wrap !important', width: '300px',  name: 'Description', field: 'description', formatter: (cell) => `<div style="font-size: 12px; max-width: 250px; overflow-wrap: break-word; word-wrap: break-word;">${cell || "---"}</div>` },
    { id: 'n_leads', width: '90px', name: '# of Leads', field: 'n_leads' },
    {
        id: 'actions',
        width: '120px',
        name: 'Actions',
        field: 'actions',
        formatter: (cell, row) => {
            if (row.checking) {
                return `<div class="actions-container">
                            <div class="cell-spinner-container"><img src="/static/assets/loadingGears.svg" class="cell-spinner source-cell-spinner" data-id="${row.id}"></div>
                            <div class="btn-danger-fill-light hide-source-btn socket-btn action-child-border-left" data-id="${row.id}"><i class="fa-solid fa-trash-can fa-icon"></i></div>
                        </div>`;
            } else if (row.checked) {
                return `<div class="actions-container">
                            <div class="btn-danger-fill-light hide-source-btn socket-btn full-width-action-btn" data-id="${row.id}"><i class="fa-solid fa-trash-can fa-icon"></i></div>
                        </div>`;
            } else {
                return `<div class="actions-container">
                            <div class="btn-primary-fill-dark check-source-btn socket-btn" data-id="${row.id}" style="border-top-right-radius: 0; border-bottom-right-radius: 0;"><i class="fa-brands fa-searchengin fa-icon"></i></div>
                            <div class="btn-danger-fill-light hide-source-btn socket-btn action-child-border-left" data-id="${row.id}" style="border-top-left-radius: 0; border-bottom-left-radius: 0;"><i class="fa-solid fa-trash-can fa-icon"></i></div>
                        </div>`;
            }
        }
    }
];

let getLeadTableColumns;
getLeadTableColumns = () => [
    { id: 'id', name: 'ID', field: 'id', hidden: true },
    { id: 'checking', name: 'Checking', field: 'checking', hidden: true },
    {
        id: 'name', width: '300px', textAlign: 'left !important', name: 'Name', field: 'name', formatter: (cell, row) => desktopLeadNameFormatter(cell, row)
    },
    { id: 'description', whiteSpace: 'wrap !important', width: '300px', name: 'Description', field: 'description', formatter: (cell) => `<div style="font-size: 12px;">${cell || "---"}</div>` },
    {
        id: 'contact',
        width: '200px',
        name: 'Contact',
        field: 'contact',
        formatter: (cell, row) => {
            const contactInfo = row.contact_info || '---';
            const contactPage = row.contact_page ? `<a href="${row.contact_page}" target="_blank">Contact Page</a>` : '---';

            // Check if contactInfo is an email address
            const isEmail = /\S+@\S+\.\S+/.test(contactInfo);

            let contactInfoHtml = '';
            if (isEmail) {
                contactInfoHtml = `
                    <div style="font-size: 12px; display: flex; align-items: center;">
                        <div class="copy-email-btn socket-btn" data-email="${contactInfo}" style="margin-right: 5px; padding: 2px 5px; font-size: 10px;"><i class="fa-solid fa-clipboard fa-icon"></i></div>
                        <span>${contactInfo}</span>
                    </div>`;
            } else {
                contactInfoHtml = `<div style="font-size: 12px;">${contactInfo}</div>`;
            }

            return `
                ${contactInfoHtml}
                <div style="font-size: 12px;">${contactPage}</div>
            `;
        }
    },
		{
		    id: 'actions',
		    width: '120px',
		    name: 'Actions',
		    field: 'actions',
		    formatter: (cell, row) => {
		        if (row.checking) {
		            return `<div class="actions-container">
		                        <div class="cell-spinner-container"><img src="/static/assets/loadingGears.svg" class="cell-spinner lead-cell-spinner" data-id="${row.id}"></div>
		                        <div class="btn-danger-fill-light hide-lead-btn socket-btn action-child-border-left" data-id="${row.id}"><i class="fa-solid fa-trash-can fa-icon"></i></div>
		                    </div>`;
		        } else if ((row.checked) && (row.valid) && (!row.hidden)) {
		            return `<div class="actions-container">
		                        <div class="${row.liked ? 'btn-primary-fill-light' : 'btn-primary-outline-light'} liked-lead-btn socket-btn" data-id="${row.id}" style="border-top-right-radius: 0; border-bottom-right-radius: 0;"><i class="fa-${row.liked ? 'solid' : 'regular'} fa-thumbs-up fa-icon"></i></div>
		                        <div class="${row.hidden ? 'btn-danger-fill-light unhide-lead-btn' : 'btn-danger-fill-light hide-lead-btn'} socket-btn action-child-border-left" data-id="${row.id}" style="border-top-left-radius: 0; border-bottom-left-radius: 0;">
		                            <i class="fa-solid ${row.hidden ? 'fa-trash-can-arrow-up' : 'fa-trash-can'} fa-icon"></i>
		                        </div>
		                    </div>`;
		        } else if ((row.checked) || (row.hidden)) {
		            return `<div class="actions-container">
		                        <div class="${row.hidden ? 'btn-danger-fill-light unhide-lead-btn' : 'btn-danger-fill-light hide-lead-btn'} socket-btn full-width-action-btn" data-id="${row.id}">
		                            <i class="fa-solid ${row.hidden ? 'fa-trash-can-arrow-up' : 'fa-trash-can'} fa-icon"></i>
		                        </div>
		                    </div>`;
		        } else {
		            return `<div class="actions-container">
		                        <div class="btn-primary-fill-dark check-lead-btn socket-btn" data-id="${row.id}" style="border-top-right-radius: 0; border-bottom-right-radius: 0; "><i class="fa-brands fa-searchengin fa-icon"></i></div>
		                        <div class="${row.hidden ? 'btn-danger-fill-light unhide-lead-btn' : 'btn-danger-fill-light hide-lead-btn'} socket-btn action-child-border-left" data-id="${row.id}" style="border-top-left-radius: 0; border-bottom-left-radius: 0;">
		                            <i class="fa-solid ${row.hidden ? 'fa-trash-can-arrow-up' : 'fa-trash-can'} fa-icon"></i>
		                        </div>
		                    </div>`;
		        }
		    }
		}
];

if (window.is_mobile) {
	getQueryTableColumns = () => [
		{ id: 'id', name: 'ID', field: 'id', hidden: true },
		{ id: 'user_query', name: 'User Query', field: 'user_query', formatter: (cell, row) => `<a href="/query/${row.guid}" data-id="${row.id}">${cell}</a>` },
		{ id: 'reformatted_query', name: 'Reformatted Query', field: 'reformatted_query' },
		{
			id: 'totals',
			name: 'Totals',
			formatter: (cell, row) => {
				const nLeads = row.n_leads || 0;
				const nSources = row.n_sources || 0;
				const leadsFontSize = nLeads > 9 ? '18px' : '24px';
				const sourcesFontSize = nSources > 9 ? '18px' : '24px';
				const leadsFontWeight = nLeads > 100 ? 'bold' : 'normal';
				const sourcesFontWeight = nSources > 100 ? 'bold' : 'normal';
				return `<div style="display: flex; justify-content: space-between; width: 100%;">
								<div style="width: 50%; font-size: ${leadsFontSize}; font-weight: ${leadsFontWeight}; text-align: center;">
										${nLeads}
										<div style="font-size: 12px;">Leads</div>
								</div>
								<div style="width: 50%; font-size: ${sourcesFontSize}; font-weight: ${sourcesFontWeight}; text-align: center;">
										${nSources}
										<div style="font-size: 12px;">Sources</div>
								</div>
				</div>`;
			}
		},
		{
				id: 'actions',
				name: 'Actions',
				field: 'actions',
				formatter: (_, row) => `
					<div class="actions-container" style="display: flex; margin-top: 0px;">
								<div style="width: 50%;margin: auto; text-align: center;" class="socket-btn">
									${row.finished ? '<i class="fa-solid fa-check fa-icon">' : '<i class="fa-solid fa-x fa-icon">'}</i>
								</div>
								<div style="width: 50%;margin: auto; text-align: center;" class="${row.hidden ? 'btn-danger-fill-light unhide-request-btn' : 'btn-danger-fill-light hide-request-btn'} socket-btn full-width-action-btn" data-id="${row.id}">
								    <i class="fa-solid ${row.hidden ? 'fa-trash-can-arrow-up' : 'fa-trash-can'} fa-icon"></i>
								</div>
					</div>`
		}
	];

	getSourceTableColumns = () => [
        { id: 'id', name: 'ID', field: 'id', hidden: true },
        { id: 'checking', name: 'Checking', field: 'checking', hidden: true },
        {
            id: 'name',
            width: '100%',
            textAlign: 'left !important',
            name: 'Name',
            field: 'name',
            formatter: (cell, row) => {
                const content = cell ? cell : row.url;
                const isUrl = !cell;
                const percentage = row.quality_score !== null ? Math.floor(row.quality_score * 100) : 0;
                const color = `rgb(${Math.floor(255 - (percentage * 2.55))}, ${Math.floor(percentage * 2.55)}, 0)`;
                const containerStyle = 'text-align: left; padding: 5px; display: flex; flex-direction: column; gap: 0.5em;';
                const style = `${isUrl ? 'word-break: break-all;' : 'word-break: normal;'}`;
                const imageUrl = row.image_url
									? row.image_url
									: (row.checked && row.valid)
									? '/static/assets/ai-leads-checkMark.png'
									: (row.checked && !row.valid)
									? '/static/assets/ai-leads-x.png'
									: '/static/assets/placeholder_img.png';
				        const imageLink = row.guid
									? `/source/${row.guid}`
									: '#';
                return cell
                    ? `<div style="${containerStyle}">
                        <div style="display: flex; align-items: center; gap: 0.5em;">
	                      		<div style="min-width: 50px">
															<a href="${imageLink}"  target="_blank">
																<img src="${imageUrl}" alt="Lead image" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
															</a>
														</div>
                            <div style="width: 100%;">
                                <a href="/source/${row.guid}" class="source-name" data-id="${row.id}" style="${style}">${content}</a>
                                <a class="link-below-name" href="${row.url}" target="_blank">${row.url}</a>
                            </div>
                        </div>
                        <div class="description-text">
                        	${row.description || ''}
                        </div>
                    </div>`
                    : `<div style="${containerStyle}">
                        <div style="display: flex; align-items: center;">
                      		<div style="display: flex; flex-direction: column; overflow: hidden;text-overflow: ellipsis;white-space: nowrap;min-width: 50px">
															<a href="${imageLink}"  target="_blank">
																<img src="${imageUrl}" alt="Lead image" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
															</a>
														</div>
                            <a href="${row.url}" target="_blank" style="${style}" class="name-url">${content}</a>
                        </div>
                    </div>`;
            }
        },
        {
					id: 'totals',
					name: 'Totals',
					field: 'n_leads',
					formatter: (cell, row) => {
						const nLeads = row.n_leads || 0;
						if (!nLeads) {
							return ``;
						}
						const leadsFontSize = nLeads > 9 ? '18px' : '24px';
						const leadsFontWeight = nLeads > 100 ? 'bold' : 'normal';
						return `<div style="display: flex; justify-content: space-between; width: 100%;">
											<div style="width: 100%; font-size: ${leadsFontSize}; font-weight: ${leadsFontWeight}; text-align: center;">
												${nLeads}
												<div style="font-size: 12px;">Leads</div>
											</div>
										</div>`;
					}
				},
        {
            id: 'actions',
            width: '100%',
            name: 'Actions',
            field: 'actions',
            formatter: (cell, row) => {
                if (row.checking) {
                    return `<div class="actions-container">
                                <div class="cell-spinner-container"><img src="/static/assets/loadingGears.svg" class="cell-spinner source-cell-spinner"  data-id="${row.id}"></div>
                                <div class="btn-danger-fill-light hide-source-btn socket-btn action-child-border-left" data-id="${row.id}" style="width: 50%;margin: auto; text-align: center;"><i class="fa-solid fa-trash-can fa-icon"></i></div>
                            </div>`;
                } else if (row.checked) {
                    return `<div class="actions-container">
                    						<div class="btn-danger-fill-light hide-source-btn socket-btn full-width-action-btn" data-id="${row.id}" style="width: 50%;margin: auto; text-align: center;">
                                	<i class="fa-solid fa-trash-can fa-icon"></i>
                                </div>
                            </div>`;
                } else {
                    return `<div class="actions-container">
                                <div class="btn-primary-fill-dark check-source-btn socket-btn" data-id="${row.id}" style="width: 50%;margin: auto; text-align: center;border-top-right-radius: 0; border-bottom-right-radius: 0;"><i class="fa-brands fa-searchengin fa-icon"></i></div>
                                <div class="btn-danger-fill-light hide-source-btn socket-btn action-child-border-left" data-id="${row.id}" style="width: 50%;margin: auto; text-align: center;border-top-left-radius: 0; border-bottom-left-radius: 0;">
                                	<i class="fa-solid fa-trash-can fa-icon"></i>
                                </div>
                            </div>`;
                }
            }
        }
    ];
	getLeadTableColumns = () => [
					{ id: 'id', name: 'ID', field: 'id', hidden: true },
					{ id: 'checking', name: 'Checking', field: 'checking', hidden: true },
					{
						id: 'name', width: '100%', textAlign: 'left !important', name: 'Name', field: 'name', formatter: (cell, row) => mobileLeadNameFormatter(cell, row)
					},
					{ id: 'description', whiteSpace: 'wrap !important', width: '100%', name: 'Description', field: 'description', formatter: (cell) => {
							if (cell) {
								return `<div style="font-size: 12px;">${cell}</div>`
							} else {
								return ``
							}
						}
					},
					{
									id: 'contact',
									width: '100%',
									name: 'Contact',
									field: 'contact',
									formatter: (cell, row) => {
													if (!row.contact_info && !row.contact_page) {
														return ``;
													}

													// Check if contactInfo is an email address
													const isEmail = /\S+@\S+\.\S+/.test(row.contact_info);

													let contactInfoHtml = '';
													if ((row.contact_info) && (isEmail)) {
																	contactInfoHtml = `
																					<div style="font-size: 12px; display: flex; align-items: center;">
																									<span>${row.contact_info}</span>
																									<div class="copy-email-btn socket-btn" data-email="${row.contact_info}" style="margin-right: 8px; padding: 2px 5px; font-size: 9px;">
																									<i class="fa-solid fa-clipboard fa-icon"></i>
																									</div>
																					</div>`;
													} else if (row.contact_info) {
																	contactInfoHtml = `<div style="font-size: 12px;">${row.contact_info}</div>`;
													}
													let contactPageHtml = '';
													if (row.contact_page) {
														contactPageHtml = `<div style="font-size: 12px;"><a href="${row.contact_page}" target="_blank">Contact Page</a></div>`;
													}

													if ((contactInfoHtml == ``) && (contactPageHtml == ``)) {
														return ``;
													}

													return `
																	${contactInfoHtml}
																	${contactPageHtml}
													`;
									}
					},
					{
					    id: 'actions',
					    width: '100%',
					    name: 'Actions',
					    field: 'actions',
					    formatter: (cell, row) => {
					        if (row.checking) {
					            return `<div class="actions-container">
					                        <div class="cell-spinner-container"><img src="/static/assets/loadingGears.svg" class="cell-spinner lead-cell-spinner" data-id="${row.id}"></div>
					                        <div class="btn-danger-fill-light hide-lead-btn socket-btn action-child-border-left" data-id="${row.id}" style="width: 50%;margin: auto; text-align: center;"><i class="fa-solid fa-trash-can fa-icon"></i></div>
					                    </div>`;
					        } else if ((row.checked) && (row.valid) && (!row.hidden)) {
					            return `<div class="actions-container">
					                        <div class="${row.liked ? 'btn-primary-fill-light' : 'btn-primary-outline-light'} liked-lead-btn socket-btn" data-id="${row.id}" style="width: 50%;margin: auto; text-align: center;border-top-right-radius: 0; border-bottom-right-radius: 0;"><i class="fa-${row.liked ? 'solid' : 'regular'} fa-thumbs-up fa-icon"></i></div>
					                        <div class="${row.hidden ? 'btn-danger-fill-light unhide-lead-btn' : 'btn-danger-fill-light hide-lead-btn'} socket-btn action-child-border-left" data-id="${row.id}" style="width: 50%;margin: auto; text-align: center;border-top-left-radius: 0; border-bottom-left-radius: 0;">
					                            <i class="fa-solid ${row.hidden ? 'fa-trash-can-arrow-up' : 'fa-trash-can'} fa-icon"></i>
					                        </div>
					                    </div>`;
					        } else if (!row.checked) {
					            return `<div class="actions-container">
					                        <div class="btn-primary-fill-light check-lead-btn socket-btn" data-id="${row.id}" style="width: 50%;margin: auto; text-align: center;border-top-right-radius: 0; border-bottom-right-radius: 0;"><i class="fa-brands fa-searchengin fa-icon"></i></div>
					                        <div class="${row.hidden ? 'btn-danger-fill-light unhide-lead-btn' : 'btn-danger-fill-light hide-lead-btn'} socket-btn action-child-border-left" data-id="${row.id}" style="width: 50%;margin: auto; text-align: center;border-top-left-radius: 0; border-bottom-left-radius: 0;">
					                            <i class="fa-solid ${row.hidden ? 'fa-trash-can-arrow-up' : 'fa-trash-can'} fa-icon"></i>
					                        </div>
					                    </div>`;
					        } else {
					            return `<div class="actions-container">
					                        <div class="${row.hidden ? 'btn-danger-fill-light unhide-lead-btn' : 'btn-danger-fill-light hide-lead-btn'} socket-btn full-width-action-btn" data-id="${row.id}" style="width: 50%;margin: auto; text-align: center;">
					                            <i class="fa-solid ${row.hidden ? 'fa-trash-can-arrow-up' : 'fa-trash-can'} fa-icon"></i>
					                        </div>
					                    </div>`;
					        }
					    }
					}
	];
}

const getLikedLeadTableColumns = () => getLeadTableColumns();

const createTable = (tableId, columns, data, show_hidden=false) => {
    const table = document.getElementById(tableId);
    table.innerHTML = '';
    table.className = 'table-container';

    // Create table header
    if (!window.is_mobile) {
	    const headerRow = document.createElement('div');
	    headerRow.className = 'table-row table-header';
	    let visibleColumnIndex = 0;
	    columns.forEach((column, index) => {
	        if (!column.hidden) {
	            const headerCell = document.createElement('div');
	            headerCell.className = 'table-cell header-cell';
	            headerCell.textContent = column.name;
	            headerCell.style.cursor = 'pointer';

	            // Use an IIFE to create a new scope for each iteration
	            (function(currentIndex) {
	                headerCell.onclick = function() {
	                    console.log(`Header cell clicked: ${column.name}, visible index: ${currentIndex}`);
	                    sortTable(tableId, currentIndex);
	                };
	            })(visibleColumnIndex);
	            if (column.width) {
	                headerCell.style.width = column.width;
	            }
	            if (column.textAlign) {
	                headerCell.style.textAlign = column.textAlign;
	            } else {
	            	headerCell.style.textAlign = 'center';
	            }
	            if (column.whiteSpace) {
										headerCell.style.whiteSpace = column.whiteSpace;
	            }
	            headerRow.appendChild(headerCell);
	            visibleColumnIndex++;
	        }
	    });
	    table.appendChild(headerRow);

    }

    // Create scrollable container for table body
    const bodyContainer = document.createElement('div');
    bodyContainer.className = 'table-body-container';

    if (data.length === 0) {
        table.style.height = 'auto';
        table.style.maxHeight = '600px';
        table.style.minHeight = '150px';
        const noDataMessage = document.createElement('div');
        noDataMessage.className = 'no-data-message';
        noDataMessage.textContent = 'No data found';
        bodyContainer.appendChild(noDataMessage);
    } else {
        // Create table body
        data.forEach(rowData => {
            let row = document.createElement('div');
            row.className = 'table-row';
            row.setAttribute('data-id', rowData.id);
            row = addClassToTableRow(row, rowData);

            columns.forEach(column => {
                if (!column.hidden) {
                    const cell = document.createElement('div');
                    cell.className = 'table-cell';
                    if (column.width) {
                        cell.style.width = column.width;
                    }
                    if (column.textAlign) {
                        cell.style.textAlign = column.textAlign;
                    } else {
                        cell.style.textAlign = 'center';
                    }

                    if (column.whiteSpace) {
                        cell.style.whiteSpace = column.whiteSpace;
                    }
                    cell.setAttribute('data-field', column.field);
                    const cellValue = rowData[column.field];
                    cell.innerHTML = column.formatter ? column.formatter(cellValue, rowData) : cellValue;
                    row.appendChild(cell);
                }
            });
            bodyContainer.appendChild(row);
        });
    }

    table.appendChild(bodyContainer);
};

const addClassToTableRow = (row, data) => {
	if ('valid' in data && data.valid === false && data.checked) {
   	row.classList.remove('valid-table-row', 'contactable-table-row', 'unchecked-table-row', 'checking-table-row');
    row.classList.add('invalid-table-row');
	} else if ('contact_info' in data && (data.contact_info || data.contact_page)) {
		row.classList.remove('valid-table-row', 'invalid-table-row', 'unchecked-table-row', 'checking-table-row');
		row.classList.add('contactable-table-row');
	} else if ((data.valid && data.checked) || (data.finished)) {
		row.classList.remove('invalid-table-row', 'contactable-table-row', 'unchecked-table-row', 'checking-table-row');
		row.classList.add('valid-table-row');
	} else if (data.checking) {
		row.classList.remove('valid-table-row', 'contactable-table-row', 'invalid-table-row', 'unchecked-table-row', 'checking-table-row');
		row.classList.add('checking-table-row');
	} else if ('finished' in data && data.finished === false) {
		row.classList.remove('valid-table-row', 'contactable-table-row', 'invalid-table-row', 'unchecked-table-row', 'checking-table-row');
		row.classList.add('checking-table-row');
	} else {
		row.classList.remove('valid-table-row', 'contactable-table-row', 'invalid-table-row', 'checking-table-row', 'checking-table-row');
		row.classList.add('unchecked-table-row');
	}
	return row
}

const updateRow = (tableId, newData) => {
		console.log(`Updating table: ${tableId}`);
		console.log(newData);
    const tableElement = document.getElementById(tableId);
    if (!tableElement) return; // Skip if table doesn't exist

    let rowId = newData.id;

    let row = tableElement.querySelector(`.table-row[data-id="${rowId}"]`);
    const columns = getTableColumnsById(tableId);

    if (addRowById(tableId, newData) && row) {
    		console.log('updating existing row');
    		row = addClassToTableRow(row, newData);
        // Update existing row
        const cells = row.getElementsByClassName('table-cell');
        let visibleIndex = 0;

        columns.forEach((column) => {
            if (!column.hidden) {
									if (cells[visibleIndex]) {
										if (column.field === 'contact') {
											// Special handling for contact field
											cells[visibleIndex].innerHTML = column.formatter(null, newData);
										} else {
											const cellValue = newData[column.field];
											if ((cellValue !== null && cellValue !== undefined) || (column.field == 'actions')) {
												cells[visibleIndex].innerHTML = ''; // Clear existing content
												cells[visibleIndex].innerHTML = column.formatter ? column.formatter(cellValue, newData) : cellValue;
											}
										}
										visibleIndex++;
									}
            }
        });
    } else if (addRowById(tableId, newData)) {
			console.log('adding row');
			addRow(tableId, newData);
    } else {
			console.log('hiding row');
			handleHideEvent(tableId, rowId);
    }

    updateCounts();
};

// Modify the addRow function to ensure it's creating the row correctly
const addRow = (tableId, newData) => {
    const table = document.getElementById(tableId);

    if (!table) {
			console.log('No table found', tableId);
    	return;
    }
    console.log(tableId, newData);
    if (!addRowById(tableId, newData)) {
			handleHideEvent(tableId, newData.id);
			updateCounts();
			return;
    }
    const bodyContainer = table.querySelector('.table-body-container');
    const columns = getTableColumnsById(tableId);

    let row = document.createElement('div');
    row.className = 'table-row';
    row.setAttribute('data-id', newData.id);
    row = addClassToTableRow(row, newData);

    if (table.querySelector('.no-data-message')) {
  		table.querySelector('.no-data-message').remove();
    }

    columns.forEach(column => {
        if (!column.hidden) {
            const cell = document.createElement('div');
            cell.className = 'table-cell';
            cell.setAttribute('data-field', column.field);
            if (column.width) {
                cell.style.width = column.width;
            }
            if (column.textAlign) {
                cell.style.textAlign = column.textAlign;
            } else {
                cell.style.textAlign = 'center';
            }
            if (column.whiteSpace) {
                cell.style.whiteSpace = column.whiteSpace;
            }
            const cellValue = newData[column.field];
            cell.innerHTML = column.formatter ? column.formatter(cellValue, newData) : cellValue;
            row.appendChild(cell);
        }
    });

    // Insert the new row at the bottom of the body container
    bodyContainer.appendChild(row);
    updateCounts();
};

const handleHideEvent = (tableId, rowId) => {
		console.log('tableId' + tableId);
    const table = document.getElementById(tableId);
    if (table) {
	    const row = table.querySelector(`.table-row[data-id="${rowId}"]`);
	    if (row) {
	        row.remove();
	    }
    }

    // if table is empty, add .no-data-message with text "No Data Found"
    if (!table.querySelector('.table-row')) {
				const noDataMessage = document.createElement('div');
				noDataMessage.className = 'no-data-message';
				noDataMessage.innerHTML = 'No Data Found';
				table.querySelector('.table-body-container').appendChild(noDataMessage);
		}

    updateCounts();
};

function createAllTables(data) {
    if (document.getElementById('requests-table')) {
        createTable('requests-table', getQueryTableColumns(), data.requests || []);
    }
    if (document.getElementById('sources-table')) {
        createTable('sources-table', getSourceTableColumns(), data.sources || []);
    }
    if (document.getElementById('leads-table')) {
        createTable('leads-table', getLeadTableColumns(), data.leads || []);
    }
    if (document.getElementById('liked-leads-table')) {
        createTable('liked-leads-table', getLikedLeadTableColumns(), data.liked_leads || []);
    }
    updateCounts();
}

function initializeSearches(extra_ids=[]) {
	if (document.getElementById('requests-search')) {
		document.getElementById('requests-search').addEventListener('input', (e) => searchTable('requests-table', e.target.value));
	}
	if (document.getElementById('sources-search')) {
		document.getElementById('sources-search').addEventListener('input', (e) => searchTable('sources-table', e.target.value));
	}
	if (document.getElementById('leads-search')) {
		document.getElementById('leads-search').addEventListener('input', (e) => searchTable('leads-table', e.target.value));
	}
	if (document.getElementById('liked-leads-search')) {
		document.getElementById('liked-leads-search').addEventListener('input', (e) => searchTable('liked-leads-table', e.target.value));
	}

	extra_ids.forEach((id) => {
		if (document.getElementById(`${id}-search`)) {
			document.getElementById(`${id}-search`).addEventListener('input', (e) => searchTable(`${id}-table`, e.target.value));
		}
	});
}

function initializeClicks() {
	document.addEventListener('click', function(event) {
        const target = event.target;
        let clicked_button = false;

        if (target.classList.contains('check-lead-btn')) {
            const leadId = target.getAttribute('data-id');
            console.log('Checking lead with id:', leadId);
            socket.emit('check_lead', { lead_id: leadId });
            target.outerHTML = `<div class="cell-spinner-container"><img src="/static/assets/loadingGears.svg" class="cell-spinner lead-cell-spinner" 	data-id="${leadId}"></div>`;
            clicked_button = true;
        } else if (target.classList.contains('lead-cell-spinner')) {
        	const leadId = target.getAttribute('data-id');
					Swal.fire({
						title: 'Retry Checking Lead?',
						text: 'Do you want to retry checking this lead?',
						icon: 'warning',
						showCancelButton: true,
						confirmButtonText: 'Yes, retry',
						cancelButtonText: 'No, cancel'
					}).then((result) => {
						if (result.isConfirmed) {
							console.log('Checking lead with id:', leadId);
							socket.emit('check_lead', { lead_id: leadId });
							target.outerHTML = `<img src="/static/assets/loadingGears.svg" class="cell-spinner lead-cell-spinner" data-id="${leadId}">`;
							clicked_button = true;
						}
					});
        } else if (target.classList.contains('source-cell-spinner')) {
        	const sourceId = target.getAttribute('data-id');
					Swal.fire({
						title: 'Retry Checking Source?',
						text: 'Do you want to retry checking this source?',
						icon: 'warning',
						showCancelButton: true,
						confirmButtonText: 'Yes, retry',
						cancelButtonText: 'No, cancel'
					}).then((result) => {
						if (result.isConfirmed) {
							console.log('Checking source with id:', sourceId);
							socket.emit('check_lead_source', { lead_source_id: sourceId });
							target.outerHTML = `<img src="/static/assets/loadingGears.svg" class="cell-spinner source-cell-spinner" data-id="${sourceId}">`;
							clicked_button = true;
						}
					});
        } else if (target.classList.contains('liked-lead-btn')) {
            const leadId = target.getAttribute('data-id');
            console.log('Liking lead with id:', leadId);
            socket.emit('liked_lead', { lead_id: leadId });
            target.style.opacity = '0.5';
            clicked_button = true;
        } else if (target.classList.contains('hide-lead-btn')) {
            const leadId = target.getAttribute('data-id');
            console.log('Hiding lead with id:', leadId);
            if (window.confirmHides) {
                Swal.fire({
                    title: 'Are you sure?',
                    text: 'This lead will be hidden from the list.',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonText: 'Yes, hide it',
                    cancelButtonText: 'Cancel',
                    reverseButtons: true
                }).then((result) => {
                    if (result.isConfirmed) {
                        socket.emit('hide_lead', { lead_id: leadId });
                        target.style.opacity = '0.5';
                        clicked_button = true;
                    }
                });
            } else {
                socket.emit('hide_lead', { lead_id: leadId });
                target.style.opacity = '0.5';
                clicked_button = true;
            }
        } else if (target.classList.contains('check-source-btn')) {
            const sourceId = target.getAttribute('data-id');
            console.log('Checking source with id:', sourceId);
            socket.emit('check_lead_source', { lead_source_id: sourceId });
            target.outerHTML = `<div class="cell-spinner-container"><img src="/static/assets/loadingGears.svg" class="cell-spinner source-cell-spinner" data-id="${sourceId}"></div>`;
            clicked_button = true;
        } else if (target.classList.contains('hide-source-btn')) {
            const sourceId = target.getAttribute('data-id');
            console.log('Hiding source with id:', sourceId);
						if (window.confirmHides) {
							Swal.fire({
									title: 'Are you sure?',
									text: 'This source will be hidden from the list.',
									icon: 'warning',
									showCancelButton: true,
									confirmButtonText: 'Yes, hide it',
									cancelButtonText: 'Cancel',
									reverseButtons: true
							}).then((result) => {
									if (result.isConfirmed) {
										socket.emit('hide_source', { source_id: sourceId });
										target.style.opacity = '0.5';
										clicked_button = true;
									}
							});
						} else {
            	socket.emit('hide_source', { source_id: sourceId });
	            target.style.opacity = '0.5';
	            clicked_button = true;
						}
        } else if (target.classList.contains('hide-request-btn')) {
            const requestId = target.getAttribute('data-id');
            console.log('Toggling hide request', requestId);
            if (window.confirmHides) {
             Swal.fire({
                 title: 'Are you sure?',
                 text: 'This request will be hidden from the list.',
                 icon: 'warning',
                 showCancelButton: true,
                 confirmButtonText: 'Yes, hide it',
                 cancelButtonText: 'Cancel',
                 reverseButtons: true
             }).then((result) => {
                 if (result.isConfirmed) {
                     socket.emit('hide_request', { query_id: requestId });
                     target.style.opacity = '0.5';
                     clicked_button = true;
                 }
             });
		        } else {
			        socket.emit('hide_request', { query_id: requestId });
			        target.style.opacity = '0.5';
			        clicked_button = true;
		        }
        } else if (target.classList.contains('unhide-request-btn')) {
            const requestId = target.getAttribute('data-id');
            console.log('unhiding request', requestId);
            if (window.confirmHides) {
             Swal.fire({
                 title: 'Are you sure?',
                 text: 'This request will be unhidden and shown again.',
                 icon: 'warning',
                 showCancelButton: true,
                 confirmButtonText: 'Yes, unhide it',
                 cancelButtonText: 'Cancel',
                 reverseButtons: true
             }).then((result) => {
                 if (result.isConfirmed) {
                     socket.emit('unhide_request', { query_id: requestId });
                     target.style.opacity = '0.5';
                     clicked_button = true;
                 }
             });
		        } else {
			        socket.emit('unhide_request', { query_id: requestId });
			        target.style.opacity = '0.5';
			        clicked_button = true;
		        }
        } else if (target.classList.contains('unhide-source-btn')) {
				    const sourceId = target.getAttribute('data-id');
				    console.log('unhiding source', sourceId);
				    if (window.confirmHides) {
				        Swal.fire({
				            title: 'Are you sure?',
				            text: 'This source will be unhidden and shown again.',
				            icon: 'warning',
				            showCancelButton: true,
				            confirmButtonText: 'Yes, unhide it',
				            cancelButtonText: 'Cancel',
				            reverseButtons: true
				        }).then((result) => {
				            if (result.isConfirmed) {
				                socket.emit('unhide_source', { source_id: sourceId });
				                target.style.opacity = '0.5';
				                clicked_button = true;
				            }
				        });
				    } else {
				        socket.emit('unhide_source', { source_id: sourceId });
				        target.style.opacity = '0.5';
				        clicked_button = true;
				    }
				} else if (target.classList.contains('unhide-lead-btn')) {
				    const leadId = target.getAttribute('data-id');
				    console.log('unhiding lead', leadId);
				    if (window.confirmHides) {
				        Swal.fire({
				            title: 'Are you sure?',
				            text: 'This lead will be unhidden and shown again.',
				            icon: 'warning',
				            showCancelButton: true,
				            confirmButtonText: 'Yes, unhide it',
				            cancelButtonText: 'Cancel',
				            reverseButtons: true
				        }).then((result) => {
				            if (result.isConfirmed) {
				                socket.emit('unhide_lead', { lead_id: leadId });
				                target.style.opacity = '0.5';
				                clicked_button = true;
				            }
				        });
				    } else {
				        socket.emit('unhide_lead', { lead_id: leadId });
				        target.style.opacity = '0.5';
				        clicked_button = true;
				    }
				} else if (event.target.classList.contains('copy-email-btn')) {
            const email = event.target.getAttribute('data-email');
            console.log('Copying email to clipboard:', email);
            navigator.clipboard.writeText(email).then(() => {
                // Optionally, provide some visual feedback
                const originalIcon = event.target.innerHTML;
                event.target.innerHTML = '<i class="fa-solid fa-clipboard-check fa-icon"></i>';
                setTimeout(() => {
                    event.target.innerHTML = originalIcon;
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
            });
            clicked_button = true;
        } else {

		        const cell = event.target.closest('.table-cell:not(.header-cell)');
		        if (cell && !clicked_button) {
		            const row = cell.closest('.table-row');
		            // skip if table-row is a child of `requests-table`
		            const table = cell.closest('.table-container');
		            let tableId = table ? table.id : '';

		            if (tableId === 'requests-table') {
		                return;
		            }

		            tableId = tableId.replace('-table', '');
		            if (row) {
		                // Contract all other expanded rows
		                document.querySelectorAll('.table-row.expanded').forEach(expandedRow => {
		                    if (expandedRow !== row) {
		                        expandedRow.classList.remove('expanded');
		                        expandedRow.style.height = '';
		                        expandedRow.querySelectorAll('.table-cell').forEach(expandedCell => {
		                            expandedCell.style.whiteSpace = 'nowrap';
		                            expandedCell.style.overflow = 'hidden';
		                            expandedCell.style.textOverflow = 'ellipsis';
		                        });
		                    }
		                });

		                if (row.classList.contains('expanded')) {
		                    row.classList.remove('expanded');
		                    if (row.classList.contains('table-row-selected')) {
													row.classList.remove('table-row-selected');
		                    } else {
		                    	row.classList.add('table-row-selected');
		                    }
		                    updateSelectedCount(tableId);
		                } else {
		                    row.classList.toggle('expanded');
		                    if (row.classList.contains('expanded')) {
		                        row.style.height = 'auto';
		                        row.querySelectorAll('.table-cell').forEach(cell => {
		                            cell.style.whiteSpace = 'normal';
		                            cell.style.overflow = 'visible';
		                            cell.style.textOverflow = 'clip';
		                        });
		                    } else {
		                        row.style.height = '';
		                        row.querySelectorAll('.table-cell').forEach(cell => {
		                            cell.style.whiteSpace = 'nowrap';
		                            cell.style.overflow = 'hidden';
		                            cell.style.textOverflow = 'ellipsis';
		                        });
		                    }
		                }
		            }
		        }

        }

    });
}

function initializeSelectAll(extra_tables=[]) {
		let tables = ['requests', 'sources', 'leads', 'liked-leads'];
		tables = tables.concat(extra_tables);


    tables.forEach(tableId => {
    		console.log(`Setting up ${tableId}`);
        const selectAllCheckbox = document.getElementById(`${tableId}-select-all`);
        const dropdownMenu = document.querySelector(`#${tableId}-dropdown + .dropdown-menu`);
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
            const rows = Array.from(document.querySelectorAll(`#${tableId}-table .table-row:not(.table-header)`))
                .filter(row => row.style.display !== 'none');
            rows.forEach(row => {
                row.classList.toggle('table-row-selected', this.checked);
            });
                updateSelectedCount(tableId);
            });
        }

        if (dropdownMenu) {
            dropdownMenu.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                let clicked_button = false;

                if (e.target.classList.contains('select-all')) {
                    selectAllRows(tableId);
                    clicked_button = true;
                } else if (e.target.classList.contains('unselect-all')) {
                    unselectAllRows(tableId);
                    clicked_button = true;
                } else if (e.target.classList.contains('select-unchecked')) {
                    unselectAllRows(tableId);
                		selectUncheckedRows(tableId);
                    clicked_button = true;
                } else if (e.target.classList.contains('select-checked')) {
                    unselectAllRows(tableId);
                		selectCheckedRows(tableId);
                    clicked_button = true;
                } else if (e.target.classList.contains('select-invalid')) {
                    unselectAllRows(tableId);
                    selectInvalidRows(tableId);
                    clicked_button = true;
                } else if (e.target.classList.contains('check-all')) {
                    checkAllSelected(tableId);
                    clicked_button = true;
                } else if (e.target.classList.contains('hide-all')) {
                    hideAllSelected(tableId);
                    clicked_button = true;
                } else if (e.target.classList.contains('export-csv')) {
                    exportToCSV(tableId);
                    clicked_button = true;
                } else if (e.target.classList.contains('unhide-all')) {
                    unhideAllSelected(tableId);
                    clicked_button = true;
                }
                updateSelectedCount(tableId);

                if (clicked_button) {
                	// close the menu
										dropdownMenu.classList.remove('show');
                }
            });
        }
    });
}

function selectAllRows(tableId) {
	const rows = Array.from(document.querySelectorAll(`#${tableId}-table .table-row:not(.table-header)`))
					.filter(row => row.style.display !== 'none');
    rows.forEach(row => row.classList.add('table-row-selected'));
    document.getElementById(`${tableId}-select-all`).checked = true;
}

function unselectAllRows(tableId) {
    const rows = document.querySelectorAll(`#${tableId}-table .table-row:not(.table-header)`);
    rows.forEach(row => row.classList.remove('table-row-selected'));
    document.getElementById(`${tableId}-select-all`).checked = false;
}

function selectUncheckedRows(tableId) {
	const rows = Array.from(document.querySelectorAll(`#${tableId}-table .table-row:not(.table-header)`))
																	.filter(row => row.style.display !== 'none');
    rows.forEach(row => {
        if (row.classList.contains('unchecked-table-row')) {
            row.classList.add('table-row-selected');
        }
    });
}

function selectCheckedRows(tableId) {
	const rows = Array.from(document.querySelectorAll(`#${tableId}-table .table-row:not(.table-header)`))
																	.filter(row => row.style.display !== 'none');
    rows.forEach(row => {
    if (row.classList.contains('valid-table-row') || row.classList.contains('contactable-table-row')) {
        row.classList.add('table-row-selected');
    }
    });
}

function selectInvalidRows(tableId) {
		const rows = Array.from(document.querySelectorAll(`#${tableId}-table .table-row:not(.table-header)`))
																			.filter(row => row.style.display !== 'none');
    rows.forEach(row => {
        if (row.classList.contains('invalid-table-row')) {
            row.classList.add('table-row-selected');
        }
    });
}

function checkAllSelected(tableId) {
    const rows = Array.from(document.querySelectorAll(`#${tableId}-table .table-row.table-row-selected:not(.table-header)`))
                      .filter(row => row.style.display !== 'none');
    let emitCount = 0;
    rows.forEach(row => {
        const checkButton = row.querySelector('.check-lead-btn, .check-source-btn');
        if (checkButton) {
            const id = checkButton.getAttribute('data-id');
            console.log(`Checking ${tableId} with id:`, id);
            if (tableId.includes('leads')) {
                socket.emit('check_lead', { lead_id: id });
                emitCount++;
                checkButton.outerHTML = `<div class="cell-spinner-container"><img src="/static/assets/loadingGears.svg" class="cell-spinner lead-cell-spinner" data-id="${id}"></div>`;
            } else if (tableId.includes('sources')) {
                socket.emit('check_lead_source', { lead_source_id: id });
                emitCount++;
                checkButton.outerHTML = `<div class="cell-spinner-container"><img src="/static/assets/loadingGears.svg" class="cell-spinner source-cell-spinner" data-id="${id}"></div>`;
            }
        }
    });
    if (emitCount > 0) {
        iziToast.info({
            title: 'Queued',
            message: `${emitCount} ${emitCount === 1 ? 'item' : 'items'} queued to be checked`,
            position: 'topRight',
            timeout: 5000
        });
    } else {
        iziToast.info({
            title: 'No Items Queued',
            message: `0 items queued to be checked`,
            position: 'topRight',
            timeout: 5000
        });

    }
    unselectAllRows(tableId);
}

function hideAllSelected(tableId) {
		const rows = Array.from(document.querySelectorAll(`#${tableId}-table .table-row.table-row-selected:not(.table-header)`))
																			.filter(row => row.style.display !== 'none');
    const idsToHide = [];
    let emitCount = 0;
    rows.forEach(row => {
        const id = row.getAttribute('data-id');
        idsToHide.push(id);
        if (tableId === 'leads' || tableId === 'liked-leads') {
            console.log('Hiding lead with id:', id);
            socket.emit('hide_lead', { lead_id: id });
            emitCount++;
        } else if (tableId === 'sources') {
            console.log('Hiding source with id:', id);
            socket.emit('hide_source', { source_id: id });
            emitCount++;
        } else if (tableId === 'requests') {
            console.log('Hiding request with id:', id);
            socket.emit('hide_request', { query_id: id });
            emitCount++;
        }
    });
    // Remove hidden rows from the table
    rows.forEach(row => row.remove());

    if (emitCount > 0) {
        iziToast.info({
            title: 'Hidden',
            message: `${emitCount} ${emitCount === 1 ? 'item' : 'items'} hidden`,
            position: 'topRight',
            timeout: 5000
        });
    } else {
			iziToast.info({
				title: 'No Items Hidden',
				message: `0 items hidden`,
				position: 'topRight',
				timeout: 5000
			});
    }
    updateCounts();
    unselectAllRows(tableId);
}

function updateSelectedCount(tableId) {
    const selectedRows = document.querySelectorAll(`#${tableId}-table .table-row.table-row-selected:not(.table-header)`);
    const countElement = document.getElementById(`${tableId}-selected-count`);
    if (countElement) {
        countElement.textContent = selectedRows.length > 0 ? `${selectedRows.length} selected` : '';
    }
}

function exportToCSV(tableId) {
    const selectedRows = document.querySelectorAll(`#${tableId}-table .table-row.table-row-selected:not(.table-header)`);
    if (selectedRows.length === 0) {
        alert('Please select at least one row to export.');
        return;
    }

    const headerRow = document.querySelector(`#${tableId}-table .table-header`);
    const headers = Array.from(headerRow.querySelectorAll('.table-cell'))
        .map(cell => cell.textContent.trim())
        .filter(header => !['Checked', 'Like', 'Hide'].includes(header));

    // Add separate headers for contact info and contact page
    const contactIndex = headers.indexOf('Contact');
    if (contactIndex !== -1) {
        headers.splice(contactIndex, 1, 'Contact Info', 'Contact Page');
    }

    let csvContent = headers.join(',') + '\n';

    selectedRows.forEach(row => {
        let rowData = Array.from(row.querySelectorAll('.table-cell'))
            .map((cell, index) => {
                if (['Checked', 'Like', 'Hide'].includes(headerRow.children[index].textContent.trim())) {
                    return null; // Skip these columns
                }

                let content = cell.textContent.trim();

                // Handle the contact column
                if (headerRow.children[index].textContent.trim() === 'Contact') {
                    const contactInfo = cell.querySelector('div:first-child').textContent.trim();
                    const contactPageLink = cell.querySelector('a');
                    const contactPage = contactPageLink ? contactPageLink.href : '';
                    return [contactInfo, contactPage];
                }

                // Escape commas and quotes
                content = content.replace(/"/g, '""');
                if (content.includes(',') || content.includes('"') || content.includes('\n')) {
                    content = `"${content}"`;
                }
                return content;
            })
            .filter(content => content !== null); // Remove skipped columns

        // Flatten the array in case of split contact info
        rowData = rowData.flat();

        csvContent += rowData.join(',') + '\n';
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `${tableId}_export.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function unhideAllSelected(tableId) {
    const rows = Array.from(document.querySelectorAll(`#${tableId}-table .table-row.table-row-selected:not(.table-header)`))
                            .filter(row => row.style.display !== 'none');
    const idsToUnhide = [];
    let emitCount = 0;
    rows.forEach(row => {
        const id = row.getAttribute('data-id');
        idsToUnhide.push(id);
        if (tableId === 'requests') {
            console.log('Unhiding request with id:', id);
            socket.emit('unhide_request', { query_id: id });
            emitCount++;
        }
    });

    if (emitCount > 0) {
        iziToast.info({
            title: 'Unhidden',
            message: `${emitCount} ${emitCount === 1 ? 'request' : 'requests'} unhidden`,
            position: 'topRight',
            timeout: 5000
        });
    } else {
        iziToast.info({
            title: 'No Requests Unhidden',
            message: `0 requests unhidden`,
            position: 'topRight',
            timeout: 5000
        });
    }

    // Remove unhidden rows from the table
    rows.forEach(row => row.classList.remove('table-row-selected'));
    updateSelectedCount(tableId);
}

export {
	dataCache,
	updateCounts,
	searchTable,
	sortTable,
	getSourceTableColumns,
	getLeadTableColumns,
	getLikedLeadTableColumns,
	getQueryTableColumns,
	createTable,
	updateRow,
	addRow,
	handleHideEvent,
	createAllTables,
	initializeSearches,
	initializeClicks,
	initializeSelectAll
};
