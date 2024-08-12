const options = {
    debug: true,
    path: '/socket.io',
    transports: ['websocket'],
    upgrade: true,
};

socket = io(options);

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('settings-form');

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        const industry = document.getElementById('industry').value;
        const pref_org_size = document.getElementById('preferred_org_size').value;
        const description = document.getElementById('user-description').value;
        const searchModelPreference = document.getElementById('search-model-preference').value;
        const sourceCollectionModelPreference = document.getElementById('source-collection-model-preference').value;
        const leadValidationModelPreference = document.getElementById('lead-validation-model-preference').value;
        const credits = document.getElementById('credits').value;

        const settingsData = {
            user_description: description,
            search_model_preference: searchModelPreference,
            source_collection_model_preference: sourceCollectionModelPreference,
            lead_validation_model_preference: leadValidationModelPreference,
            industry: industry,
            preferred_org_size: pref_org_size,
            credits: credits

        };

			socket.emit('update_user_settings', settingsData);

			socket.on('update_user_settings_response', function(response) {
            if (response.success) {
                alert('Settings updated successfully!');
            } else {
                alert('There was an error updating your settings.');
            }
        });
    });
});
