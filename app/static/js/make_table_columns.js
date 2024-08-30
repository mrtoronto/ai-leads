let getQueryTableColumns;
let getLeadTableColumns;
let getSourceTableColumns;



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
								<img src="${imageUrl}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
							</a>
						</div>
		        <div style="display: flex; flex-direction: column; overflow: hidden;text-overflow: ellipsis;white-space: nowrap;">
		        	<a href="/lead/${row.guid}" class="lead-name" data-id="${row.id}" style="${style}">${content}</a>
		         	<a href="${row.base_url}" target="_blank" style="${linkStyle}">${row.base_url}</a>
							<div style="${linkStyle}; margin-top: 0.25em;" class="lead-description">${row.description}</div>
		        </div>
					</div>`
        : `<div style="${containerStyle}">
          	<div style="min-width: 50px">
							<a href="${imageLink}"  target="_blank" style="min-width: 50px">
								<img src="${imageUrl}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
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
												<img src="${imageUrl}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
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
												<img src="${imageUrl}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
											</a>
										</div>
										<div style="display: flex; flex-direction: column; width: 100%; overflow: hidden;text-overflow: ellipsis;white-space: nowrap;">
											<a class="name-url" href="${row.url}" target="_blank" style="${style}">${content}</a>
										</div>
									</div>
							</div>`;
}

getQueryTableColumns = () => [
    { id: 'id', name: 'ID', field: 'id', hidden: true },
    { id: 'user_query', textAlign: 'left', justifyContent: 'flex-start', width: '400px', name: 'User Query', field: 'user_query', formatter: (cell, row) => `
        <div>
            <a href="/query/${row.guid}" data-id="${row.id}">${cell}</a>
            <div style="font-size: 0.8em; color: #888;">${new Date(row.created_at).toLocaleString()}</div>
        </div>
    ` },
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

getSourceTableColumns = () => [
    { id: 'id', name: 'ID', field: 'id', hidden: true },
    { id: 'checking', name: 'Checking', field: 'checking', hidden: true },
    {
        id: 'name',
        width: '70%',
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
															<img src="${imageUrl}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
														</a>
													</div>
													<div style="display: flex; flex-direction: column; overflow: hidden;text-overflow: ellipsis;white-space: nowrap;">
													<a href="/source/${row.guid}" class="source-name" data-id="${row.id}" style="${style}">${content}</a>
													<a href="${row.url}" target="_blank" style="${linkStyle}">${row.url}</a>
													<div class="source-description" style="font-size: 12px; margin-top: 0.25em; overflow-wrap: break-word; word-wrap: break-word;">${row.description || "---"}</div>
													</div>
										</div>`
									: `<div style="${containerStyle}; display: flex; align-items: center;">
												<div style="display: flex; flex-direction: column; overflow: hidden;text-overflow: ellipsis;white-space: nowrap; min-width: 50px">
													<a href="${imageLink}"  target="_blank">
														<img src="${imageUrl}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
													</a>
												</div>
												<a href="${row.url}" target="_blank" style="${style}" class="name-url">${content}</a>
										</div>`;
        }
    },
    // { id: 'description', whiteSpace: 'wrap !important', width: '300px',  name: 'Description', field: 'description', formatter: (cell) => `<div style="font-size: 12px; max-width: 250px; overflow-wrap: break-word; word-wrap: break-word;">${cell || "---"}</div>` },
    { id: 'n_leads', width: '90px', name: '# of Leads', field: 'n_leads' },
    {
        id: 'actions',
        width: '120px',
        name: 'Actions',
        field: 'actions',
        formatter: (cell, row) => {
            if (row.checking) {
                return `<div class="actions-container">
                            <div class="cell-spinner-container">
                            	<img src="/static/assets/loadingGears.svg" class="cell-spinner source-cell-spinner" data-id="${row.id}">
	                            <div class="queue-circle">
	                                ${row.place_in_queue}
	                            </div>
                             </div>
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


getLeadTableColumns = () => [
    { id: 'id', name: 'ID', field: 'id', hidden: true },
    { id: 'checking', name: 'Checking', field: 'checking', hidden: true },
    {
        id: 'name', maxWidth: '70%', textAlign: 'left !important', name: 'Name', field: 'name', formatter: (cell, row) => desktopLeadNameFormatter(cell, row)
    },
    {
        id: 'contact',
        width: 'fit-content',
        marginLeft: 'auto',
        textAlign: 'right',
        name: 'Contact',
        field: 'contact',
        formatter: (cell, row) => {
            const contactInfo = row.contact_info || '---';
            const contactPage = row.contact_page ? `<a href="${row.contact_page}" target="_blank" style="text-decoration: none;">Contact Page</a>` : '---';

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
                contactInfoHtml = `<div style="font-size: 12px; margin-left: auto;text-decoration: none;">${contactInfo}</div>`;
            }

            return `
                ${contactInfoHtml}
                <div style="font-size: 12px; margin-left: auto;font-weight: bold;text-decoration: none;">${contactPage}</div>
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
		                        <div class="cell-spinner-container">
															<img src="/static/assets/loadingGears.svg" class="cell-spinner lead-cell-spinner" data-id="${row.id}">
															<div class="queue-circle">
								                  ${row.place_in_queue}
								              </div>
														</div>
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
		{ id: 'user_query', textAlign: "left", name: 'User Query', field: 'user_query', formatter: (cell, row) => `<a href="/query/${row.guid}" data-id="${row.id}">${cell}</a>` },
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
																<img src="${imageUrl}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
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
																<img src="${imageUrl}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; opacity: 0.8">
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
                                <div class="cell-spinner-container">
	                                <img src="/static/assets/loadingGears.svg" class="cell-spinner source-cell-spinner"  data-id="${row.id}">
	                                <div class="queue-circle">
										                  ${row.place_in_queue}
										              </div>
                                </div>
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
																	contactInfoHtml = `<div style="font-size: 12px; text-align: center;">${row.contact_info}</div>`;
													}
													let contactPageHtml = '';
													if (row.contact_page) {
														contactPageHtml = `<div style="font-size: 12px;text-align: center;"><a href="${row.contact_page}" target="_blank">Contact Page</a></div>`;
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
					                        <div class="cell-spinner-container">
																		<img src="/static/assets/loadingGears.svg" class="cell-spinner lead-cell-spinner" data-id="${row.id}">
																		<div class="queue-circle">
											                  ${row.place_in_queue}
											              </div>
																	</div>
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


export { getLeadTableColumns, getLikedLeadTableColumns, getQueryTableColumns, getSourceTableColumns };
