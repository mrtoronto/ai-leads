import { socket } from './socket.js';

let allJourneys = [];
let displayedJourneys = [];
let currentOffset = 0;
const pageSize = 50;
let currentQuery = '';
let durationFilter = '';
let loggedInOnly = window.logged_in_only;

const journeyTableBody = document.getElementById('journey_table_body');
const loadMoreButton = document.getElementById('load_more');
const searchBar = document.getElementById('search-bar');
const durationFilterInput = document.getElementById('duration-filter');

function createRow(label, value) {
    const row = document.createElement('tr');
    row.innerHTML = `<td><strong>${label}:</strong> ${value}</td>`;
    return row;
}

function createJourneyLog(journey) {
    const journeyFragment = document.createDocumentFragment();

    if (journey.id !== null) journeyFragment.appendChild(createRow('Journey ID', journey.id));
    if (journey.guid !== null) journeyFragment.appendChild(createRow('GUID', journey.guid));
    if (journey._type != null) journeyFragment.appendChild(createRow('Type', journey._type));
    if (journey.created_at !== null) journeyFragment.appendChild(createRow('Created At', new Date(journey.created_at).toLocaleString()));
    if (journey.user_id !== null) journeyFragment.appendChild(createRow('User ID', journey.user_id));
    if (journey.user_hash !== null) journeyFragment.appendChild(createRow('User Hash', journey.user_hash));
    if (journey.location !== null) journeyFragment.appendChild(createRow('Location', journey.location));
    if (journey.endpoint !== null) journeyFragment.appendChild(createRow('Endpoint', journey.endpoint));
    if (journey.referrer !== null) journeyFragment.appendChild(createRow('Referrer', journey.referrer));
    if (journey.user_agent !== null) journeyFragment.appendChild(createRow('User Agent', journey.user_agent));

    const separatorRow = document.createElement('tr');
    separatorRow.innerHTML = '<td colspan="2"><hr style="border: 0; border-top: 1px solid #ccc;"></td>';
    journeyFragment.appendChild(separatorRow);

    return journeyFragment;
}

function appendRows(records) {
    records.forEach(record => {
        const journeyLogContainer = document.createElement('tbody');
        journeyLogContainer.classList.add('journey-log');
        journeyLogContainer.appendChild(createJourneyLog(record));
        journeyTableBody.appendChild(journeyLogContainer);
    });
}

function filterJourneys() {
    displayedJourneys = allJourneys.filter(journey => {
        const matchesQuery = currentQuery === '' || Object.values(journey).some(value =>
            String(value).toLowerCase().includes(currentQuery.toLowerCase())
        );
        const matchesDuration = durationFilter === '' || journey.duration >= parseFloat(durationFilter);
        const matchesLoggedIn = !loggedInOnly || journey.user_id !== null;
        return matchesQuery && matchesDuration && matchesLoggedIn;
    });
    currentOffset = 0;
    journeyTableBody.innerHTML = '';
    loadMore();
}

function loadMore() {
    const journeysToDisplay = displayedJourneys.slice(currentOffset, currentOffset + pageSize);
    appendRows(journeysToDisplay);
    currentOffset += journeysToDisplay.length;
    loadMoreButton.style.display = currentOffset >= displayedJourneys.length ? 'none' : 'block';
}

export function initJourneyScript() {

    socket.emit('get_all_journeys', { logged_in_only: loggedInOnly, user_id: window.user_id });

    socket.on('all_journeys_response', function(data) {
        if (data.status === "success") {
            allJourneys = data.records;
            filterJourneys();
        }
    });

    loadMoreButton.addEventListener('click', loadMore);

    searchBar.addEventListener('input', (event) => {
        currentQuery = event.target.value;
        filterJourneys();
    });

    durationFilterInput.addEventListener('input', (event) => {
        durationFilter = event.target.value;
        filterJourneys();
    });
}
