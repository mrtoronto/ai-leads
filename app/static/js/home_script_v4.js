document.addEventListener('DOMContentLoaded', function() {
		console.log(window.is_mobile);


    // document.getElementById('retrain-model-btn').addEventListener('click', function() {
    //   // can you make the button disabled and a spinner
    //   $('#retrain-model-btn').prop('disabled', true);
    //   $('#retrain-model-btn').html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Retraining...');
    // 	socket.emit('retrain_model');
    // });

    // socket.on('model_retrained', function(data) {
    //     $('#retrain-model-btn').prop('disabled', false);
    //     $('#retrain-model-btn').html('Retrain Model');
    //     if (data.trained_at) {
    //         $('#last-trained-time').text(`Last trained: ${new Date(data.trained_at).toLocaleString()}`);
    //     }
    // });

    // Add event listeners for forms and buttons
    // document.getElementById('create-lead-source-form').addEventListener('submit', function(event) {
    //     event.preventDefault();
    //     const url = document.getElementById('lead-source-url').value;
    //     socket.emit('create_lead_source', { url });
    //     document.getElementById('lead-source-url').value = '';
    // });

    // Toggle Lead Source Form
    // document.getElementById('toggle-lead-source-form').addEventListener('click', function() {
    //     const formContainer = document.getElementById('lead-source-form-container');
    //     formContainer.style.display = (formContainer.style.display === 'none' || formContainer.style.display === '') ? 'block' : 'none';
    // });

    // document.getElementById('toggle-lead-form').addEventListener('click', function() {
    //     const formContainer = document.getElementById('lead-form-container');
    //     formContainer.style.display = (formContainer.style.display === 'none' || formContainer.style.display === '') ? 'block' : 'none';
    // });

    // document.getElementById('create-lead-form').addEventListener('submit', function(event) {
    //     event.preventDefault();
    //     const url = document.getElementById('lead-url').value;
    //     socket.emit('create_lead', { url });
    //     document.getElementById('lead-url').value = '';
    // });


    document.querySelector('#lead-form').addEventListener('submit', function (event) {
        event.preventDefault();
        const query = document.querySelector('#query').value;

        if ((query === '') || (query === null) || (query === undefined) || (query.trim() === '')) {
						Swal.fire({
								icon: 'error',
								title: 'Error',
								text: 'Enter a query to search for!',
								showConfirmButton: true,
								confirmButtonText: 'OK',
								confirmButtonColor: '#3E8CFF'
						});
						return;
				}

        fetch("/submit_request", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        }).then(response => response.json())
          .then(data => {
              if (data.message) {
                Swal.fire({
                    icon: 'success',
                    title: 'Success',
                    text: data.message,
                    showConfirmButton: true,
                    confirmButtonText: 'Go to Query',
                    confirmButtonColor: '#3E8CFF'
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.href = `/query/${data.guid}`;
                    }
                });
              }
          }).catch((error) => {
              console.error('Error:', error);
          });
    });

});
