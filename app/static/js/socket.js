let socket;

function initializeSocket() {
	const options = {
		debug: true,
		path: '/socket.io',
		transports: ['websocket'],
		upgrade: true,
	};

	socket = io(options);
}

initializeSocket();

export { socket };
