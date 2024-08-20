import { CountUp } from "/static/js/countUp.min.js";
let socket;
let fetchData;

import { updateRow } from "/static/js/general_script.js";

function initializeSocket() {
	const options = {
		debug: true,
		path: '/socket.io',
		transports: ['websocket'],
		upgrade: true,
	};

	socket = io(options);

	socket.on('credit_error', function (data) {
		let toast_class;
		    	if (data.lead) {
			updateRow('leads-table', data.lead.id, data.lead);
			toast_class = 'credit-lead-error-toast';
		} else if (data.source) {

			updateRow('sources-table', data.source.id, data.source);
			toast_class = 'credit-source-error-toast';
		} else if (data.request) {
			updateRow('requests-table', data.request.id, data.request);
			toast_class = 'credit-request-error-toast';
		}

		    	if ($(`.${toast_class}`).length == 0) {
			iziToast.warning({
		      title: 'Warning',
		      message: data.message,
		      class: toast_class,
		      position: 'topRight',
		      timeout: 10000
		    });
		}

  });

	socket.on('update_credits', function (data) {
    console.log(data);

    // Get the current value of the credit counter
    const currentValue = parseInt($('#creditValue').text().replace(/[^0-9.-]+/g, ""), 10);

		if (data.credits > currentValue) {
			return;
		}

    // Create a new CountUp instance
    const countUp = new CountUp(
    		'creditValue',
       	data.credits,
        {
        		duration: 4,
        		startVal: currentValue,
          	decimalPlaces: 0,
		        useEasing: true,
		        useGrouping: true,
		        separator: ','
		    }
    );

    // Start the animation
    countUp.start((complete) => {
				if (complete) {
					$('#creditSuffix').text(`${data.credits > 1 ? '⚡' : data.credits === 0 ? '😢' : ''}`);
				}
    });
	});



}

initializeSocket();

fetchData = (data) => {
    return new Promise(resolve => {
        socket.once('initial_data', data => {
            resolve(data);
        });
        socket.emit('get_initial_data', data);
    });
};


export { socket, fetchData };
