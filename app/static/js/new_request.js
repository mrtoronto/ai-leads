$(document).ready(function () {
	if (document.querySelector('#lead-form')) {
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
	}

});
