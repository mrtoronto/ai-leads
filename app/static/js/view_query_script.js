import { socket, fetchData } from "./socket.js";
import {
    createTable,
    initializeClicks,
    initializeSearches,
    initializeSelectAll,
    getLeadTableColumns,
    updateCounts,
    getSourceTableColumns
} from "./general_script.js";
import { handleLeadEvents, handleSourceEvents, handleRequestEvents, handleQueryCardUpdate } from "./socket_handlers.js";
import { createQueryDetailsComponent, createTableComponent, createSourceStatusBar } from "./components.js";

let cachedData = null;

document.addEventListener('DOMContentLoaded', function() {
    const queryId = parseInt(document.getElementById('query-id').value, 10);

    document.getElementById('query-leads-table-container').innerHTML = createTableComponent(
        'Leads from Query', 'query-leads',
        ['select-all', 'unselect-all', 'select-checked', 'select-unchecked', 'select-invalid','', 'check-all', 'hide-all', 'export-csv']
    );

    const container = document.querySelector('#query-sources-status-bar-container');
    container.innerHTML = createSourceStatusBar();

    const checkedSourcesBar = document.getElementById('checked-sources-bar');
    const inProgressSourcesBar = document.getElementById('in-progress-sources-bar');
    const uncheckedSourcesBar = document.getElementById('unchecked-sources-bar');
    const sourceProgressCounter = document.getElementById('source-progress-counter');

    function updateProgressBar() {
        const totalSources = cachedData.lead_sources.length;
        const checkedSources = cachedData.lead_sources.filter(source => source.checked).length;
        const inProgressSources = cachedData.lead_sources.filter(source => source.checking).length;
        const uncheckedSources = totalSources - checkedSources - inProgressSources;

        const checkedPercentage = (checkedSources / totalSources) * 100;
        const inProgressPercentage = (inProgressSources / totalSources) * 100;
        const uncheckedPercentage = (uncheckedSources / totalSources) * 100;

        checkedSourcesBar.style.width = `${checkedPercentage}%`;
        inProgressSourcesBar.style.width = `${inProgressPercentage}%`;
        uncheckedSourcesBar.style.width = `${uncheckedPercentage}%`;

        if (inProgressSources > 0) {
            sourceProgressCounter.innerHTML = `<b>Scanned</b>: ${checkedSources} / ${totalSources} (${inProgressSources} <span class="spinner-border spinner-border-sm ms-1" role="status" aria-hidden="true"></span>) <i class="fa-solid fa-circle-question" style="margin-left: auto; margin-right: 1em;" data-bs-toggle="tooltip" data-bs-placement="top" title="Number of scanned sources / Number of total sources found (number of sources being scanned)"></i>`;
        } else {
            sourceProgressCounter.innerHTML = `<b>Scanned</b>: ${checkedSources} / ${totalSources} <i class="fa-solid fa-circle-question" style="margin-left: auto; margin-right: 1em;" data-bs-toggle="tooltip" data-bs-placement="top" title="Number of scanned sources / Number of total sources found"></i>`;
        }

        // Reinitialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl)
        });
    }

    fetchData({'query_id': queryId}).then(data => {
        cachedData = data;
        var query_container = document.querySelector('.query-container');
        query_container.innerHTML = createQueryDetailsComponent(data.query);

        updateProgressBar();

        createTable('query-leads-table', getLeadTableColumns(), data.leads.filter(request => !request.hidden));

        initializeClicks();
        initializeSearches(['query-leads']);
        initializeSelectAll(['query-leads']);
        updateCounts();
    });

    document.getElementById('check-10-sources').addEventListener('click', () => checkSources(10));
    document.getElementById('check-50-sources').addEventListener('click', () => checkSources(50));
    document.getElementById('check-100-sources').addEventListener('click', () => checkSources(100));
    document.getElementById('check-all-sources').addEventListener('click', () => checkSources('all'));

    function checkSources(count) {
        if (!cachedData) return;

        let sourcesToCheck = cachedData.lead_sources.filter(source => !source.checked && !source.checking);
        if (count !== 'all') {
            sourcesToCheck = sourcesToCheck.slice(0, count);
        }
        sourcesToCheck.forEach(source => {
            source.checking = true;
            // update source in cachedData
            const index = cachedData.lead_sources.indexOf(source);
            if (index !== -1) {
                cachedData.lead_sources[index].checking = true;
            }
        });
        
        updateProgressBar();
        
        sourcesToCheck.forEach(source => {
            socket.emit('check_lead_source', { lead_source_id: source.id });
        });

        iziToast.info({
            title: 'Queued',
            message: `${sourcesToCheck.length} ${sourcesToCheck.length === 1 ? 'source' : 'sources'} queued to be checked`,
            position: 'topRight',
            timeout: 5000
        });
    }

    socket.on('sources_updated', (data) => {
        data.sources.forEach(source => {
            if (source.query_id !== queryId) {
                return;
            }
            const index = cachedData.lead_sources.findIndex(s => s.id === source.id);
            if (index !== -1) {
                cachedData.lead_sources[index] = source;
            } else {
                cachedData.lead_sources.push(source);
            }
        });
        updateProgressBar();
    });

    handleQueryCardUpdate('.query-container', queryId);
    handleLeadEvents('query-leads', queryId);
    handleSourceEvents('query-sources', queryId);
});
