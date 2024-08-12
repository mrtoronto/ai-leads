document.addEventListener('DOMContentLoaded', function () {
    // Display any flashed messages from the server
    console.log(window.flash_messages);
    if (window.flash_messages) {
        window.flash_messages.forEach(function(flash) {
            const category = flash[0];
            const messageText = flash[1];
            if (category === 'warning') {
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

}, true);
