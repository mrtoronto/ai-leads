document.addEventListener('DOMContentLoaded', function () {
    // Display any flashed messages from the server
    if (window.flash_messages) {
        window.flash_messages.forEach(function(flash) {
            const category = flash[0];
            const messageText = flash[1];
            if ((category === 'warning') || (category === 'error') || (category === 'danger')) {
                iziToast.warning({
                    title: 'Warning',
                    message: messageText,
                    position: 'topRight',
                    timeout: 0
                });
            } else {
                iziToast.show({
                    title: 'Notice',
                    message: messageText,
                    position: 'bottomRight',
                    timeout: 5000
                });
            }
        });
    }

    // Additional conditions that may trigger toasts
    if (window.isBanned) {
        // Example message for a banned user, update as necessary
        iziToast.warning({
            title: 'Warning',
            message: 'You have been banned. If you believe this is an error, please contact us.',
            position: 'bottomRight'
        });
    }
    if (!window.is_verified && window.is_auth) {
        // Example message for a banned user, update as necessary
        iziToast.warning({
            title: 'Warning',
            message: 'Verify your email for <b>5,000 free credits</b>! <a href="/send_verification_email" style="text-decoration: none; font-weight: bold;">Verify Email</a>',
            position: 'bottomRight',
            timeout: 0
        });
    }

}, true);
