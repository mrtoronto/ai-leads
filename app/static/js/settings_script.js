const options = {
    debug: true,
    path: '/socket.io',
    transports: ['websocket'],
    upgrade: true,
};

socket = io(options);

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('settings-form');
    const emailForm = document.getElementById('settings-email-form');
    const emailInput = document.getElementById('email');
    const resendVerificationBtn = document.getElementById('resend-verification-email');
    const resendPasswordResetBtn = document.getElementById('resend-password-reset-email');

    let emailTimeout;

    emailInput.addEventListener('input', function() {
        clearTimeout(emailTimeout); // Clearing the previous timeout
        const emailFeedback = document.getElementById('email-feedback');
        const emailSpinner = document.getElementById('email-spinner');
        const emailSuccess = document.getElementById('email-success');
        const emailError = document.getElementById('email-error');

        emailSpinner.classList.remove('d-none');
        emailSuccess.classList.add('d-none');
        emailError.classList.add('d-none');

        if (emailInput.value.includes('@')) {
            emailTimeout = setTimeout(() => {
                const email = emailInput.value;
                socket.emit('check_email_availability', { email });

                socket.on('email_check_response', function(response) {
                    emailSpinner.classList.add('d-none');
                    if (response.available) {
                        emailSuccess.classList.remove('d-none');
                    } else {
                        emailError.classList.remove('d-none');
                    }
                });
            }, 2000); // 2 second delay
        } else {
            emailSpinner.classList.add('d-none');
        }
    });

		emailForm.addEventListener('submit', function (event) {
			event.preventDefault();
			const email = emailInput.value;

			socket.emit('update_email', { email: email });

			socket.on('email_updated', function (response) {
				if (response.success) {
					console.log('Email updated successfully!')
					Swal.fire({
						icon: 'success',
						title: 'Success',
						text: 'Email updated successfully!',
					});
				} else {
					console.log('Email updated faiuled!')
					Swal.fire({
						icon: 'error',
						title: 'Error',
						text: response.message,
					});
				}
			});
		});

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        const industry = document.getElementById('industry').value;
        const pref_org_size = document.getElementById('preferred_org_size').value;
        const description = document.getElementById('user-description').value;
        const searchModelPreference = document.getElementById('search-model-preference').value;
        const sourceCollectionModelPreference = document.getElementById('source-collection-model-preference').value;
        const leadValidationModelPreference = document.getElementById('lead-validation-model-preference').value;

        const settingsData = {
            user_description: description,
            search_model_preference: searchModelPreference,
            source_collection_model_preference: sourceCollectionModelPreference,
            lead_validation_model_preference: leadValidationModelPreference,
            email: email,
            industry: industry,
            preferred_org_size: pref_org_size
        };

        socket.emit('update_user_settings', settingsData);

        socket.on('update_user_settings_response', function(response) {
            if (response.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Success',
                    text: 'Settings updated successfully!',
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'There was an error updating your settings.',
                });
            }
        });
    });

    if (resendVerificationBtn) {
        resendVerificationBtn.addEventListener('click', function(event) {
            event.preventDefault();
            fetch('/send_verification_email', { method: 'POST' })
                .then(response => {
                if (response.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Success',
                        text: 'Verification email sent successfully!',
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'There was an error sending the verification email.',
                    });
                }
                });
        });
    }

    if (resendPasswordResetBtn) {
        resendPasswordResetBtn.addEventListener('click', function(event) {
            event.preventDefault();
            fetch('/password_reset_request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: window.current_user_email })
            }).then(response => {
            if (response.ok) {
                Swal.fire({
                    icon: 'success',
                    title: 'Success',
                    text: 'Password reset email sent successfully!',
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'There was an error sending the password reset email.',
                });
            }
            });
        });
    }
});
